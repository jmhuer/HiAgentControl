#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GROUP_ID="${1:-model_architecture}"
WORKDIR="${2:-$ROOT}"
EVIDENCE_JSON="${HAC_EVIDENCE_JSON:-$ROOT/hiagentresearch/state/evidence/model_architecture.json}"
AGENT_COMMAND="${HAC_AGENT_COMMAND:-}"

export PYTHONPATH="$ROOT"

python -m hiagentresearch.src.orchestrator init
run_args=(
  --group-id "$GROUP_ID"
  --workdir "$WORKDIR"
  --quick
  --evidence-json "$EVIDENCE_JSON"
)
if [[ -n "$AGENT_COMMAND" ]]; then
  run_args+=(--agent-command "$AGENT_COMMAND")
fi
python -m hiagentresearch.src.orchestrator run-group "${run_args[@]}"
