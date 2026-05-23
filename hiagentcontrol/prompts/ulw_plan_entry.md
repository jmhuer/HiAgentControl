Use skill **hac-plan-pipeline** as the loop owner.

Produce exactly `{num_tasks}` tasks in `state/current/plan.json`.
Execute phases in strict order: PI -> Atlas -> Formatter -> Gate.

Gate command:
`PYTHONPATH={repo_root} python -m hiagentcontrol.tools.run_plan_gate --workdir . --num-tasks {num_tasks}`

Loop rule:
- If gate prints `<promise>DONE</promise>`, output only that tag and stop.
- Otherwise read `state/current/targeted_rework.md` and continue at `rework_phase`.

Execution constraints:
- Do NOT call `task_create` as a placeholder and stop.
- Do NOT end with "All tasks completed" unless `run_plan_gate` just printed `<promise>DONE</promise>`.
- You must actually create artifacts: `.omo/plans/*.md`, `state/current/draft.md`, `state/current/plan.json`.

---

{bootstrap_block}

{rework_block}
