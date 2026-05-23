from __future__ import annotations

import argparse
import json
from pathlib import Path

from .plan import PlanDefinition
from .task import TaskDefinition


def export_schemas(*, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    exported: dict[str, Path] = {}
    definitions = {
        "task_definition.schema.json": TaskDefinition.model_json_schema(),
        "plan_definition.schema.json": PlanDefinition.model_json_schema(),
    }
    for filename, payload in definitions.items():
        path = out_dir / filename
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        exported[filename] = path
    return exported


def main() -> None:
    parser = argparse.ArgumentParser(description="Export HiAgentControl JSON schemas from Pydantic models.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "json",
        help="Directory where schema files should be written.",
    )
    args = parser.parse_args()
    exported = export_schemas(out_dir=args.out_dir)
    for name, path in exported.items():
        print(f"[schema] {name}: {path}")


if __name__ == "__main__":
    main()

