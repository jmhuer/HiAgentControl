from __future__ import annotations

from enum import StrEnum

from .evaluator_report import EvaluatorReport
from .loop_state import LoopState


class NextAction(StrEnum):
    STOP = "stop"
    STRUCTURE_RETRY = "structure_retry"
    REPLAN_AUGMENT = "replan_augment"


def choose_next_action(*, state: LoopState, report: EvaluatorReport) -> NextAction:
    if report.passed:
        return NextAction.STOP
    if state.attempt >= state.max_retries:
        return NextAction.STOP

    failed_names = {item.name for item in report.checks if not item.passed}

    # Missing deliverable or draft — full pipeline retry, not structure-only.
    if "plan-json-exists" in failed_names:
        return NextAction.REPLAN_AUGMENT

    if failed_names.issubset(
        {"plan-json-schema", "plan-task-count", "plan-task-scope", "ai-review"}
    ):
        return NextAction.STRUCTURE_RETRY

    return NextAction.REPLAN_AUGMENT
