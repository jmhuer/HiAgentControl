from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def default_ohmy_bin() -> str:
    """
    Resolve the oh-my-openagent CLI (headless OpenCode + plugin launcher).

    Order: HAC_OHMY_BIN → oh-my-openagent on PATH → oh-my-opencode on PATH
    → bunx oh-my-openagent@latest (single fallback).
    """
    override = os.getenv("HAC_OHMY_BIN")
    if override:
        return override

    for name in ("oh-my-openagent", "oh-my-opencode"):
        found = shutil.which(name)
        if found:
            return found

    return "bunx oh-my-openagent@latest"


@dataclass(frozen=True)
class OhMyRunResult:
    returncode: int
    stdout: str
    session_id: str
    success: bool
    summary: str


class OhMyBackend:
    """
    Thin wrapper around `oh-my-openagent run` (or `oh-my-opencode run`).

    OMO waits until todos and background child sessions are idle before exiting.
    Python only invokes and checks deliverables on disk.
    """

    def __init__(
        self,
        *,
        root: Path,
        binary_path: str | None = None,
        base_port: int = 4205,
        timeout_sec: int = 1800,
        on_complete: str | None = None,
    ) -> None:
        self.root = root.resolve()
        self.binary_path = binary_path or default_ohmy_bin()
        self.base_port = base_port
        self.timeout_sec = timeout_sec
        self.on_complete = on_complete

    def run(
        self,
        *,
        workdir: Path,
        prompt: str,
        port_offset: int = 0,
        agent: str | None = None,
        on_complete: str | None = None,
    ) -> OhMyRunResult:
        selected_port = _pick_available_port(self.base_port + port_offset)
        binary = self.binary_path
        use_bunx = binary.startswith("bunx ")

        cmd: list[str]
        if use_bunx:
            cmd = binary.split() + [
                "run",
                "--directory",
                str(workdir.resolve()),
                "--port",
                str(selected_port),
                "--json",
            ]
        else:
            cmd = [
                binary,
                "run",
                "--directory",
                str(workdir.resolve()),
                "--port",
                str(selected_port),
                "--json",
            ]

        hook = on_complete or self.on_complete
        if hook:
            cmd.extend(["--on-complete", hook])

        if agent:
            cmd.extend(["--agent", agent])
        cmd.append(prompt)

        log_path = workdir / f"state/current/omo_run_{selected_port}.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        agent_label = f"  agent={agent}" if agent else ""
        _log(
            f"oh-my-openagent run  port={selected_port}  workdir={workdir.name}  "
            f"timeout={self.timeout_sec}s{agent_label}"
        )
        _log(f"  binary: {binary}")
        _log(f"  live log: tail -f {log_path}")
        _log(f"  prompt[:120]: {prompt[:120].replace(chr(10), ' ')}")

        stdout_lines: list[str] = []

        def _stream(proc: subprocess.Popen) -> None:
            assert proc.stdout is not None
            with open(log_path, "w", encoding="utf-8") as fh:
                for line in proc.stdout:
                    fh.write(line)
                    fh.flush()
                    stdout_lines.append(line)

        proc: subprocess.Popen | None = None
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(workdir.resolve()),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
            )
            reader = threading.Thread(target=_stream, args=(proc,), daemon=True)
            reader.start()
            proc.wait(timeout=self.timeout_sec)
            reader.join(timeout=10)
        except subprocess.TimeoutExpired:
            _log(f"  [TIMEOUT] oh-my-openagent did not finish within {self.timeout_sec}s — killing")
            if proc is not None:
                proc.kill()
                reader.join(timeout=5)
            raise

        assert proc is not None
        stdout_text = "".join(stdout_lines)
        _log(f"  oh-my-openagent done  rc={proc.returncode}  lines={len(stdout_lines)}")
        parsed = _parse_run_output(stdout_text)
        return OhMyRunResult(
            returncode=proc.returncode,
            stdout=stdout_text,
            session_id=str(parsed.get("sessionId", "")),
            success=bool(parsed.get("success", proc.returncode == 0)),
            summary=str(parsed.get("summary", "")),
        )


def _parse_run_output(stdout: str) -> dict[str, Any]:
    """Parse `--json` result or opencode NDJSON event stream."""
    stripped = stdout.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            payload = json.loads(stripped)
            if isinstance(payload, dict):
                return {
                    "success": payload.get("success", True),
                    "summary": payload.get("summary", payload.get("message", "")),
                    "sessionId": payload.get("sessionId", payload.get("sessionID", "")),
                }
        except json.JSONDecodeError:
            pass

    session_id = ""
    text_parts: list[str] = []
    had_error = False
    error_msg = ""

    for line in stdout.splitlines():
        line = line.strip()
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue

        etype = event.get("type", "")
        session_id = session_id or str(event.get("sessionID", event.get("sessionId", "")))

        if etype == "text":
            part = event.get("part", {})
            chunk = part.get("text", "") if isinstance(part, dict) else ""
            if chunk:
                text_parts.append(str(chunk))
        elif etype == "error":
            had_error = True
            err = event.get("error", {})
            if isinstance(err, dict):
                error_msg = str(err.get("data", {}).get("message", "") or err.get("message", ""))

    summary = " ".join(text_parts).strip()
    return {
        "success": not had_error and bool(summary or session_id),
        "summary": summary if not had_error else error_msg,
        "sessionId": session_id,
    }


def _pick_available_port(start_port: int, max_tries: int = 50) -> int:
    port = start_port
    for _ in range(max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port
