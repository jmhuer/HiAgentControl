from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hiagentcontrol.gates import GlobalEvaluationNode
from hiagentcontrol.loops import from_outcome
from hiagentcontrol.loops.rework_phase import DONE_PROMISE, ReworkPhase, choose_rework_phase
from hiagentcontrol.loops.failure_routing import build_follow_up_work_items
from hiagentcontrol.schemas import GateDefinition, TaskDefinition


ROOT = Path(__file__).resolve().parents[2]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministic plan gate; prints DONE promise on pass."
    )
    parser.add_argument("--workdir", default=str(ROOT / "mnist"))
    parser.add_argument("--num-tasks", type=int, default=4)
    parser.add_argument(
        "--bootstrap-task",
        default=str(ROOT / "hiagentcontrol/bootstrap/plan_bootstrap_task.json"),
    )
    parser.add_argument(
        "--deliverable",
        default="state/current/plan.json",
        help="Relative path to plan.json under workdir",
    )
    return parser.parse_args()


def write_targeted_rework(
    *,
    path: Path,
    report,
    phase: ReworkPhase,
) -> None:
    items = build_follow_up_work_items(report=report)
    lines = [
        "# Targeted Rework",
        "",
        f"rework_phase: {phase.value}",
        "",
        f"Resume at pipeline phase: **{phase.value}** (pi | atlas | format).",
        "",
    ]
    if not items:
        lines.append("No failed checks.")
    for idx, item in enumerate(items, start=1):
        lines.extend(
            [
                f"## {idx}. {item.check_name}",
                f"- target_ref: {item.target_ref}",
                f"- failure_detail: {item.failure_detail}",
                f"- suggested_action: {item.suggested_action}",
                "",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_gate(
    *,
    workdir: Path,
    num_tasks: int,
    deliverable_relative: str = "state/current/plan.json",
    gate: GateDefinition | None = None,
) -> tuple[bool, str]:
    deliverable = workdir / deliverable_relative
    evaluator = GlobalEvaluationNode()
    outcome = evaluator.evaluate(
        workdir=workdir,
        deliverable_path=deliverable,
        gate=gate,
        min_tasks=num_tasks,
        exact_tasks=num_tasks,
    )
    report = from_outcome(outcome)
    phase = choose_rework_phase(report=report)
    # If plan.json is missing but draft exists, formatter can often recover
    # without forcing full PI replanning.
    failed = {c.name for c in report.checks if not c.passed}
    if "plan-json-exists" in failed:
        draft_path = workdir / "state/current/draft.md"
        if draft_path.is_file():
            phase = ReworkPhase.FORMAT

    state_dir = workdir / "state/current"
    state_dir.mkdir(parents=True, exist_ok=True)
    report_path = state_dir / "evaluator_report.json"
    rework_path = state_dir / "targeted_rework.md"

    report_path.write_text(
        json.dumps(
            {
                "passed": report.passed,
                "summary": report.summary,
                "rework_phase": phase.value if not report.passed else None,
                "checks": [c.model_dump() for c in report.checks],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_targeted_rework(path=rework_path, report=report, phase=phase)

    if outcome.passed:
        print(DONE_PROMISE)
        return True, DONE_PROMISE
    return False, report.summary


def main() -> None:
    args = _args()
    workdir = Path(args.workdir).resolve()
    bootstrap = Path(args.bootstrap_task).resolve()
    gate: GateDefinition | None = None
    if bootstrap.is_file():
        task = TaskDefinition.model_validate_json(bootstrap.read_text(encoding="utf-8"))
        gate = task.gate

    passed, _ = run_gate(
        workdir=workdir,
        num_tasks=args.num_tasks,
        deliverable_relative=args.deliverable,
        gate=gate,
    )
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
