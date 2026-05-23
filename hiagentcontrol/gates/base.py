from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str
    target_ref: str | None = None


@dataclass(frozen=True)
class EvaluationOutcome:
    passed: bool
    summary: str
    checks: tuple[CheckResult, ...]
    deliverable_path: Path
    follow_up_work_items: tuple[str, ...] = field(default_factory=tuple)

