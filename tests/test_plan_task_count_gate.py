from __future__ import annotations

import json
from pathlib import Path

from hiagentcontrol.gates.deterministic_checks import validate_plan_task_count


def test_validate_plan_task_count_passes(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "plan_id": "t",
                "metadata": {
                    "title": "T",
                    "objective": "O",
                    "workdir": "mnist",
                    "source_draft_path": "state/current/draft.md",
                },
                "tasks": [
                    {"task": f"Task {i}", "goal_type": "feature", "scope": "scope " * 20}
                    for i in range(3)
                ],
            }
        ),
        encoding="utf-8",
    )
    result = validate_plan_task_count(plan_json_path=plan_path, min_tasks=3)
    assert result.passed


def test_validate_plan_task_count_fails_when_too_few(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "plan_id": "t",
                "metadata": {
                    "title": "T",
                    "objective": "O",
                    "workdir": "mnist",
                    "source_draft_path": "state/current/draft.md",
                },
                "tasks": [
                    {"task": "Only one", "goal_type": "feature", "scope": "x"},
                ],
            }
        ),
        encoding="utf-8",
    )
    result = validate_plan_task_count(plan_json_path=plan_path, min_tasks=10)
    assert not result.passed


def test_validate_plan_task_count_exact(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "plan_id": "t",
                "metadata": {
                    "title": "T",
                    "objective": "O",
                    "workdir": "mnist",
                    "source_draft_path": "state/current/draft.md",
                },
                "tasks": [
                    {"task": f"Task {i}", "goal_type": "feature", "scope": "scope " * 20}
                    for i in range(5)
                ],
            }
        ),
        encoding="utf-8",
    )
    ok = validate_plan_task_count(plan_json_path=plan_path, min_tasks=1, exact_tasks=5)
    assert ok.passed
    bad = validate_plan_task_count(plan_json_path=plan_path, min_tasks=1, exact_tasks=3)
    assert not bad.passed
