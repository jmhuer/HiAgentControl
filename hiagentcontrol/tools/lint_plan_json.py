from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hiagentcontrol.gates.plan_lint import lint_plan_json
from hiagentcontrol.schemas import GateDefinition, TaskDefinition


ROOT = Path(__file__).resolve().parents[2]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint plan.json against PlanDefinition (pre-gate). "
            "Use during structure to fix issues before run_plan_gate."
        )
    )
    parser.add_argument("--workdir", default=str(ROOT / "mnist"))
    parser.add_argument("--num-tasks", type=int, default=5)
    parser.add_argument(
        "--bootstrap-task",
        default=str(ROOT / "hiagentcontrol/bootstrap/plan_bootstrap_task.json"),
    )
    parser.add_argument(
        "--deliverable",
        default="state/current/plan.json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of agent text",
    )
    return parser.parse_args()


def main() -> None:
    args = _args()
    workdir = Path(args.workdir).resolve()
    gate: GateDefinition | None = None
    bootstrap = Path(args.bootstrap_task).resolve()
    if bootstrap.is_file():
        task = TaskDefinition.model_validate_json(bootstrap.read_text(encoding="utf-8"))
        gate = task.gate

    result = lint_plan_json(
        workdir=workdir,
        num_tasks=args.num_tasks,
        deliverable_relative=args.deliverable,
        gate=gate,
    )
    if args.json:
        print(json.dumps(result.to_json_dict(), indent=2))
    else:
        print(result.to_agent_text())
    raise SystemExit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
