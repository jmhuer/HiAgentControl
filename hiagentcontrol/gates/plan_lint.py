from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from hiagentcontrol.gates import GlobalEvaluationNode
from hiagentcontrol.loops import from_outcome
from hiagentcontrol.schemas import GateDefinition


@dataclass(frozen=True)
class PlanLintIssue:
    check: str
    detail: str
    target_ref: str | None
    fix_hint: str


@dataclass(frozen=True)
class PlanLintResult:
    passed: bool
    summary: str
    issues: tuple[PlanLintIssue, ...]

    def to_agent_text(self) -> str:
        if self.passed:
            return "PLAN LINT: PASS — plan.json matches PlanDefinition and gate checks."
        lines = [f"PLAN LINT: FAIL — {len(self.issues)} issue(s)", ""]
        for issue in self.issues:
            lines.append(f"- [{issue.check}] {issue.detail}")
            if issue.fix_hint:
                lines.append(f"  fix: {issue.fix_hint}")
        return "\n".join(lines)

    def to_json_dict(self) -> dict:
        return {
            "passed": self.passed,
            "summary": self.summary,
            "issues": [
                {
                    "check": i.check,
                    "detail": i.detail,
                    "target_ref": i.target_ref,
                    "fix_hint": i.fix_hint,
                }
                for i in self.issues
            ],
        }


_FIX_HINTS: dict[str, str] = {
    "plan-json-exists": "Write state/current/plan.json using plan_example.json shape.",
    "plan-json-schema": "Add plan_id, metadata, tasks[]; match hiagentcontrol/schemas/json/plan_example.json.",
    "plan-task-count": "Set tasks array length to exactly the required N.",
    "plan-task-scope": "Each scope needs TRY:/FILES:/CHANGE:/VERIFY: labels; paths must exist under pipeline/ or eval/.",
}


def lint_plan_json(
    *,
    workdir: Path,
    num_tasks: int,
    deliverable_relative: str = "state/current/plan.json",
    gate: GateDefinition | None = None,
) -> PlanLintResult:
    """
    LSP-style pre-check for plan.json — same rules as the official gate, no DONE tag or rework files.
    """
    deliverable = workdir / deliverable_relative
    outcome = GlobalEvaluationNode().evaluate(
        workdir=workdir,
        deliverable_path=deliverable,
        gate=gate,
        min_tasks=num_tasks,
        exact_tasks=num_tasks,
    )
    report = from_outcome(outcome)
    issues: list[PlanLintIssue] = []
    for check in report.checks:
        if check.passed:
            continue
        issues.append(
            PlanLintIssue(
                check=check.name,
                detail=check.detail,
                target_ref=check.target_ref,
                fix_hint=_FIX_HINTS.get(check.name, "Fix the field cited in target_ref."),
            )
        )
    return PlanLintResult(
        passed=report.passed,
        summary=report.summary,
        issues=tuple(issues),
    )
