from __future__ import annotations

from enum import StrEnum

from .evaluator_report import EvaluatorReport


class ReworkPhase(StrEnum):
    """Which pipeline phase should handle the next loop iteration."""

    PI = "pi"
    ATLAS = "atlas"
    FORMAT = "format"


DONE_PROMISE = "<promise>DONE</promise>"


def choose_rework_phase(*, report: EvaluatorReport) -> ReworkPhase:
    """Map failed gate checks to PI, Atlas (draft), or formatter (plan.json)."""
    if report.passed:
        return ReworkPhase.FORMAT

    failed = {c.name for c in report.checks if not c.passed}

    if "plan-json-exists" in failed:
        return ReworkPhase.PI

    if failed <= {"plan-task-count"}:
        # Count mismatch can usually be fixed by formatter trimming/expanding tasks
        # without forcing PI replanning.
        return ReworkPhase.FORMAT

    if failed <= {"plan-json-schema", "plan-task-scope"} or failed <= {
        "plan-json-schema",
    } or failed <= {"plan-task-scope"}:
        return ReworkPhase.FORMAT

    if "ai-review" in failed:
        return ReworkPhase.ATLAS

    if failed & {"plan-json-schema", "plan-task-scope"}:
        return ReworkPhase.FORMAT

    return ReworkPhase.ATLAS
