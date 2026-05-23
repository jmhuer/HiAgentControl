from __future__ import annotations

import argparse
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from hiagentcontrol.backends import OhMyBackend, default_ohmy_bin
from hiagentcontrol.run_config import RunRequirements
from hiagentcontrol.runners.orchestrate_runner import OrchestrateRunner, OrchestrateRunnerConfig
from hiagentcontrol.schemas import TaskDefinition
from hiagentcontrol.tools.clean_run_state import clean_for_fresh_run, clean_for_structure_retry
from hiagentcontrol.tools.run_plan_gate import run_gate
from hiagentcontrol.tools.validate_plan_artifacts import validate


ROOT = Path(__file__).resolve().parents[2]


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Single-session OMO plan loop (ulw-loop + hac-plan-pipeline skill)."
    )
    parser.add_argument("--workdir", default=str(ROOT / "mnist"))
    parser.add_argument(
        "--bootstrap-task",
        default=str(ROOT / "hiagentcontrol/bootstrap/plan_bootstrap_task.json"),
    )
    parser.add_argument("--binary", default=default_ohmy_bin())
    parser.add_argument("--base-port", type=int, default=4205)
    parser.add_argument("--timeout-sec", type=int, default=3600)
    parser.add_argument("--num-tasks", type=int, default=5)
    parser.add_argument(
        "--agent",
        default="atlas",
        help="Primary session agent for /ulw-loop coordination",
    )
    parser.add_argument(
        "--stall-check-sec",
        type=int,
        default=240,
        help="Log stuck warning if artifacts unchanged for this many seconds",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip post-run validate_plan_artifacts (not recommended)",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not remove prior draft/plan/gate artifacts (continue/rework mode)",
    )
    parser.add_argument(
        "--clean-mode",
        choices=("fresh", "structure"),
        default="fresh",
        help="fresh=remove draft+plans+plan; structure=keep draft, clear plan.json only",
    )
    return parser.parse_args()


def build_ulw_prompt(
    *,
    num_tasks: int,
    bootstrap_task: TaskDefinition,
    rework_path: Path | None,
    repo_root: Path,
) -> str:
    template = (ROOT / "hiagentcontrol/prompts/ulw_plan_entry.md").read_text(encoding="utf-8")
    bootstrap_block = (
        f"## Bootstrap task\n\n"
        f"- task: {bootstrap_task.task}\n"
        f"- goal_type: {bootstrap_task.goal_type}\n"
        f"- scope: {bootstrap_task.scope}\n"
    )
    rework_block = ""
    if rework_path and rework_path.is_file():
        rework_block = f"## Prior rework\n\n{rework_path.read_text(encoding='utf-8')}"
    return template.format(
        num_tasks=num_tasks,
        repo_root=repo_root,
        bootstrap_block=bootstrap_block,
        rework_block=rework_block,
    )


def _artifact_mtimes(workdir: Path) -> dict[str, float]:
    paths = [
        workdir / "state/current/draft.md",
        workdir / "state/current/plan.json",
    ]
    plans = list((workdir / ".omo/plans").glob("*.md")) if (workdir / ".omo/plans").is_dir() else []
    paths.extend(plans)
    mtimes: dict[str, float] = {}
    for p in paths:
        if p.is_file():
            mtimes[str(p.relative_to(workdir))] = p.stat().st_mtime
    return mtimes


def _stall_monitor(
    *,
    workdir: Path,
    interval_sec: int,
    stop_event: threading.Event,
) -> None:
    last = _artifact_mtimes(workdir)
    last_change = time.monotonic()
    while not stop_event.wait(interval_sec):
        current = _artifact_mtimes(workdir)
        if current != last:
            last = current
            last_change = time.monotonic()
            continue
        idle = time.monotonic() - last_change
        if idle >= interval_sec:
            _log(
                f"[STUCK?] No artifact changes for {int(idle)}s — "
                "check pgrep oh-my-openagent; tail /tmp/oh-my-opencode.log"
            )


def _ensure_plan_artifact(
    *,
    backend: OhMyBackend,
    workdir: Path,
    bootstrap_task: TaskDefinition,
    num_tasks: int,
) -> None:
    if list((workdir / ".omo/plans").glob("*.md")):
        return
    _log("  no .omo/plans/*.md found after session; running Prometheus plan recovery")
    runner = OrchestrateRunner(
        backend=backend,
        config=OrchestrateRunnerConfig(
            prompt_template=ROOT / "hiagentcontrol/prompts/prometheus_orchestrate.md",
            requirements=RunRequirements(num_tasks=num_tasks),
            agent="prometheus",
        ),
    )
    runner.run(
        workdir=workdir,
        bootstrap_task=bootstrap_task,
        loop_attempt=0,
    )


def main() -> None:
    args = _args()
    workdir = Path(args.workdir).resolve()
    bootstrap = Path(args.bootstrap_task).resolve()
    task = TaskDefinition.model_validate_json(bootstrap.read_text(encoding="utf-8"))
    requirements = RunRequirements(num_tasks=args.num_tasks)

    if not args.no_clean:
        if args.clean_mode == "structure":
            removed = clean_for_structure_retry(workdir)
        else:
            removed = clean_for_fresh_run(workdir)
        _log(f"  cleaned {len(removed)} artifact(s) before run")
    else:
        _log("  --no-clean: prior draft/plan/rework left in place")

    # Stale rework from a prior partial run confuses the loop
    rework = workdir / "state/current/targeted_rework.md"
    if rework.is_file() and args.no_clean:
        pass
    elif rework.is_file() and not args.no_clean:
        pass  # already removed by clean_for_fresh_run

    # Pre-create files Atlas/formatter expect under strict edit/append policies.
    state_dir = workdir / "state/current"
    state_dir.mkdir(parents=True, exist_ok=True)
    draft_path = state_dir / "draft.md"
    if not draft_path.exists():
        draft_path.write_text("# Draft\n\n", encoding="utf-8")

    notepad_dir = workdir / ".omo/notepads/plan"
    notepad_dir.mkdir(parents=True, exist_ok=True)
    for name in ("learnings.md", "decisions.md", "issues.md", "verification.md", "problems.md"):
        f = notepad_dir / name
        if not f.exists():
            f.write_text(f"# {name[:-3].title()}\n\n", encoding="utf-8")

    _log("=" * 60)
    _log("HiAgentControl — OMO single-session plan loop")
    _log(f"  workdir:    {workdir}")
    _log(f"  num_tasks:  {requirements.num_tasks}")
    _log(f"  agent:      {args.agent}")
    _log(f"  skill:      hac-plan-pipeline")
    _log("=" * 60)

    prompt = build_ulw_prompt(
        num_tasks=args.num_tasks,
        bootstrap_task=task,
        rework_path=workdir / "state/current/targeted_rework.md",
        repo_root=ROOT,
    )

    # Gate runs inside the /ulw-loop (skill phase 4), not --on-complete — that hook
    # fired too early and wrote rework files before plan.json existed.
    backend = OhMyBackend(
        root=ROOT,
        binary_path=args.binary,
        base_port=args.base_port,
        timeout_sec=args.timeout_sec,
    )

    stop_event = threading.Event()
    monitor = threading.Thread(
        target=_stall_monitor,
        kwargs={
            "workdir": workdir,
            "interval_sec": args.stall_check_sec,
            "stop_event": stop_event,
        },
        daemon=True,
    )
    monitor.start()

    try:
        result = backend.run(
            workdir=workdir,
            prompt=prompt,
            agent=args.agent,
        )
    finally:
        stop_event.set()
        monitor.join(timeout=2)

    _log(f"OMO session finished  success={result.success}  rc={result.returncode}")

    # Some runs complete without persisting PI artifact; recover once via Prometheus.
    _ensure_plan_artifact(
        backend=backend,
        workdir=workdir,
        bootstrap_task=task,
        num_tasks=args.num_tasks,
    )

    # Official gate after session (writes evaluator_report if still failing)
    gate_passed, gate_summary = run_gate(workdir=workdir, num_tasks=args.num_tasks)
    _log(f"  post-session gate: {'PASS' if gate_passed else 'FAIL'}  {gate_summary[:100]}")

    if args.skip_validate:
        passed = result.success
    else:
        errors = validate(workdir=workdir, num_tasks=args.num_tasks)
        passed = not errors and result.returncode == 0 and gate_passed
        if errors:
            for err in errors:
                _log(f"  validate: {err}")

    _log("=" * 60)
    _log(f"RESULT: {'PASSED' if passed else 'FAILED'}")
    _log("=" * 60)
    print(json.dumps({"passed": passed, "omo_success": result.success}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
