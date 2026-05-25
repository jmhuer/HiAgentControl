# hiagentresearch (Phase 1)

This directory contains the first implementation of the branch-based research runtime.

## Phase 1 goals

- Set up GitHub automation for MNIST research branches.
- Define research groups and agent skeleton contracts.
- Run one research-group cycle with strong observability outputs.
- Keep orchestration thin and deterministic.

## Scope boundaries

- Merge orchestration is phase 2.
- Plugin packaging is phase 3.
- The Python control plane is intentionally thin:
  - state transitions,
  - registry writes,
  - eval lifecycle integration,
  - intent packet persistence.

## Layout

- `src/` runtime modules and CLIs
- `state/` research-group definitions and persisted run artifacts
- `docs/` design contracts
- `workflows/` reusable workflow templates

## Quick start (local)

```bash
PYTHONPATH=. python -m hiagentresearch.src.orchestrator init
PYTHONPATH=. python -m hiagentresearch.src.orchestrator run-group --group-id model_architecture --workdir mnist --quick
```

Optional: run one real agent command before evaluation and capture full stdout/stderr:

```bash
PYTHONPATH=. python -m hiagentresearch.src.orchestrator run-group \
  --group-id model_architecture \
  --workdir . \
  --agent-command "echo phase1-agent-step"
```

The run command writes visibility artifacts under:

- `hiagentresearch/state/runs/<run_id>/`
- `hiagentresearch/state/intent_packets/<group_id>.json`
- `hiagentresearch/state/events.jsonl`
