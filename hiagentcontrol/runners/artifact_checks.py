from __future__ import annotations

from pathlib import Path


def plan_file_looks_corrupt(path: Path) -> bool:
    """Detect JSONL / opencode stream accidentally written into a plan markdown file."""
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return True
    if not head.strip():
        return True
    if head.lstrip().startswith("{"):
        return True
    markers = ('{"type":', '"sessionID":', '"type":"step_')
    return any(marker in head for marker in markers)
