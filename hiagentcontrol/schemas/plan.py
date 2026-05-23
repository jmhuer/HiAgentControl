from __future__ import annotations

from pydantic import BaseModel, Field

from .task import TaskDefinition


class PlanMetadata(BaseModel):
    """Top-level metadata for a plan artifact."""

    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    workdir: str = Field(min_length=1)
    source_draft_path: str = Field(min_length=1)
    loop_attempt: int = Field(ge=0, default=0)


class PlanDefinition(BaseModel):
    """Structured output for a plan instance."""

    plan_id: str = Field(min_length=1)
    metadata: PlanMetadata
    tasks: list[TaskDefinition] = Field(min_length=1)

