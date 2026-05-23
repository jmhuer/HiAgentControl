from __future__ import annotations

import re
import subprocess
from pathlib import Path

from hiagentcontrol.schemas import PlanDefinition, ScriptCheck

from .base import CheckResult


def run_script_check(*, workdir: Path, check: ScriptCheck) -> CheckResult:
    cmd = [check.path] + check.args
    effective_cwd = Path(check.cwd).resolve() if check.cwd else workdir.resolve()
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(effective_cwd),
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
    except FileNotFoundError:
        return CheckResult(
            name=check.name,
            passed=False,
            detail=f"Missing executable for check path: {check.path}",
            target_ref=check.path,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name=check.name,
            passed=False,
            detail=f"Timed out while running {check.path}",
            target_ref=check.path,
        )

    passed = completed.returncode == 0
    stdio = "\n".join(
        [part for part in [completed.stdout.strip(), completed.stderr.strip()] if part]
    ).strip()
    detail = stdio if stdio else f"Exit code: {completed.returncode}"
    return CheckResult(name=check.name, passed=passed, detail=detail, target_ref=check.path)


def sanitize_plan_json_text(text: str) -> str:
    """Fix common agent JSON mistakes before schema validation."""
    return text.replace("\\'", "'")


SCOPE_MARKERS = ("TRY:", "FILES:", "CHANGE:", "VERIFY:")
MIN_SCOPE_CHARS = 120
_SCOPE_REPO_PY_PATH = re.compile(r"\b(?:pipeline|eval)/[a-zA-Z0-9_./-]+\.py\b")
_SCOPE_BARE_PY_PATH = re.compile(r"\b[a-zA-Z0-9_-]+\.py\b")
_FORBIDDEN_CHANGE_PATHS = frozenset({"mnist_cnn.py"})


def _scope_segment(scope: str, start_label: str, end_label: str) -> str:
    if start_label not in scope or end_label not in scope:
        return ""
    start = scope.index(start_label) + len(start_label)
    end = scope.index(end_label, start)
    return scope[start:end]


def _py_paths_in_segment(segment: str) -> set[str]:
    repo_paths = set(_SCOPE_REPO_PY_PATH.findall(segment))
    bare_paths = set(_SCOPE_BARE_PY_PATH.findall(segment))
    for qualified in repo_paths:
        bare_paths.discard(qualified.rsplit("/", 1)[-1])
    return repo_paths | bare_paths


def _scope_path_issues(scope: str) -> list[str]:
    """CHANGE .py paths must match FILES; known phantom paths are rejected."""
    files_seg = _scope_segment(scope, "FILES:", "CHANGE:")
    change_seg = _scope_segment(scope, "CHANGE:", "VERIFY:")
    if not files_seg or not change_seg:
        return []
    files_paths = _py_paths_in_segment(files_seg)
    change_paths = _py_paths_in_segment(change_seg)
    issues: list[str] = []
    for path in change_paths:
        if path in _FORBIDDEN_CHANGE_PATHS:
            issues.append(
                f"CHANGE references {path} (no such file; model code is pipeline/model.py, class MnistCNN)"
            )
        elif files_paths and path not in files_paths:
            issues.append(
                f"CHANGE cites {path} but FILES only lists {', '.join(sorted(files_paths))}"
            )
    return issues


def validate_plan_task_scopes(*, plan_json_path: Path) -> CheckResult:
    if not plan_json_path.exists():
        return CheckResult(
            name="plan-task-scope",
            passed=False,
            detail=f"Deliverable not found: {plan_json_path}",
            target_ref=str(plan_json_path),
        )
    try:
        plan = PlanDefinition.model_validate_json(
            sanitize_plan_json_text(plan_json_path.read_text(encoding="utf-8"))
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            name="plan-task-scope",
            passed=False,
            detail=f"Cannot validate scopes: {exc}",
            target_ref=str(plan_json_path),
        )

    bad: list[str] = []
    for idx, task in enumerate(plan.tasks):
        scope = task.scope.strip()
        missing = [m for m in SCOPE_MARKERS if m not in scope]
        if missing or len(scope) < MIN_SCOPE_CHARS:
            bad.append(
                f"tasks[{idx}] ({task.task[:40]}…): "
                f"missing {missing or 'length'} (need TRY/FILES/CHANGE/VERIFY, ≥{MIN_SCOPE_CHARS} chars)"
            )
            continue
        for issue in _scope_path_issues(scope):
            bad.append(f"tasks[{idx}] ({task.task[:40]}…): {issue}")

    passed = not bad
    return CheckResult(
        name="plan-task-scope",
        passed=passed,
        detail=(
            "All task scopes include TRY/FILES/CHANGE/VERIFY with consistent paths."
            if passed
            else "Invalid task scopes: " + "; ".join(bad[:3])
            + (" …" if len(bad) > 3 else "")
        ),
        target_ref=f"{plan_json_path}#tasks/*/scope",
    )


def validate_plan_task_count(
    *, plan_json_path: Path, min_tasks: int, exact_tasks: int | None = None
) -> CheckResult:
    if not plan_json_path.exists():
        return CheckResult(
            name="plan-task-count",
            passed=False,
            detail=f"Deliverable not found: {plan_json_path}",
            target_ref=str(plan_json_path),
        )
    try:
        plan = PlanDefinition.model_validate_json(
            sanitize_plan_json_text(plan_json_path.read_text(encoding="utf-8"))
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            name="plan-task-count",
            passed=False,
            detail=f"Cannot count tasks: {exc}",
            target_ref=str(plan_json_path),
        )
    count = len(plan.tasks)
    if exact_tasks is not None:
        passed = count == exact_tasks
        detail = (
            f"Task count exact match: {count} tasks (required exactly {exact_tasks})."
            if passed
            else (
                f"Task count mismatch: plan.json has {count} tasks, "
                f"required exactly {exact_tasks}."
            )
        )
    else:
        passed = count >= min_tasks
        detail = (
            f"Task requirement met: {count} tasks (required {min_tasks})."
            if passed
            else (
                f"Lack of task requirements: plan.json has {count} tasks, "
                f"required {min_tasks}."
            )
        )
    return CheckResult(
        name="plan-task-count",
        passed=passed,
        detail=detail,
        target_ref=f"{plan_json_path}#tasks",
    )


def validate_plan_json(*, plan_json_path: Path) -> list[CheckResult]:
    """Return separate exists + schema checks for the deliverable path."""
    if not plan_json_path.exists():
        return [
            CheckResult(
                name="plan-json-exists",
                passed=False,
                detail=f"Deliverable not found: {plan_json_path}",
                target_ref=str(plan_json_path),
            ),
            CheckResult(
                name="plan-json-schema",
                passed=False,
                detail="Skipped schema validation because deliverable file is missing.",
                target_ref=str(plan_json_path),
            ),
        ]
    try:
        payload = sanitize_plan_json_text(plan_json_path.read_text(encoding="utf-8"))
        PlanDefinition.model_validate_json(payload)
    except Exception as exc:  # noqa: BLE001
        return [
            CheckResult(
                name="plan-json-exists",
                passed=True,
                detail=f"Deliverable found: {plan_json_path}",
                target_ref=str(plan_json_path),
            ),
            CheckResult(
                name="plan-json-schema",
                passed=False,
                detail=f"Schema validation failed: {exc}",
                target_ref=f"{plan_json_path}#root",
            ),
        ]
    return [
        CheckResult(
            name="plan-json-exists",
            passed=True,
            detail=f"Deliverable found: {plan_json_path}",
            target_ref=str(plan_json_path),
        ),
        CheckResult(
            name="plan-json-schema",
            passed=True,
            detail="PlanDefinition schema validation passed.",
            target_ref=f"{plan_json_path}#root",
        ),
    ]
