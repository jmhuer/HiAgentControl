# Group Runner Skeleton

## Inputs

- planner output
- group charter
- allowed file paths

## Required action log entries

- `start_cycle`
- `code_inspection`
- `change_proposal`
- `eval_triggered`
- `eval_completed`
- `intent_packet_updated`

## Rules

- Do not claim success without eval artifacts.
- Persist action trace for each step.
