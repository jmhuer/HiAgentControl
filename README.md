# HiAgentControl

Hierarchical agent control: gated planning with oh-my-openagent (OMO) and deterministic Python validation.

## What it does

The **plan-only loop** runs three OMO phases, then gates the deliverable:

1. **Prometheus** — manager plan in `.omo/plans/*.md` (where to look; delegates research)
2. **Atlas** — research draft in `state/current/draft.md`
3. **Sisyphus** — structured `state/current/plan.json` (`PlanDefinition` schema)
4. **Python gates** — schema, task count, scope labels (`TRY` / `FILES` / `CHANGE` / `VERIFY`)

OMO owns agents, delegation, and in-session continuation. Python only invokes `oh-my-opencode run` and validates files on disk.

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

## Run plan-only loop

```bash
PYTHONPATH=. python -m hiagentcontrol.tools.run_plan_only_loop \
  --workdir mnist \
  --num-tasks 3 \
  --max-retries 2 \
  --timeout-sec 1800
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
