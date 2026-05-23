from __future__ import annotations

from pydantic import BaseModel, Field

from hiagentcontrol.gates import EvaluationOutcome


class ReportCheck(BaseModel):
    name: str
    passed: bool
    detail: str
    target_ref: str | None = None


class EvaluatorReport(BaseModel):
    passed: bool
    summary: str
    checks: list[ReportCheck] = Field(default_factory=list)
    follow_up_work_items: list[str] = Field(default_factory=list)


def from_outcome(outcome: EvaluationOutcome) -> EvaluatorReport:
    checks = [
        ReportCheck(
            name=item.name,
            passed=item.passed,
            detail=item.detail,
            target_ref=item.target_ref,
        )
        for item in outcome.checks
    ]
    return EvaluatorReport(
        passed=outcome.passed,
        summary=outcome.summary,
        checks=checks,
        follow_up_work_items=list(outcome.follow_up_work_items),
    )

