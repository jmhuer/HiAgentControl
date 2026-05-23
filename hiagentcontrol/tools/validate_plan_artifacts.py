from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hiagentcontrol.gates.deterministic_checks import sanitize_plan_json_text
from hiagentcontrol.schemas import PlanDefinition
from hiagentcontrol.tools.run_plan_gate import run_gate


ROOT = Path(__file__).resolve().parents[2]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate plan loop artifacts after E2E.")
    parser.add_argument("--workdir", default=str(ROOT / "mnist"))
    parser.add_argument("--num-tasks", type=int, required=True)
    return parser.parse_args()


def validate(*, workdir: Path, num_tasks: int) -> list[str]:
    errors: list[str] = []
    plans = list((workdir / ".omo/plans").glob("*.md")) if (workdir / ".omo/plans").is_dir() else []
    if not plans:
        errors.append("missing .omo/plans/*.md")

    draft = workdir / "state/current/draft.md"
    if not draft.is_file() or draft.stat().st_size < 50:
        errors.append("draft.md missing or too small")

    plan_path = workdir / "state/current/plan.json"
    if not plan_path.is_file():
        errors.append("plan.json missing")
    else:
        try:
            plan = PlanDefinition.model_validate_json(
                sanitize_plan_json_text(plan_path.read_text(encoding="utf-8"))
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"plan.json invalid: {exc}")
        else:
            if len(plan.tasks) != num_tasks:
                errors.append(
                    f"expected exactly {num_tasks} tasks, got {len(plan.tasks)}"
                )
            for idx, t in enumerate(plan.tasks):
                if not t.task.strip():
                    errors.append(f"tasks[{idx}].task empty")
                if not t.scope.strip():
                    errors.append(f"tasks[{idx}].scope empty")
                if not str(t.goal_type):
                    errors.append(f"tasks[{idx}].goal_type missing")

    passed, _ = run_gate(workdir=workdir, num_tasks=num_tasks)
    if not passed:
        errors.append("run_plan_gate did not pass")

    return errors


def main() -> None:
    args = _args()
    workdir = Path(args.workdir).resolve()
    errors = validate(workdir=workdir, num_tasks=args.num_tasks)
    result = {"passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
