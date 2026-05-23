from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from hiagentcontrol.backends import OhMyBackend, default_ohmy_bin
from hiagentcontrol.run_config import RunRequirements
from hiagentcontrol.runners import StructureRunner, StructureRunnerConfig
from hiagentcontrol.tools.run_plan_gate import DONE_PROMISE, run_gate


ROOT = Path(__file__).resolve().parents[2]


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Format existing draft.md into plan.json (structure phase only)."
    )
    parser.add_argument("--workdir", default=str(ROOT / "mnist"))
    parser.add_argument("--num-tasks", type=int, default=5)
    parser.add_argument("--binary", default=default_ohmy_bin())
    parser.add_argument("--base-port", type=int, default=4215)
    parser.add_argument("--timeout-sec", type=int, default=1800)
    parser.add_argument(
        "--agent",
        default="sisyphus",
        help="OMO agent for structure invoke (use strict formatter prompt)",
    )
    return parser.parse_args()


def main() -> None:
    args = _args()
    workdir = Path(args.workdir).resolve()
    draft_path = workdir / "state/current/draft.md"
    plan_path = workdir / "state/current/plan.json"
    requirements = RunRequirements(num_tasks=args.num_tasks)

    if not draft_path.is_file():
        raise SystemExit(f"draft.md missing at {draft_path} — run Atlas phase first or use full loop")

    _log("=" * 60)
    _log("Structure-only: draft.md -> plan.json")
    _log(f"  workdir:   {workdir}")
    _log(f"  num_tasks: {args.num_tasks}")
    _log("=" * 60)

    backend = OhMyBackend(
        root=ROOT,
        binary_path=args.binary,
        base_port=args.base_port,
        timeout_sec=args.timeout_sec,
    )
    runner = StructureRunner(
        backend=backend,
        config=StructureRunnerConfig(
            prompt_template=ROOT / "hiagentcontrol/prompts/structure_output.md",
            plan_example_path=ROOT / "hiagentcontrol/schemas/json/plan_example.json",
            requirements=requirements,
            agent=args.agent,
        ),
    )
    artifact = runner.run(
        workdir=workdir,
        draft_path=draft_path,
        output_path=plan_path,
        rework_path=workdir / "state/current/targeted_rework.md",
        evaluator_report_path=workdir / "state/current/evaluator_report.json",
    )
    _log(f"  structure done  schema_valid={artifact.schema_valid}")

    passed, summary = run_gate(workdir=workdir, num_tasks=args.num_tasks)
    _log(f"  gate: {'PASS' if passed else 'FAIL'}  {summary[:120]}")
    if passed:
        print(DONE_PROMISE)

    print(json.dumps({"passed": passed, "schema_valid": artifact.schema_valid}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
