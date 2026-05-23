from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CleanOptions:
    """What to remove before a new loop run."""

    draft: bool = True
    plan: bool = True
    gate_artifacts: bool = True
    omo_logs: bool = True
    plans: bool = True
    notepads: bool = False


STATE_ARTIFACTS = (
    "draft.md",
    "plan.json",
    "evaluator_report.json",
    "targeted_rework.md",
    "loop_state.json",
)


def clean_run_state(
    workdir: Path,
    *,
    options: CleanOptions | None = None,
) -> list[str]:
    """
    Remove prior run artifacts so agents start fresh.

    Returns relative paths removed (for logging).
    """
    opts = options or CleanOptions()
    removed: list[str] = []
    workdir = workdir.resolve()
    state_dir = workdir / "state/current"

    if opts.gate_artifacts or opts.draft or opts.plan:
        state_dir.mkdir(parents=True, exist_ok=True)
        for name in STATE_ARTIFACTS:
            if name == "draft.md" and not opts.draft:
                continue
            if name == "plan.json" and not opts.plan:
                continue
            if name in {
                "evaluator_report.json",
                "targeted_rework.md",
                "loop_state.json",
            } and not opts.gate_artifacts:
                continue
            path = state_dir / name
            if path.is_file():
                path.unlink()
                removed.append(str(path.relative_to(workdir)))

    if opts.omo_logs and state_dir.is_dir():
        for path in state_dir.glob("omo_run_*.jsonl"):
            path.unlink()
            removed.append(str(path.relative_to(workdir)))

    if opts.plans:
        plans_dir = workdir / ".omo/plans"
        if plans_dir.is_dir():
            for path in plans_dir.glob("*.md"):
                path.unlink()
                removed.append(str(path.relative_to(workdir)))

    if opts.notepads:
        notepads = workdir / ".omo/notepads"
        if notepads.is_dir():
            shutil.rmtree(notepads)
            removed.append(str(notepads.relative_to(workdir)))

    return removed


def clean_for_fresh_run(workdir: Path) -> list[str]:
    """Full cleanup before a new end-to-end loop."""
    return clean_run_state(workdir, options=CleanOptions())


def clean_for_structure_retry(workdir: Path) -> list[str]:
    """Keep draft.md and PI plans; reset plan + gate outputs only."""
    return clean_run_state(
        workdir,
        options=CleanOptions(
            draft=False,
            plan=True,
            gate_artifacts=True,
            omo_logs=True,
            plans=False,
        ),
    )


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove prior HiAgentControl run artifacts.")
    parser.add_argument("--workdir", default="mnist")
    parser.add_argument(
        "--mode",
        choices=("fresh", "structure"),
        default="fresh",
        help="fresh=full clean; structure=keep draft+plans, clear plan.json",
    )
    parser.add_argument("--also-notepads", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _args()
    workdir = Path(args.workdir).resolve()
    if args.mode == "structure":
        removed = clean_for_structure_retry(workdir)
    else:
        opts = CleanOptions(notepads=args.also_notepads)
        removed = clean_run_state(workdir, options=opts)
    if removed:
        print("Removed:")
        for path in removed:
            print(f"  {path}")
    else:
        print("Nothing to remove.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
