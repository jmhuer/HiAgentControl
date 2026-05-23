from __future__ import annotations

from pathlib import Path

from hiagentcontrol.schemas import GateDefinition

from .ai_checks import run_ai_review
from .base import CheckResult, EvaluationOutcome
from .deterministic_checks import (
    run_script_check,
    validate_plan_json,
    validate_plan_task_count,
    validate_plan_task_scopes,
)


class GlobalEvaluationNode:
    """Single gate node that merges deterministic checks with optional AI review."""

    def evaluate(
        self,
        *,
        workdir: Path,
        deliverable_path: Path,
        gate: GateDefinition | None,
        min_tasks: int = 1,
    ) -> EvaluationOutcome:
        checks: list[CheckResult] = list(validate_plan_json(plan_json_path=deliverable_path))
        checks.append(
            validate_plan_task_count(plan_json_path=deliverable_path, min_tasks=min_tasks)
        )
        checks.append(validate_plan_task_scopes(plan_json_path=deliverable_path))
        if gate:
            for script_check in gate.script_checks:
                checks.append(run_script_check(workdir=workdir, check=script_check))
            if gate.ai_eval:
                checks.append(
                    run_ai_review(
                        ai_eval=gate.ai_eval,
                        deliverable_path=deliverable_path,
                    )
                )
        passed = all(item.passed for item in checks)
        summary = "All global gate checks passed." if passed else "Global gate checks failed."
        follow_up_work_items = tuple(
            f"{item.name}: {item.detail}" for item in checks if not item.passed
        )
        return EvaluationOutcome(
            passed=passed,
            summary=summary,
            checks=tuple(checks),
            deliverable_path=deliverable_path,
            follow_up_work_items=follow_up_work_items,
        )
