ULW state bridge contract:

- OMO `ulw-loop` owns loop continuation semantics.
- Python owns persistence/readback of loop artifacts and restart orchestration.
- Python writes/updates:
  - `state/current/loop_state.json`
  - `state/current/evaluator_report.json`
  - `state/current/targeted_rework.md`
- On restart, Python passes a compact re-entry prompt pointing to those files.
- Prometheus consumes state and delegates targeted fixes.

