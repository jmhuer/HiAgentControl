from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from cursor_sdk import Agent, AgentOptions, LocalAgentOptions

from hiagentresearch.src.models import IntentPacket, ResearchGroup, utc_now_iso


class AgentBackendError(RuntimeError):
    """Raised when agent backend execution fails."""


@dataclass(slots=True)
class AgentExecutionRecord:
    backend: str
    success: bool
    status: str
    summary: str
    raw_result: dict
    timestamp: str


def run_cursor_agent_cycle(
    *,
    workdir: Path,
    run_dir: Path,
    group: ResearchGroup,
    intent_packet: IntentPacket,
    run_id: str,
    model: str = "composer-2.5",
) -> AgentExecutionRecord:
    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        raise AgentBackendError(
            "CURSOR_API_KEY is missing. Export CURSOR_API_KEY before running real cursor-agent loops."
        )

    prompt = _build_prompt(group=group, intent_packet=intent_packet, run_id=run_id)
    result = Agent.prompt(
        prompt,
        AgentOptions(
            api_key=api_key,
            model=model,
            local=LocalAgentOptions(cwd=str(workdir)),
        ),
    )
    status = str(result.status)
    success = status == "finished"
    record = AgentExecutionRecord(
        backend="cursor_sdk",
        success=success,
        status=status,
        summary=str(result.result)[:2000],
        raw_result={
            "id": getattr(result, "id", ""),
            "agent_id": getattr(result, "agent_id", ""),
            "status": status,
            "result": str(getattr(result, "result", "")),
            "duration_ms": int(getattr(result, "duration_ms", 0)),
            "created_at": getattr(result, "created_at", None),
        },
        timestamp=utc_now_iso(),
    )
    _write_record(run_dir=run_dir, record=record, prompt=prompt)
    if not success:
        raise AgentBackendError(f"Cursor agent run did not finish successfully (status={status}).")
    return record


def _write_record(run_dir: Path, record: AgentExecutionRecord, prompt: str) -> None:
    payload = {
        "backend": record.backend,
        "success": record.success,
        "status": record.status,
        "summary": record.summary,
        "raw_result": record.raw_result,
        "timestamp": record.timestamp,
        "prompt": prompt,
    }
    (run_dir / "agent_backend_record.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_prompt(*, group: ResearchGroup, intent_packet: IntentPacket, run_id: str) -> str:
    return (
        f"You are the phase-1 research agent for group '{group.id}'.\n"
        f"Run ID: {run_id}\n"
        f"Objective: {group.objective}\n"
        f"Policy mode: {group.policy_mode}\n"
        f"Current hypothesis id: {intent_packet.active_hypothesis_id}\n"
        f"Current hypothesis text: {intent_packet.hypothesis_text}\n\n"
        "Required file changes:\n"
        "1) Update mnist/pipeline/research_hypotheses.py by prepending exactly one new hypothesis entry\n"
        "   with keys: hypothesis_id, theme, hypothesis, planned_change, run_id, timestamp.\n"
        "2) Update mnist/pipeline/research_markers.py by prepending exactly one marker string.\n"
        "3) Keep edits minimal and syntactically valid Python.\n\n"
        "Constraints:\n"
        "- Do not edit files outside the allowed research marker/hypothesis files.\n"
        "- Do not delete previous entries.\n"
        "- Write evidence-backed, concrete hypothesis text.\n"
        "- At the end, output a short JSON summary with keys: hypothesis_id, theme, changed_files.\n"
    )

