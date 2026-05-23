from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

from hiagentcontrol.gates import EvaluationOutcome, GlobalEvaluationNode, run_until_pass
from hiagentcontrol.loops import (
    EvaluatorReport,
    LoopState,
    NextAction,
    build_follow_up_work_items,
    choose_next_action,
    from_outcome,
)
from hiagentcontrol.run_config import RunRequirements
from hiagentcontrol.runners.draft_runner import DraftRunner
from hiagentcontrol.runners.phase_errors import DeliverableError
from hiagentcontrol.runners.orchestrate_runner import OrchestrateRunner
from hiagentcontrol.runners.structure_runner import StructureRunner
from hiagentcontrol.schemas import TaskDefinition


@dataclass(frozen=True)
class PlanOnlyLoopConfig:
    max_retries: int = 2
    requirements: RunRequirements = RunRequirements()
    draft_relative_path: str = "state/current/draft.md"
    deliverable_relative_path: str = "state/current/plan.json"
    evaluator_report_relative_path: str = "state/current/evaluator_report.json"
    loop_state_relative_path: str = "state/current/loop_state.json"
    targeted_rework_relative_path: str = "state/current/targeted_rework.md"


class PlanOnlyLoop:
    """
    Orchestrate → Draft (if needed) → Structure → Gate

    - Prometheus session: `.omo/plans/*.md` (+ draft when feasible)
    - Draft fill: second thin invoke if draft is skeleton-only
    - Structure: schema-valid `state/current/plan.json`
    """

    def __init__(
        self,
        *,
        orchestrate_runner: OrchestrateRunner,
        draft_runner: DraftRunner,
        structure_runner: StructureRunner,
        evaluator: GlobalEvaluationNode | None = None,
        config: PlanOnlyLoopConfig | None = None,
    ) -> None:
        self.orchestrate_runner = orchestrate_runner
        self.draft_runner = draft_runner
        self.structure_runner = structure_runner
        self.evaluator = evaluator or GlobalEvaluationNode()
        self.config = config or PlanOnlyLoopConfig()

    def run(
        self,
        *,
        workdir: Path,
        bootstrap_task_path: Path,
        run_id: str | None = None,
    ) -> EvaluationOutcome:
        task = TaskDefinition.model_validate_json(bootstrap_task_path.read_text(encoding="utf-8"))
        run_token = run_id or uuid4().hex[:8]

        req = self.config.requirements
        _log(
            f"=== PlanOnlyLoop start  run_id={run_token}  max_retries={self.config.max_retries} "
            f"num_tasks={req.num_tasks} ==="
        )
        _log(f"  workdir:    {workdir}")
        _log(f"  bootstrap:  {bootstrap_task_path.name}")
        _log(f"  task:       {task.task[:100]}")
        _log(f"  num_tasks:  {req.num_tasks} (gate: plan-json-schema + plan-task-count)")

        draft_path = workdir / self.config.draft_relative_path
        deliverable_path = workdir / self.config.deliverable_relative_path
        evaluator_report_path = workdir / self.config.evaluator_report_relative_path
        loop_state_path = workdir / self.config.loop_state_relative_path
        targeted_rework_path = workdir / self.config.targeted_rework_relative_path
        for parent in {
            draft_path.parent,
            deliverable_path.parent,
            evaluator_report_path.parent,
            loop_state_path.parent,
            targeted_rework_path.parent,
        }:
            parent.mkdir(parents=True, exist_ok=True)

        state = LoopState(run_id=run_token, max_retries=self.config.max_retries)
        next_action = NextAction.REPLAN_AUGMENT

        def produce_attempt(attempt: int) -> None:
            nonlocal next_action
            t0 = time.monotonic()
            _log(f"--- Attempt {attempt}: produce ---")

            if next_action == NextAction.STOP:
                _log("  produce skipped (loop stop)")
                return

            run_orchestrate = next_action == NextAction.REPLAN_AUGMENT
            rework = targeted_rework_path if targeted_rework_path.exists() else None
            eval_report = evaluator_report_path if evaluator_report_path.exists() else None

            if run_orchestrate:
                _log("  [1/3] PLAN  Prometheus → .omo/plans/*.md")
                artifact = self.orchestrate_runner.run(
                    workdir=workdir,
                    bootstrap_task=task,
                    loop_attempt=attempt,
                    rework_path=rework,
                    evaluator_report_path=eval_report,
                )
                _log(f"  [1/3] PLAN  done  plan_files={len(artifact.plan_paths)}")
            else:
                _log(f"  [1/3] PLAN  skipped ({next_action.value})")

            run_draft = (
                run_orchestrate
                or (next_action == NextAction.REPLAN_AUGMENT and not draft_path.is_file())
            )
            if run_draft:
                _log("  [2/3] DRAFT  fill research draft from plan")
                self.draft_runner.run(
                    workdir=workdir,
                    loop_attempt=attempt,
                    rework_path=rework,
                    evaluator_report_path=eval_report,
                )
                _log("  [2/3] DRAFT  done")
            else:
                _log("  [2/3] DRAFT  skipped (draft exists)")

            if draft_path.is_file():
                _log("  [3/3] STRUCTURE  draft.md → plan.json")
                struct_artifact = self.structure_runner.run(
                    workdir=workdir,
                    draft_path=draft_path,
                    output_path=deliverable_path,
                    rework_path=rework,
                    evaluator_report_path=eval_report,
                    loop_attempt=attempt,
                )
                _log(
                    f"  [3/3] STRUCTURE  done  rc={struct_artifact.result.returncode}  "
                    f"schema_valid={struct_artifact.schema_valid}"
                )
            else:
                _log("  [3/3] STRUCTURE  skipped (draft missing)")
            _log(f"  produce_attempt elapsed {time.monotonic() - t0:.1f}s")

        def evaluate_attempt(attempt: int) -> EvaluationOutcome:
            _log(f"--- Attempt {attempt}: evaluate ---")
            outcome = self.evaluator.evaluate(
                workdir=workdir,
                deliverable_path=deliverable_path,
                gate=task.gate,
                min_tasks=req.num_tasks,
            )
            status = "PASS" if outcome.passed else "FAIL"
            _log(f"  gate={status}  checks={len(outcome.checks)}")
            for check in outcome.checks:
                icon = "✓" if check.passed else "✗"
                _log(f"    {icon} {check.name}: {check.detail[:120]}")
            return outcome

        def on_failure(attempt: int, outcome: EvaluationOutcome) -> None:
            nonlocal next_action, state
            _log(f"--- Attempt {attempt}: on_failure ---")
            report = from_outcome(outcome)
            _write_json(evaluator_report_path, report.model_dump())

            state = LoopState(
                run_id=state.run_id,
                attempt=attempt + 1,
                max_retries=state.max_retries,
                stop=False,
                last_decision=state.last_decision,
            )
            next_action = choose_next_action(state=state, report=report)
            state = LoopState(
                run_id=state.run_id,
                attempt=state.attempt,
                max_retries=state.max_retries,
                stop=next_action == NextAction.STOP,
                last_decision=next_action.value,
            )
            _write_json(loop_state_path, state.model_dump())
            _write_targeted_rework(path=targeted_rework_path, report=report)

        _log("--- starting gate loop (orchestrate → draft → structure) ---")
        t_start = time.monotonic()
        outcome = run_until_pass(
            max_retries=self.config.max_retries,
            produce_attempt=produce_attempt,
            evaluate_attempt=evaluate_attempt,
            on_failure=on_failure,
        )
        elapsed = time.monotonic() - t_start
        status = "PASSED" if outcome.passed else "FAILED (retries exhausted)"
        _log(f"=== PlanOnlyLoop done  {status}  elapsed={elapsed:.1f}s ===")
        _log(f"  deliverable: {outcome.deliverable_path}")
        return outcome


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_targeted_rework(*, path: Path, report: EvaluatorReport) -> None:
    if not report.follow_up_work_items:
        path.write_text("# Targeted Rework\n\nNo failed checks.\n", encoding="utf-8")
        return
    follow_up_items = build_follow_up_work_items(report=report)
    lines = ["# Targeted Rework", ""]
    for idx, item in enumerate(follow_up_items, start=1):
        lines.extend(
            [
                f"## {idx}. {item.check_name}",
                f"- target_ref: {item.target_ref}",
                f"- failure_detail: {item.failure_detail}",
                f"- suggested_action: {item.suggested_action}",
                "",
            ]
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
