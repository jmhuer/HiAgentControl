Stop criteria for plan-only loop:

1) `EvaluatorReport.passed == true`.
2) Retry budget exhausted (`attempt >= max_retries`).
3) Safety stop requested by operator (`loop_state.stop == true`).

Continue criteria:

- Global gate failed and retry budget remains.
- Prometheus can emit at least one actionable, verification-first follow-up task.

