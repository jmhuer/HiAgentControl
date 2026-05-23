from __future__ import annotations

from pathlib import Path
from unittest import mock

from hiagentcontrol.schemas import TaskDefinition
from hiagentcontrol.tools.run_omo_plan_loop import build_ulw_prompt


def test_build_ulw_prompt_contains_skill_and_num_tasks() -> None:
    task = TaskDefinition.model_validate(
        {
            "task": "Improve MNIST accuracy",
            "goal_type": "survey",
            "scope": "Research pipeline improvements",
        }
    )
    prompt = build_ulw_prompt(
        num_tasks=5,
        bootstrap_task=task,
        rework_path=None,
        repo_root=Path("/repo"),
    )
    assert "hac-plan-pipeline" in prompt
    assert "5" in prompt
    assert "run_plan_gate" in prompt
    assert "<promise>DONE</promise>" in prompt
    assert "Improve MNIST accuracy" in prompt


def test_run_omo_plan_loop_invokes_backend_once(tmp_path: Path) -> None:
    from hiagentcontrol.backends.ohmy_backend import OhMyRunResult
    from hiagentcontrol.tools import run_omo_plan_loop as mod

    workdir = tmp_path / "mnist"
    workdir.mkdir()
    plans = workdir / ".omo/plans"
    plans.mkdir(parents=True)
    (plans / "p.md").write_text("# plan\n", encoding="utf-8")
    state = workdir / "state/current"
    state.mkdir(parents=True)
    draft = state / "draft.md"
    draft.write_text("# draft\n" * 20, encoding="utf-8")

    plan_json = state / "plan.json"
    from tests.test_run_plan_gate import _minimal_plan_json

    plan_json.write_text(_minimal_plan_json(num_tasks=2), encoding="utf-8")

    bootstrap = Path(mod.ROOT) / "hiagentcontrol/bootstrap/plan_bootstrap_task.json"
    fake_result = OhMyRunResult(
        returncode=0,
        stdout="ok",
        session_id="s1",
        success=True,
        summary="done",
    )

    with mock.patch.object(mod, "OhMyBackend") as backend_cls:
        backend_cls.return_value.run.return_value = fake_result
        with mock.patch.object(mod, "validate", return_value=[]):
            with mock.patch("hiagentcontrol.tools.run_omo_plan_loop.run_gate", return_value=(True, "ok")):
                with mock.patch("sys.argv", ["run_omo_plan_loop", "--workdir", str(workdir), "--num-tasks", "2", "--no-clean"]):
                    try:
                        mod.main()
                    except SystemExit as exc:
                        assert exc.code == 0
        backend_cls.return_value.run.assert_called_once()
        call_kw = backend_cls.return_value.run.call_args.kwargs
        assert "hac-plan-pipeline" in call_kw["prompt"]
