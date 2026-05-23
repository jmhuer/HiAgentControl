from __future__ import annotations

from pathlib import Path

from hiagentcontrol.tools.clean_run_state import (
    clean_for_fresh_run,
    clean_for_structure_retry,
)


def test_clean_for_fresh_run_removes_artifacts(tmp_path: Path) -> None:
    workdir = tmp_path / "mnist"
    state = workdir / "state/current"
    state.mkdir(parents=True)
    (state / "draft.md").write_text("# draft\n", encoding="utf-8")
    (state / "plan.json").write_text("{}", encoding="utf-8")
    plans = workdir / ".omo/plans"
    plans.mkdir(parents=True)
    (plans / "p.md").write_text("# plan\n", encoding="utf-8")

    removed = clean_for_fresh_run(workdir)
    assert not (state / "draft.md").exists()
    assert not (state / "plan.json").exists()
    assert not (plans / "p.md").exists()
    assert any("draft.md" in r for r in removed)


def test_clean_for_structure_retry_keeps_draft(tmp_path: Path) -> None:
    workdir = tmp_path / "mnist"
    state = workdir / "state/current"
    state.mkdir(parents=True)
    (state / "draft.md").write_text("# draft\n", encoding="utf-8")
    (state / "plan.json").write_text("{}", encoding="utf-8")
    plans = workdir / ".omo/plans"
    plans.mkdir(parents=True)
    (plans / "p.md").write_text("# plan\n", encoding="utf-8")

    clean_for_structure_retry(workdir)
    assert (state / "draft.md").is_file()
    assert not (state / "plan.json").exists()
    assert (plans / "p.md").is_file()
