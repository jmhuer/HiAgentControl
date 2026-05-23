from __future__ import annotations

import json
from pathlib import Path

from hiagentcontrol.loops.rework_phase import DONE_PROMISE, ReworkPhase, choose_rework_phase
from hiagentcontrol.loops import EvaluatorReport, from_outcome
from hiagentcontrol.loops.evaluator_report import ReportCheck
from hiagentcontrol.gates import GlobalEvaluationNode
from hiagentcontrol.tools.run_plan_gate import run_gate, write_targeted_rework


def _minimal_plan_json(*, num_tasks: int = 2) -> str:
    tasks = []
    for i in range(num_tasks):
        tasks.append(
            {
                "task": f"Research area {i + 1}",
                "goal_type": "survey",
                "scope": (
                    "TRY: Survey augmentation papers. "
                    "FILES: pipeline/train.py. "
                    "CHANGE: document candidate transforms in draft only. "
                    "VERIFY: python eval/run_eval.py --quick with accuracy >= 0.99 and latency_ms <= 13.0."
                ),
                "required_skills": [],
                "required_tools": [],
                "must_not_do": [],
                "context": [{"path": "mnist/README.md", "note": "baseline"}],
                "gate": {"script_checks": [], "ai_eval": None},
            }
        )
    payload = {
        "plan_id": "test-plan",
        "metadata": {
            "title": "Test",
            "objective": "Test objective",
            "workdir": "mnist",
            "source_draft_path": "state/current/draft.md",
            "loop_attempt": 0,
        },
        "tasks": tasks,
    }
    return json.dumps(payload, indent=2)


def test_choose_rework_phase_format_for_schema() -> None:
    report = EvaluatorReport(
        passed=False,
        summary="fail",
        checks=[
            ReportCheck(
                name="plan-json-schema",
                passed=False,
                detail="bad",
                target_ref="plan.json",
            )
        ],
    )
    assert choose_rework_phase(report=report) == ReworkPhase.FORMAT




def test_choose_rework_phase_format_for_count_mismatch() -> None:
    report = EvaluatorReport(
        passed=False,
        summary="fail",
        checks=[
            ReportCheck(
                name="plan-task-count",
                passed=False,
                detail="count mismatch",
                target_ref="plan.json#tasks",
            )
        ],
    )
    assert choose_rework_phase(report=report) == ReworkPhase.FORMAT


def test_choose_rework_phase_pi_for_missing() -> None:
    report = EvaluatorReport(
        passed=False,
        summary="fail",
        checks=[
            ReportCheck(
                name="plan-json-exists",
                passed=False,
                detail="missing",
                target_ref="plan.json",
            )
        ],
    )
    assert choose_rework_phase(report=report) == ReworkPhase.PI


def test_run_gate_prints_done_on_valid_plan(tmp_path: Path) -> None:
    workdir = tmp_path / "mnist"
    plan_path = workdir / "state/current/plan.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(_minimal_plan_json(num_tasks=2), encoding="utf-8")

    import io
    import sys

    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        passed, msg = run_gate(workdir=workdir, num_tasks=2)
    finally:
        sys.stdout = old_stdout

    assert passed
    assert DONE_PROMISE in msg
    assert DONE_PROMISE in captured.getvalue()
    rework = (workdir / "state/current/targeted_rework.md").read_text(encoding="utf-8")
    assert "rework_phase" in rework or "No failed" in rework


def test_run_gate_fails_wrong_count(tmp_path: Path, capsys) -> None:
    workdir = tmp_path / "mnist"
    plan_path = workdir / "state/current/plan.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(_minimal_plan_json(num_tasks=1), encoding="utf-8")

    passed, _ = run_gate(workdir=workdir, num_tasks=2)
    assert not passed
    rework = (workdir / "state/current/targeted_rework.md").read_text(encoding="utf-8")
    assert "rework_phase: format" in rework


def test_run_gate_missing_plan_routes_to_format_if_draft_exists(tmp_path: Path) -> None:
    workdir = tmp_path / "mnist"
    state = workdir / "state/current"
    state.mkdir(parents=True)
    (state / "draft.md").write_text("# draft\n", encoding="utf-8")

    passed, _ = run_gate(workdir=workdir, num_tasks=2)
    assert not passed
    rework = (state / "targeted_rework.md").read_text(encoding="utf-8")
    assert "rework_phase: format" in rework


def test_write_targeted_rework_includes_phase(tmp_path: Path) -> None:
    outcome = GlobalEvaluationNode().evaluate(
        workdir=tmp_path,
        deliverable_path=tmp_path / "missing.json",
        gate=None,
        min_tasks=1,
    )
    report = from_outcome(outcome)
    path = tmp_path / "targeted_rework.md"
    write_targeted_rework(path=path, report=report, phase=ReworkPhase.PI)
    text = path.read_text(encoding="utf-8")
    assert "rework_phase: pi" in text
