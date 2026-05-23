# HiAgentControl MNIST — architecture invariants

## Pipeline (single `/ulw-loop` session)

1. **PI (Prometheus)** — `.omo/plans/*.md` only; no subagents during planning.
2. **Postdoc (Atlas)** — `state/current/draft.md`; delegates explore/librarian/junior.
3. **Formatter (Sisyphus-Junior)** — `state/current/plan.json` via skill `hac-format-plan-json` only.
4. **Review committee (Python)** — `python -m hiagentcontrol.tools.run_plan_gate`; no LLM evaluator.

## Task shape in plan.json

- **task** — research area title (what domain to explore).
- **scope** — what to try / where to look before ending (TRY:/FILES:/CHANGE:/VERIFY:).
- **goal_type** — drives worker choice: survey, codebase_recon, experiment, architecture, hygiene, feature, ablation_study.

## Must not

- Atlas must not write `plan.json`.
- Prometheus must not spawn `task()` during PLAN phase.
- Formatter must not change research substance or fix gate failures.
- No phantom paths (e.g. `mnist_cnn.py`); model code is `pipeline/model.py`.

## Rework

On gate failure, read `state/current/targeted_rework.md` → `rework_phase`: pi | atlas | format.
