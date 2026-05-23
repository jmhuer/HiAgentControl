#!/usr/bin/env bash
# HiAgentControl — clean artifacts and rerun the OMO plan loop.
#
# Usage:
#   ./scripts/rerun_plan_loop.sh                    # full fresh run (5 tasks)
#   ./scripts/rerun_plan_loop.sh --num-tasks 3
#   ./scripts/rerun_plan_loop.sh --structure-only   # keep draft.md, reformat plan.json
#   ./scripts/rerun_plan_loop.sh --no-clean         # continue with existing artifacts
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKDIR="${HAC_WORKDIR:-$ROOT/mnist}"
NUM_TASKS="${HAC_NUM_TASKS:-5}"
TIMEOUT_SEC="${HAC_TIMEOUT_SEC:-3600}"
MODE="full"
CLEAN=1

# Default OMO binary (override with HAC_OHMY_BIN)
if [[ -z "${HAC_OHMY_BIN:-}" ]]; then
  if command -v oh-my-openagent >/dev/null 2>&1; then
    export HAC_OHMY_BIN="$(command -v oh-my-openagent)"
  elif [[ -x /tmp/bunx-1000-oh-my-openagent@latest/node_modules/.bin/oh-my-opencode ]]; then
    export HAC_OHMY_BIN="/tmp/bunx-1000-oh-my-openagent@latest/node_modules/.bin/oh-my-opencode"
  fi
fi

usage() {
  sed -n '2,8p' "$0" | sed 's/^# \?//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --num-tasks) NUM_TASKS="$2"; shift 2 ;;
    --workdir) WORKDIR="$2"; shift 2 ;;
    --timeout-sec) TIMEOUT_SEC="$2"; shift 2 ;;
    --structure-only) MODE="structure"; shift ;;
    --no-clean) CLEAN=0; shift ;;
    --full) MODE="full"; CLEAN=1; shift ;;
    *) echo "Unknown option: $1" >&2; usage 1 ;;
  esac
done

export PYTHONPATH="$ROOT"
export HAC_OHMY_BIN="${HAC_OHMY_BIN:-}"

echo "== HiAgentControl rerun =="
echo "  ROOT:       $ROOT"
echo "  WORKDIR:    $WORKDIR"
echo "  NUM_TASKS:  $NUM_TASKS"
echo "  MODE:       $MODE"
echo "  HAC_OHMY_BIN: ${HAC_OHMY_BIN:-<auto>}"

# Kill stale OMO / opencode serve (best-effort)
pkill -f 'oh-my-opencode run.*'"$(basename "$WORKDIR")" 2>/dev/null || true
pkill -f 'oh-my-openagent run.*'"$(basename "$WORKDIR")" 2>/dev/null || true
for port in 4205 4215 4220 4225 4230 4235; do
  pid=$(lsof -ti tcp:"$port" 2>/dev/null || true)
  if [[ -n "$pid" ]]; then kill $pid 2>/dev/null || true; fi
done
sleep 1

if [[ "$CLEAN" -eq 1 ]]; then
  if [[ "$MODE" == "structure" ]]; then
    PYTHONPATH="$ROOT" python -m hiagentcontrol.tools.clean_run_state \
      --workdir "$WORKDIR" --mode structure
  else
    PYTHONPATH="$ROOT" python -m hiagentcontrol.tools.clean_run_state \
      --workdir "$WORKDIR" --mode fresh
  fi
else
  echo "  (skipping cleanup — --no-clean)"
fi

if [[ "$MODE" == "structure" ]]; then
  echo "== Structure-only: draft.md -> plan.json =="
  PYTHONPATH="$ROOT" python -m hiagentcontrol.tools.run_structure_only \
    --workdir "$WORKDIR" \
    --num-tasks "$NUM_TASKS" \
    --timeout-sec "$TIMEOUT_SEC"
else
  echo "== Full OMO plan loop =="
  PYTHONPATH="$ROOT" python -m hiagentcontrol.tools.run_omo_plan_loop \
    --workdir "$WORKDIR" \
    --num-tasks "$NUM_TASKS" \
    --timeout-sec "$TIMEOUT_SEC" \
    --stall-check-sec 120 \
    --no-clean
fi

echo "== Post-run validation =="
PYTHONPATH="$ROOT" python -m hiagentcontrol.tools.validate_plan_artifacts \
  --workdir "$WORKDIR" --num-tasks "$NUM_TASKS"
