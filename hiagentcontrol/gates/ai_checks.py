from __future__ import annotations

from pathlib import Path

from hiagentcontrol.schemas import AiEvalCheck

from .base import CheckResult


def run_ai_review(
    *,
    ai_eval: AiEvalCheck,
    deliverable_path: Path,
) -> CheckResult:
    """
    Placeholder AI-review contract.

    This module returns a pass when AI review is disabled. When enabled,
    it records the requirement for external AI scoring. The integration point
    stays explicit so deterministic + AI checks can remain a single global node.
    """

    if not ai_eval.enabled:
        return CheckResult(
            name="ai-review",
            passed=True,
            detail="AI review disabled for this gate.",
            target_ref=str(deliverable_path),
        )

    if not ai_eval.rubric:
        return CheckResult(
            name="ai-review",
            passed=False,
            detail="AI review enabled but rubric is empty.",
            target_ref=str(deliverable_path),
        )

    return CheckResult(
        name="ai-review",
        passed=True,
        detail="AI review rubric present; external reviewer may execute this check.",
        target_ref=str(deliverable_path),
    )

