from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path


HYPOTHESIS_TEMPLATES = [
    {
        "theme": "sparsity-regularization",
        "hypothesis": "Increasing structured sparsity pressure can improve robustness without harming quick-test correctness.",
        "planned_change": "Track sparse activation marker for future model-architecture tuning.",
    },
    {
        "theme": "optimization-stability",
        "hypothesis": "Conservative optimization updates reduce noisy regressions in iterative research loops.",
        "planned_change": "Record optimization stability experiment marker for later training-step integration.",
    },
    {
        "theme": "architecture-signal-routing",
        "hypothesis": "Better feature-routing constraints may improve signal quality in downstream classifiers.",
        "planned_change": "Record architecture signal-routing marker to anchor subsequent architectural edits.",
    },
]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _append_marker(target_file: Path, marker: str) -> None:
    if not target_file.exists():
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(
            '"""Phase-1 research marker file."""\n\nfrom __future__ import annotations\n\nRESEARCH_MARKERS: list[str] = []\n',
            encoding="utf-8",
        )

    content = target_file.read_text(encoding="utf-8")
    if "RESEARCH_MARKERS: list[str] = []" in content:
        content = content.replace(
            "RESEARCH_MARKERS: list[str] = []",
            f'RESEARCH_MARKERS: list[str] = [\n    "{marker}",\n]',
            1,
        )
    elif "RESEARCH_MARKERS: list[str] = [" in content:
        content = content.replace("RESEARCH_MARKERS: list[str] = [", f'RESEARCH_MARKERS: list[str] = [\n    "{marker}",', 1)
    else:
        content = content.rstrip() + f'\n\nRESEARCH_MARKERS: list[str] = [\n    "{marker}",\n]\n'
    target_file.write_text(content, encoding="utf-8")


def _append_hypothesis(target_file: Path, entry: dict[str, str]) -> None:
    if not target_file.exists():
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(
            '"""Structured hypothesis log for phase-1 research loops."""\n\nfrom __future__ import annotations\n\nHYPOTHESES: list[dict[str, str]] = []\n',
            encoding="utf-8",
        )

    content = target_file.read_text(encoding="utf-8")
    item = (
        "    {\n"
        f'        "hypothesis_id": "{entry["hypothesis_id"]}",\n'
        f'        "theme": "{entry["theme"]}",\n'
        f'        "hypothesis": "{entry["hypothesis"]}",\n'
        f'        "planned_change": "{entry["planned_change"]}",\n'
        f'        "run_id": "{entry["run_id"]}",\n'
        f'        "timestamp": "{entry["timestamp"]}"\n'
        "    },\n"
    )
    if "HYPOTHESES: list[dict[str, str]] = []" in content:
        content = content.replace(
            "HYPOTHESES: list[dict[str, str]] = []",
            f"HYPOTHESES: list[dict[str, str]] = [\n{item}]",
            1,
        )
    elif "HYPOTHESES: list[dict[str, str]] = [" in content:
        content = content.replace("HYPOTHESES: list[dict[str, str]] = [", f"HYPOTHESES: list[dict[str, str]] = [\n{item}", 1)
    else:
        content = content.rstrip() + f"\n\nHYPOTHESES: list[dict[str, str]] = [\n{item}]\n"
    target_file.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Mock research-group agent for phase-1 loop testing.")
    parser.add_argument("--group-id", required=True)
    parser.add_argument("--marker-file", type=Path, default=Path("mnist/pipeline/research_markers.py"))
    parser.add_argument("--hypothesis-file", type=Path, default=Path("mnist/pipeline/research_hypotheses.py"))
    args = parser.parse_args()

    run_id = os.environ.get("HIAGENTRESEARCH_RUN_ID", "run_unknown")
    state_dir = Path(os.environ.get("HIAGENTRESEARCH_STATE_DIR", "hiagentresearch/state"))
    packet_path = state_dir / "intent_packets" / f"{args.group_id}.json"
    packet = {}
    if packet_path.exists():
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    attempt = int(packet.get("attempt_count", 0)) + 1

    template = HYPOTHESIS_TEMPLATES[(attempt - 1) % len(HYPOTHESIS_TEMPLATES)]
    hypothesis_id = f"{args.group_id}-h{attempt}"
    ts = _utc_now()
    marker = f"{args.group_id}:{run_id}:{hypothesis_id}:{ts}"
    hypothesis_entry = {
        "hypothesis_id": hypothesis_id,
        "theme": template["theme"],
        "hypothesis": template["hypothesis"],
        "planned_change": template["planned_change"],
        "run_id": run_id,
        "timestamp": ts,
    }

    _append_marker(args.marker_file, marker)
    _append_hypothesis(args.hypothesis_file, hypothesis_entry)

    activity_dir = state_dir / "agent_activity" / args.group_id
    activity_dir.mkdir(parents=True, exist_ok=True)
    activity = {
        "run_id": run_id,
        "group_id": args.group_id,
        "attempt_from_packet": attempt,
        "marker": marker,
        "hypothesis_entry": hypothesis_entry,
        "marker_file": str(args.marker_file),
        "hypothesis_file": str(args.hypothesis_file),
        "timestamp": ts,
    }
    (activity_dir / f"{run_id}.json").write_text(json.dumps(activity, indent=2), encoding="utf-8")
    print(json.dumps(activity, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
