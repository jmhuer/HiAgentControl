from __future__ import annotations

from pydantic import BaseModel, Field

from .evaluator_report import EvaluatorReport


class FollowUpWorkItem(BaseModel):
    check_name: str = Field(min_length=1)
    target_ref: str = Field(min_length=1)
    failure_detail: str = Field(min_length=1)
    suggested_action: str = Field(min_length=1)


def build_follow_up_work_items(*, report: EvaluatorReport) -> list[FollowUpWorkItem]:
    work_items: list[FollowUpWorkItem] = []
    for check in report.checks:
        if check.passed:
            continue
        target_ref = check.target_ref or "state/current/plan.json#root"
        suggested_action = _suggest_action(check.name)
        work_items.append(
            FollowUpWorkItem(
                check_name=check.name,
                target_ref=target_ref,
                failure_detail=check.detail,
                suggested_action=suggested_action,
            )
        )
    return work_items


def _suggest_action(check_name: str) -> str:
    if check_name in {"plan-json-schema", "plan-json-exists", "plan-task-scope", "plan-task-count"}:
        return "Run structure retry; fix JSON shape/scope/task count and rerun gate."
    if check_name == "ai-review":
        return "Prometheus replans; executors augment draft.md evidence before structure."
    return "Prometheus delegates executor fix task; re-evaluate after draft/plan updated."

