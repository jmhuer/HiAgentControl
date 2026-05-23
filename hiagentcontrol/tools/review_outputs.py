from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hiagentcontrol.gates.deterministic_checks import validate_plan_task_count
from hiagentcontrol.run_config import RunRequirements


@dataclass(frozen=True)
class OutputReview:
    plan_task_count: int
    task_requirement_met: bool
    task_detail: str


def review_plan_outputs(
    *,
    workdir: Path,
    requirements: RunRequirements,
) -> OutputReview:
    plan_path = workdir / "state/current/plan.json"
    check = validate_plan_task_count(
        plan_json_path=plan_path,
        min_tasks=requirements.num_tasks,
    )
    count = 0
    if plan_path.is_file() and check.passed:
        from hiagentcontrol.schemas import PlanDefinition

        count = len(
            PlanDefinition.model_validate_json(
                plan_path.read_text(encoding="utf-8")
            ).tasks
        )
    elif plan_path.is_file():
        try:
            from hiagentcontrol.schemas import PlanDefinition

            count = len(
                PlanDefinition.model_validate_json(
                    plan_path.read_text(encoding="utf-8")
                ).tasks
            )
        except Exception:
            count = 0

    return OutputReview(
        plan_task_count=count,
        task_requirement_met=check.passed,
        task_detail=check.detail,
    )


def format_review_report(review: OutputReview, *, requirements: RunRequirements) -> str:
    return (
        "Output review (deterministic gates only)\n"
        f"  plan_task_count:      {review.plan_task_count} "
        f"(required >= {requirements.num_tasks})\n"
        f"  task_requirement_met: {review.task_requirement_met}\n"
        f"  detail:               {review.task_detail}"
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Review plan.json task count vs requirement.")
    parser.add_argument("--workdir", default="mnist")
    parser.add_argument("--num-tasks", type=int, default=4)
    args = parser.parse_args()
    workdir = Path(args.workdir).resolve()
    req = RunRequirements(num_tasks=args.num_tasks)
    review = review_plan_outputs(workdir=workdir, requirements=req)
    print(format_review_report(review, requirements=req))
    if not review.task_requirement_met:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
