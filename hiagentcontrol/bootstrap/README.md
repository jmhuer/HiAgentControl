# Bootstrap Task

`plan_bootstrap_task.json` is the manual seed task for the plan-only workflow.

It uses the same generic `TaskDefinition` schema as downstream tasks.

## Canonical OMO phases

| Phase | Agent role | Output |
|-------|------------|--------|
| **Plan** | Prometheus | `.omo/plans/*.md` (what to research) + delegate |
| **Execute** | Workers via `task()` / `call_omo_agent` | `state/current/draft.md` |
| **Structure** | Structure worker | `state/current/plan.json` |

Prometheus does **not** write `draft.md`. Executors do.
