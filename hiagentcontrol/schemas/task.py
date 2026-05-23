from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .goal_types import GoalType

ScriptCheckKind = Literal["script", "test", "metric"]


class ScriptCheck(BaseModel):
    """Deterministic executable check."""

    kind: ScriptCheckKind
    name: str = Field(min_length=1)
    path: str = Field(min_length=1)
    args: list[str] = Field(default_factory=list)
    threshold: str | None = None
    cwd: str | None = None  # override working directory; defaults to loop workdir


class AiEvalCheck(BaseModel):
    """Optional AI review after deterministic checks."""

    enabled: bool = True
    rubric: list[str] = Field(default_factory=list)
    model_hint: str | None = None


class GateDefinition(BaseModel):
    """
    Optional gate contract.

    A gate may be empty (no deterministic check and no AI evaluation)
    when a task intentionally relies on supervisor judgment.
    """

    script_checks: list[ScriptCheck] = Field(default_factory=list)
    ai_eval: AiEvalCheck | None = None


class ContextRef(BaseModel):
    """Context references for grounded work and traceability."""

    path: str = Field(min_length=1)
    note: str | None = None


class TaskDefinition(BaseModel):
    """Generic task instance used by plan and execution workflows."""

    task: str = Field(min_length=1)
    goal_type: GoalType
    scope: str = Field(min_length=1)
    required_skills: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    gate: GateDefinition | None = None
    must_not_do: list[str] = Field(default_factory=list)
    context: list[ContextRef] = Field(default_factory=list)

