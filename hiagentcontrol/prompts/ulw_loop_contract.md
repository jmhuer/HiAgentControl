ULW loop ownership contract (plan-only phase):

1) OMO `ulw-loop` is the primary loop owner.
2) Continue/stop decisions come from project criteria in persisted state and evaluator report.
3) Python runtime is a watchdog and persistence bridge, not a semantic decider.
4) On interruption, Python re-invokes OMO with explicit re-entry context.
5) Re-entry artifacts:
   - `.omo/plans/` — Prometheus execution plan (what to research)
   - `state/current/draft.md` — executor research output
   - `state/current/evaluator_report.json`
   - `state/current/loop_state.json`
   - `state/current/targeted_rework.md`
6) **Prometheus** plans and delegates; **executors** write `draft.md`; **structure** writes `plan.json`.
