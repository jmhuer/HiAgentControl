from __future__ import annotations

import json
from pathlib import Path

from hiagentcontrol.gates.plan_lint import lint_plan_json


def _write_bad_plan(path: Path) -> None:
    path.write_text(json.dumps({"tasks": []}), encoding="utf-8")


def test_lint_plan_json_fails_on_invalid(tmp_path: Path) -> None:
    workdir = tmp_path / "mnist"
    plan = workdir / "state/current/plan.json"
    plan.parent.mkdir(parents=True)
    _write_bad_plan(plan)

    result = lint_plan_json(workdir=workdir, num_tasks=2)
    assert not result.passed
    assert result.issues
    text = result.to_agent_text()
    assert "PLAN LINT: FAIL" in text
    assert "fix:" in text


def test_lint_plan_json_passes_valid_plan(tmp_path: Path) -> None:
    from tests.test_run_plan_gate import _minimal_plan_json

    workdir = tmp_path / "mnist"
    plan = workdir / "state/current/plan.json"
    plan.parent.mkdir(parents=True)
    plan.write_text(_minimal_plan_json(num_tasks=2), encoding="utf-8")

    result = lint_plan_json(workdir=workdir, num_tasks=2)
    assert result.passed
    assert "PLAN LINT: PASS" in result.to_agent_text()
