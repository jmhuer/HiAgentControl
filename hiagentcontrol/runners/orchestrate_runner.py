from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from hiagentcontrol.backends import OhMyBackend, OhMyRunResult
from hiagentcontrol.run_config import RunRequirements
from hiagentcontrol.runners.artifact_checks import plan_file_looks_corrupt
from hiagentcontrol.runners.phase_errors import DeliverableError
from hiagentcontrol.schemas import TaskDefinition


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


@dataclass(frozen=True)
class OrchestrateRunArtifact:
    result: OhMyRunResult
    plan_paths: tuple[Path, ...]


@dataclass(frozen=True)
class OrchestrateRunnerConfig:
    prompt_template: Path
    requirements: RunRequirements = RunRequirements()
    plan_glob: str = ".omo/plans/*.md"
    agent: str = "Prometheus"


class OrchestrateRunner:
    """Prometheus planning phase: create `.omo/plans/*.md` on disk via edit."""

    def __init__(self, *, backend: OhMyBackend, config: OrchestrateRunnerConfig) -> None:
        self.backend = backend
        self.config = config

    def run(
        self,
        *,
        workdir: Path,
        bootstrap_task: TaskDefinition,
        loop_attempt: int = 0,
        rework_path: Path | None = None,
        evaluator_report_path: Path | None = None,
    ) -> OrchestrateRunArtifact:
        (workdir / ".omo" / "plans").mkdir(parents=True, exist_ok=True)

        prompt_template = self.config.prompt_template.read_text(encoding="utf-8").strip()
        prompt_parts = [
            prompt_template,
            "",
            "## Bootstrap task instance",
            f"```json\n{bootstrap_task.model_dump_json(indent=2)}\n```",
            f"Loop attempt: {loop_attempt}",
            "",
            "## Tooling reminder",
            "- Persist plan with **edit** only (write is denied).",
            "- Path: `.omo/plans/<name>.md`",
        ]
        if evaluator_report_path and evaluator_report_path.exists():
            prompt_parts.append(f"Prior gate failures: `{evaluator_report_path}`")
        if rework_path and rework_path.exists():
            prompt_parts.append(f"Targeted rework: `{rework_path}`")

        prompt_parts.extend(["", self.config.requirements.prompt_block()])
        prompt = "\n".join(prompt_parts)
        _log(f"  [plan_runner] Prometheus plan (attempt={loop_attempt})")
        result = self.backend.run(
            workdir=workdir,
            prompt=prompt,
            port_offset=10,
            agent=self.config.agent,
        )
        if result.returncode != 0:
            raise DeliverableError("PLAN", f"opencode exited with code {result.returncode}")

        plan_paths = tuple(sorted(workdir.glob(self.config.plan_glob)))
        if not plan_paths:
            raise DeliverableError(
                "PLAN",
                "No plan file at .omo/plans/*.md — use edit to write the plan",
            )

        corrupt = [p for p in plan_paths if plan_file_looks_corrupt(p)]
        if corrupt:
            names = ", ".join(str(p.relative_to(workdir)) for p in corrupt)
            raise DeliverableError("PLAN", f"Plan file looks corrupt: {names}")

        _log(f"  [plan_runner] done  plan_files={len(plan_paths)}")
        return OrchestrateRunArtifact(result=result, plan_paths=plan_paths)
