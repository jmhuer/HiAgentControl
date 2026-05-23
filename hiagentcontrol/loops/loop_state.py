from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class LoopState(BaseModel):
    """Persisted loop state used across ULW re-entry."""

    run_id: str = Field(min_length=1)
    attempt: int = Field(ge=0, default=0)
    max_retries: int = Field(ge=0, default=2)
    stop: bool = False
    last_decision: str = "continue"
    last_updated_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

