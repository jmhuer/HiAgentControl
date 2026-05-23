from __future__ import annotations

from enum import StrEnum


class GoalType(StrEnum):
    """Canonical goal types for task instances."""

    FEATURE = "feature"
    ABLATION_STUDY = "ablation_study"
    ARCHITECTURE = "architecture"
    HYGIENE = "hygiene"
    SURVEY = "survey"
    CODEBASE_RECON = "codebase_recon"
    EXPERIMENT = "experiment"

