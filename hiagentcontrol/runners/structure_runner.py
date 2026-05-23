from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from hiagentcontrol.backends import OhMyBackend, OhMyRunResult
from hiagentcontrol.gates.deterministic_checks import validate_plan_json, validate_plan_task_count
from hiagentcontrol.run_config import RunRequirements
from hiagentcontrol.runners.phase_errors import DeliverableError


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


@dataclass(frozen=True)
class StructureRunnerConfig:
    prompt_template: Path
    requirements: RunRequirements = RunRequirements()
    plan_example_path: Path | None = None
    output_relative_path: str = "state/current/plan.json"
    agent: str = "Sisyphus"


@dataclass(frozen=True)
class StructureRunArtifact:
    result: OhMyRunResult
    output_path: Path
    schema_valid: bool


class StructureRunner:
    """Formats draft.md into schema-valid plan.json (one oh-my-opencode run)."""

    def __init__(self, *, backend: OhMyBackend, config: StructureRunnerConfig) -> None:
        self.backend = backend
        self.config = config

    def run(
        self,
        *,
        workdir: Path,
        draft_path: Path,
        output_path: Path | None = None,
        rework_path: Path | None = None,
        evaluator_report_path: Path | None = None,
        loop_attempt: int = 0,
    ) -> StructureRunArtifact:
        resolved_output = output_path or (workdir / self.config.output_relative_path)
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        if not draft_path.exists():
            raise DeliverableError(
                "STRUCTURE",
                f"draft.md missing at {draft_path} — run DRAFT phase first",
            )

        template = self.config.prompt_template.read_text(encoding="utf-8").strip()
        example_path = self.config.plan_example_path
        if example_path is None:
            example_path = (
                self.config.prompt_template.parent.parent / "schemas/json/plan_example.json"
            )

        prompt_parts = [
            template,
            "",
            f"Draft path (read first): `{draft_path}`",
            f"Output path (edit JSON here): `{resolved_output}`",
            f"Loop attempt: {loop_attempt}",
            f"Workdir for metadata.workdir: `{workdir.name}`",
        ]
        if example_path.exists():
            example_json = example_path.read_text(encoding="utf-8").strip()
            prompt_parts.extend(
                [
                    "",
                    "## PlanDefinition example (follow this shape)",
                    f"```json\n{example_json}\n```",
                ]
            )
        if evaluator_report_path and evaluator_report_path.exists():
            prompt_parts.append(f"Prior gate failures: `{evaluator_report_path}`")
        if rework_path and rework_path.exists():
            prompt_parts.append(f"Targeted rework: `{rework_path}`")

        prompt_parts.extend(["", self.config.requirements.prompt_block()])
        prompt = "\n".join(prompt_parts)
        _log("  [structure_runner] draft -> plan.json")
        result = self.backend.run(
            workdir=workdir,
            prompt=prompt,
            port_offset=20,
            agent=self.config.agent,
        )
        if result.returncode != 0:
            raise DeliverableError("STRUCTURE", f"oh-my-opencode exited with code {result.returncode}")
        if not resolved_output.exists():
            raise DeliverableError(
                "STRUCTURE",
                f"plan.json not created at {resolved_output} — use edit on state/current/plan.json",
            )

        schema_checks = validate_plan_json(plan_json_path=resolved_output)
        schema_check = next((c for c in schema_checks if c.name == "plan-json-schema"), None)
        schema_valid = schema_check.passed if schema_check else False
        task_check = validate_plan_task_count(
            plan_json_path=resolved_output,
            min_tasks=self.config.requirements.num_tasks,
        )
        _log(
            f"  [structure_runner] done  schema_valid={schema_valid}  "
            f"tasks={task_check.detail}"
        )
        return StructureRunArtifact(
            result=result,
            output_path=resolved_output,
            schema_valid=schema_valid,
        )
