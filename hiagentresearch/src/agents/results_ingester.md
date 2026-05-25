# Results Ingester Skeleton

## Inputs

- canonical artifacts (`metrics.json`, `failure_class.json`, `run_meta.json`)
- group id and branch id

## Outputs

- registry run row
- metric rows
- append-only event log entry

## Rules

- Reject ingestion if required artifacts are missing.
- Never auto-convert missing artifacts into success.
