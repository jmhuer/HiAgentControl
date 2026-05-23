# HiAgentControl

Hierarchical agent control: gated planning with oh-my-openagent (OMO) and deterministic Python validation.

## What it does

The **plan loop** uses one OMO session (`/ulw-loop` + project skills) with four phases:

1. **Prometheus (PI)** — `.omo/plans/*.md`
2. **Atlas (postdoc)** — `state/current/draft.md`
3. **Sisyphus-Junior (formatter)** — `state/current/plan.json` via skill `hac-format-plan-json`
4. **Python gate** — `run_plan_gate.py` prints `<promise>DONE</promise>` when valid

Python invokes `oh-my-openagent run` once and validates artifacts on disk. Legacy three-subprocess mode: `--legacy-three-phase`.

## Repository layout

| Path | Purpose |
|------|---------|
| [`hiagentcontrol/`](hiagentcontrol/) | Package: runners, gates, prompts, schemas |
| [`mnist/`](mnist/) | Example workspace (pipeline, eval, OpenCode config) |
| [`tests/`](tests/) | Gate and schema tests |
| [`ohmycode_best_practices.md`](ohmycode_best_practices.md) | OMO integration reference |

## Prerequisites

- Python 3.10+
- [`oh-my-opencode`](https://github.com/code-yeongyu/oh-my-openagent) (`HAC_OHMY_BIN` or default bunx path)
- OpenRouter (or configured provider) API access

## Setup

```bash
cd ~/github/HiAgentControl
pip install -r requirements.txt
pip install -r mnist/requirements.txt

# OMO agent config (per machine)
cp mnist/.opencode/oh-my-openagent.jsonc.example mnist/.opencode/oh-my-openagent.jsonc
# edit models if needed

# API keys (not committed)
cp credentials/apikey.txt.example credentials/apikey.txt
# fill credentials/apikey.txt — see credentials/README.md
```

## Run plan loop (default: single OMO session)

**Quick retry** (cleans stale artifacts, sets env, runs loop):

```bash
chmod +x scripts/rerun_plan_loop.sh
./scripts/rerun_plan_loop.sh --num-tasks 5
```

Structure-only when `draft.md` is already good (keeps draft, clears `plan.json`):

```bash
./scripts/rerun_plan_loop.sh --structure-only --num-tasks 5
```

Manual:

```bash
PYTHONPATH=. python -m hiagentcontrol.tools.run_omo_plan_loop \
  --workdir mnist \
  --num-tasks 5 \
  --timeout-sec 3600
```

By default each run **removes** prior `draft.md`, `plan.json`, gate reports, `.omo/plans/`, and OMO logs so agents do not inherit a partial prior loop. Use `--no-clean` to continue with existing artifacts.

Legacy PLAN → DRAFT → STRUCTURE subprocesses:

```bash
PYTHONPATH=. python -m hiagentcontrol.tools.run_plan_only_loop \
  --workdir mnist --num-tasks 5 --legacy-three-phase
```

Gate only:

```bash
PYTHONPATH=. python -m hiagentcontrol.tools.run_plan_gate --workdir mnist --num-tasks 5
```

Pre-gate lint (for structure agents — same rules, no `<promise>DONE</promise>`):

```bash
PYTHONPATH=. python -m hiagentcontrol.tools.lint_plan_json --workdir mnist --num-tasks 5
```

Outputs (local, gitignored): `mnist/.omo/plans/`, `mnist/state/current/draft.md`, `mnist/state/current/plan.json`.

## Tests

```bash
PYTHONPATH=. pytest tests/ -q
```

## What is tracked in git

**Tracked:** `hiagentcontrol/`, `mnist/pipeline/`, `mnist/eval/`, `mnist/baseline.json`, `mnist/README.md`, `mnist/.opencode/opencode.json`, `*.example` configs, `ohmycode_best_practices.md`.

**Not tracked:** `mnist/data/` (MNIST downloads), `mnist/state/`, `mnist/.omo/`, `credentials/*` secrets, checkpoints, `last_train_metrics.json`, live `oh-my-openagent.jsonc`, `__pycache__/`.

## MNIST train / eval

See [`mnist/README.md`](mnist/README.md) for `pipeline/train.py` and `eval/run_eval.py`.
