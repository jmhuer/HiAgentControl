from __future__ import annotations

from dataclasses import dataclass


SCOPE_TEMPLATE = (
    "TRY: <exact experiment — what to train/test> "
    "FILES: <repo paths to edit> "
    "CHANGE: <concrete code/params to apply> "
    "VERIFY: <eval command + metric threshold>"
)


@dataclass(frozen=True)
class RunRequirements:
    """Cardinality targets for a plan-only loop run."""

    num_tasks: int = 4

    def __post_init__(self) -> None:
        if self.num_tasks < 1:
            raise ValueError("num_tasks must be >= 1")

    def prompt_block(self) -> str:
        return (
            "## Run requirements\n"
            f"- Produce **≥ {self.num_tasks}** distinct improvement tasks in `plan.json` `tasks`.\n"
            f"- Each task **`scope`** MUST use this exact labeled format (single string):\n"
            f"  `{SCOPE_TEMPLATE}`\n"
            "- **TRY** = the one specific thing to attempt (not vague goals).\n"
            "- **FILES** = exact paths under `pipeline/` or `eval/` (model code: `pipeline/model.py`, not `mnist_cnn.py`).\n"
            "- **CHANGE** = precise edits; every `.py` in CHANGE must be listed in FILES.\n"
            "- **VERIFY** = `python eval/run_eval.py --quick` plus accuracy/latency threshold.\n"
            "- Draft candidate-task subsections must mirror the same TRY/FILES/CHANGE detail (from Atlas research, not Prometheus guesses).\n"
            "- Prometheus plan steps = **where to look** delegations; Atlas draft = **what was found**.\n"
        )
