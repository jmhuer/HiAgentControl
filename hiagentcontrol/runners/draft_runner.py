from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from hiagentcontrol.backends import OhMyBackend, OhMyRunResult
from hiagentcontrol.run_config import RunRequirements
from hiagentcontrol.runners.phase_errors import DeliverableError


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


@dataclass(frozen=True)
class DraftRunnerConfig:
    prompt_template: Path
    requirements: RunRequirements = RunRequirements()
    plan_glob: str = ".omo/plans/*.md"
    draft_relative_path: str = "state/current/draft.md"
    agent: str = "Atlas"


@dataclass(frozen=True)
class DraftRunArtifact:
    result: OhMyRunResult
    draft_path: Path


class DraftRunner:
    """Atlas executes the plan and writes state/current/draft.md (one oh-my-opencode run)."""

    def __init__(self, *, backend: OhMyBackend, config: DraftRunnerConfig) -> None:
        self.backend = backend
        self.config = config

    def run(
        self,
        *,
        workdir: Path,
        loop_attempt: int = 0,
        rework_path: Path | None = None,
        evaluator_report_path: Path | None = None,
    ) -> DraftRunArtifact:
        plan_paths = sorted(workdir.glob(self.config.plan_glob))
        if not plan_paths:
            raise DeliverableError("DRAFT", "No plan file under .omo/plans/ — run PLAN first")

        draft_path = workdir / self.config.draft_relative_path
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        if not draft_path.exists():
            draft_path.write_text("# MNIST Improvement Draft\n\n", encoding="utf-8")

        template = self.config.prompt_template.read_text(encoding="utf-8").strip()
        prompt_parts = [
            template,
            "",
            f"Plan file: `{plan_paths[-1]}`",
            f"Draft path: `{draft_path}`",
            f"Loop attempt: {loop_attempt}",
        ]
        if evaluator_report_path and evaluator_report_path.exists():
            prompt_parts.append(f"Prior gate failures: `{evaluator_report_path}`")
        if rework_path and rework_path.exists():
            prompt_parts.append(f"Targeted rework: `{rework_path}`")

        prompt_parts.extend(["", self.config.requirements.prompt_block()])
        prompt = "\n".join(prompt_parts)
        _log(f"  [draft_runner] Atlas (attempt={loop_attempt})")
        result = self.backend.run(
            workdir=workdir,
            prompt=prompt,
            port_offset=15,
            agent=self.config.agent,
        )
        if result.returncode != 0:
            raise DeliverableError("DRAFT", f"oh-my-opencode exited with code {result.returncode}")

        if not draft_path.is_file():
            raise DeliverableError(
                "DRAFT",
                "draft.md not created at state/current/draft.md — use edit on the draft file",
            )

        _log(f"  [draft_runner] done  draft={draft_path.name}")
        return DraftRunArtifact(result=result, draft_path=draft_path)
