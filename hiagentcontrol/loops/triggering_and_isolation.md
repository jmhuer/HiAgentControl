Loop triggering and output isolation:

- Trigger owner:
  - OMO `ulw-loop` drives continue/stop.
  - Python loop wrapper only re-enters OMO and persists compact state.

- Output isolation:
  - Subagents write only task-scoped artifacts.
  - Prometheus merges into `state/current/draft.md`.
  - Structured output worker writes only `state/current/plan.json`.

- Failure-to-work-item routing:
  - Global evaluator emits failed checks.
  - Failures map to targeted rework entries with `target_ref`.
  - Prometheus delegates one or more subworker tasks from those entries.

