from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "mnist/.opencode/skills"


def _skill_name(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^name:\s*(\S+)\s*$", text, re.MULTILINE)
    assert match, f"missing name in {skill_dir}"
    return match.group(1)


def test_hac_plan_pipeline_skill() -> None:
    path = SKILLS / "hac-plan-pipeline"
    assert path.is_dir()
    assert _skill_name(path) == "hac-plan-pipeline"
    body = (path / "SKILL.md").read_text(encoding="utf-8")
    assert "Phase 1" in body and "run_plan_gate" in body


def test_hac_format_plan_json_skill() -> None:
    path = SKILLS / "hac-format-plan-json"
    assert path.is_dir()
    assert _skill_name(path) == "hac-format-plan-json"
    body = (path / "SKILL.md").read_text(encoding="utf-8")
    assert "plan.json" in body and "draft.md" in body


def test_agents_md_exists() -> None:
    agents = REPO / "mnist/AGENTS.md"
    assert agents.is_file()
    text = agents.read_text(encoding="utf-8")
    assert "rework_phase" in text
