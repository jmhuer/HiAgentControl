from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from hiagentcontrol.backends import OhMyBackend, default_ohmy_bin
from hiagentcontrol.run_config import RunRequirements
from hiagentcontrol.runners import (
    DraftRunner,
    DraftRunnerConfig,
    OrchestrateRunner,
    OrchestrateRunnerConfig,
    PlanOnlyLoop,
    PlanOnlyLoopConfig,
    StructureRunner,
    StructureRunnerConfig,
)
from hiagentcontrol.runners.phase_errors import DeliverableError
from hiagentcontrol.tools.review_outputs import format_review_report, review_plan_outputs


ROOT = Path(__file__).resolve().parents[2]


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HiAgentControl V2 plan-only execution loop.")
    parser.add_argument("--workdir", default=str(ROOT / "mnist"))
    parser.add_argument(
        "--bootstrap-task",
        default=str(ROOT / "hiagentcontrol/bootstrap/plan_bootstrap_task.json"),
    )
    parser.add_argument("--binary", default=default_ohmy_bin())
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--base-port", type=int, default=4205)
    parser.add_argument("--timeout-sec", type=int, default=3600)
    parser.add_argument("--run-id", default="")
    parser.add_argument(
        "--num-tasks",
        "--no-tasks",
        type=int,
        default=4,
        dest="num_tasks",
        metavar="N",
        help="Minimum tasks in plan.json (plan-task-count gate). Alias: --no-tasks",
    )
    return parser.parse_args()


def main() -> None:
    args = _args()
    workdir = Path(args.workdir).resolve()
    bootstrap = Path(args.bootstrap_task).resolve()
    requirements = RunRequirements(num_tasks=args.num_tasks)

    _log("=" * 60)
    _log("HiAgentControl V2 - Plan Only Loop")
    _log(f"  workdir:     {workdir}")
    _log(f"  bootstrap:   {bootstrap.name}")
    _log(f"  num_tasks:   {requirements.num_tasks}")
    _log(f"  max_retries: {args.max_retries}")
    _log(f"  timeout_sec: {args.timeout_sec}s  (~{args.timeout_sec//60}min)")
    _log("  gates:       plan-json-exists, plan-json-schema, plan-task-count, plan-task-scope")
    _log("  backend:     oh-my-opencode run")
    _log("=" * 60)

    backend = OhMyBackend(
        root=ROOT,
        binary_path=args.binary,
        base_port=args.base_port,
        timeout_sec=args.timeout_sec,
    )
    prompts = ROOT / "hiagentcontrol/prompts"
    loop = PlanOnlyLoop(
        orchestrate_runner=OrchestrateRunner(
            backend=backend,
            config=OrchestrateRunnerConfig(
                prompt_template=prompts / "prometheus_orchestrate.md",
                requirements=requirements,
            ),
        ),
        draft_runner=DraftRunner(
            backend=backend,
            config=DraftRunnerConfig(
                prompt_template=prompts / "execute_draft.md",
                requirements=requirements,
            ),
        ),
        structure_runner=StructureRunner(
            backend=backend,
            config=StructureRunnerConfig(
                prompt_template=prompts / "structure_output.md",
                plan_example_path=ROOT / "hiagentcontrol/schemas/json/plan_example.json",
                requirements=requirements,
            ),
        ),
        config=PlanOnlyLoopConfig(
            max_retries=args.max_retries,
            requirements=requirements,
        ),
    )
    try:
        outcome = loop.run(
            workdir=workdir,
            bootstrap_task_path=bootstrap,
            run_id=args.run_id.strip() or None,
        )
    except DeliverableError as exc:
        _log("=" * 60)
        _log("RESULT: FAILED (deliverable error)")
        _log(f"phase:   {exc.phase}")
        _log(f"detail:  {exc}")
        _log("=" * 60)
        print(json.dumps({"passed": False, "summary": str(exc), "phase": exc.phase}, indent=2))
        raise SystemExit(1) from exc

    review = review_plan_outputs(workdir=workdir, requirements=requirements)
    _log(format_review_report(review, requirements=requirements))

    _log("=" * 60)
    _log(f"RESULT: {'PASSED' if outcome.passed else 'FAILED'}")
    _log(f"deliverable: {outcome.deliverable_path}")
    _log(f"summary:     {outcome.summary}")
    _log("=" * 60)
    print(
        json.dumps(
            {
                "passed": outcome.passed,
                "summary": outcome.summary,
                "plan_task_count": review.plan_task_count,
                "num_tasks_required": requirements.num_tasks,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
