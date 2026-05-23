from __future__ import annotations

from collections.abc import Callable

from .base import EvaluationOutcome


def run_until_pass(
    *,
    max_retries: int,
    produce_attempt: Callable[[int], None],
    evaluate_attempt: Callable[[int], EvaluationOutcome],
    on_failure: Callable[[int, EvaluationOutcome], None],
) -> EvaluationOutcome:
    """
    Reusable produce -> evaluate -> retry loop.

    Keeps logic generic for plan-only and future hierarchical task instances.
    """

    attempts = max(1, max_retries + 1)
    last_outcome: EvaluationOutcome | None = None
    for attempt in range(attempts):
        produce_attempt(attempt)
        outcome = evaluate_attempt(attempt)
        last_outcome = outcome
        if outcome.passed:
            return outcome
        on_failure(attempt, outcome)
    if last_outcome is None:
        raise RuntimeError("Gate loop ran zero attempts.")
    return last_outcome

