from pathlib import Path

from hiagentcontrol.runners.artifact_checks import plan_file_looks_corrupt


def test_plan_file_looks_corrupt_detects_jsonl(tmp_path: Path) -> None:
    bad = tmp_path / "plan.md"
    bad.write_text('{"type":"step_finish","sessionID":"ses_x"}\n', encoding="utf-8")
    assert plan_file_looks_corrupt(bad)


def test_plan_file_looks_corrupt_accepts_markdown(tmp_path: Path) -> None:
    good = tmp_path / "plan.md"
    good.write_text("# MNIST Plan\n\n## Tasks\n- survey pipeline\n", encoding="utf-8")
    assert not plan_file_looks_corrupt(good)
