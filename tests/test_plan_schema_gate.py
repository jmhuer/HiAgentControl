from __future__ import annotations

import json
from pathlib import Path

from hiagentcontrol.schemas import PlanDefinition, TaskDefinition
from hiagentcontrol.schemas.export_json_schema import export_schemas


def test_bootstrap_task_is_valid_task_definition() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    bootstrap_path = repo_root / "hiagentcontrol/bootstrap/plan_bootstrap_task.json"
    payload = bootstrap_path.read_text(encoding="utf-8")
    parsed = TaskDefinition.model_validate_json(payload)
    assert parsed.goal_type == "survey"
    assert parsed.gate is not None


def test_plan_definition_schema_export_contract(tmp_path: Path) -> None:
    exported = export_schemas(out_dir=tmp_path)
    plan_schema_path = exported["plan_definition.schema.json"]
    task_schema_path = exported["task_definition.schema.json"]
    assert plan_schema_path.exists()
    assert task_schema_path.exists()

    plan_schema = json.loads(plan_schema_path.read_text(encoding="utf-8"))
    task_schema = json.loads(task_schema_path.read_text(encoding="utf-8"))
    assert plan_schema.get("type") == "object"
    assert task_schema.get("type") == "object"
    assert "properties" in plan_schema
    assert "properties" in task_schema


def test_minimal_plan_definition_validates() -> None:
    plan = PlanDefinition.model_validate(
        {
            "plan_id": "mnist-plan-v2",
            "metadata": {
                "title": "MNIST Improvement Plan",
                "objective": "Improve accuracy while preserving reproducibility.",
                "workdir": "mnist",
                "source_draft_path": "state/current/draft.md",
                "loop_attempt": 1,
            },
            "tasks": [
                {
                    "task": "Survey augmentation approaches and expected gains.",
                    "goal_type": "survey",
                    "scope": "Gather references and map to candidate experiments.",
                    "required_skills": ["research"],
                    "required_tools": ["webfetch", "read"],
                    "must_not_do": ["Do not invent benchmark numbers."],
                    "context": [{"path": "mnist/README.md", "note": "Project baseline."}],
                    "gate": {
                        "script_checks": [],
                        "ai_eval": {
                            "enabled": True,
                            "rubric": ["Coverage and grounding are adequate."],
                        },
                    },
                }
            ],
        }
    )
    assert plan.plan_id == "mnist-plan-v2"

