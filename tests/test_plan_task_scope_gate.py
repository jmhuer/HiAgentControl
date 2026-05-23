from __future__ import annotations

import json
from pathlib import Path

from hiagentcontrol.gates.deterministic_checks import validate_plan_task_scopes


def test_validate_plan_task_scopes_passes(tmp_path: Path) -> None:
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
                    {
                        "task": "Augment",
                        "goal_type": "feature",
                        "scope": (
                            "TRY: Add RandomRotation(10). "
                            "FILES: pipeline/train.py. "
                            "CHANGE: extend Compose. "
                            "VERIFY: eval/run_eval.py --quick accuracy >= 0.99."
                            + " " * 80
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = validate_plan_task_scopes(plan_json_path=plan_path)
    assert result.passed


def test_validate_plan_task_scopes_fails_when_vague(tmp_path: Path) -> None:
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
                    {
                        "task": "Improve model",
                        "goal_type": "feature",
                        "scope": "Make the model better.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = validate_plan_task_scopes(plan_json_path=plan_path)
    assert not result.passed


def test_validate_plan_task_scopes_fails_on_phantom_model_path(tmp_path: Path) -> None:
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
                    {
                        "task": "Batch norm",
                        "goal_type": "feature",
                        "scope": (
                            "TRY: Add BatchNorm2d after conv layers. "
                            "FILES: pipeline/model.py. "
                            "CHANGE: insert nn.BatchNorm2d in mnist_cnn.py. "
                            "VERIFY: python eval/run_eval.py --quick accuracy >= 0.988."
                            + " " * 80
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = validate_plan_task_scopes(plan_json_path=plan_path)
    assert not result.passed
    assert "mnist_cnn.py" in result.detail
