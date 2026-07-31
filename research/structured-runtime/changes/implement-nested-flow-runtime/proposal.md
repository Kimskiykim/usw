## Why

Experimental structured flows already accept and document `CALL FLOW`, but the
runtime has no production executor for that call type, so a valid parent flow
stops with `missing_executor`. Nested execution also lacks a durable contract
for origin preservation, cycle safety, outcome propagation, and resume.

## What Changes

- Add a production `CALL FLOW` adapter for explicitly selected structured
  execution.
- Resolve every child from the parent flow's selected origin and root, validate
  the complete reachable flow graph before mutation, and reject unsafe paths,
  missing children, and direct or indirect cycles.
- Execute a child to a terminal outcome before completing the parent action,
  preserving task, scope, optional action input, write authority, results, and
  output references across the boundary.
- Persist enough nested execution state to resume the innermost unfinished
  child and then return deterministically through its parent frames.
- Store each structured run under
  `.usw/states/flows/<origin>/<flow-name>/<run-id>/flow.json`, so independent
  runs and equal local/shared names never overwrite one another.
- Keep the whole nested run inside the parent operation boundary and preserve
  existing permission gates for external or destructive actions.
- Add contract and end-to-end coverage for success, stop propagation,
  origin isolation, graph safety, authority checks, interruption, and resume.
- Keep ordinary Markdown execution unchanged; nested runtime semantics remain
  available only through the explicit structured experiment.

## Capabilities

### New Capabilities

- `nested-flow-runtime`: Safe, resumable execution of structured `CALL FLOW`
  actions within one parent operation.

### Modified Capabilities

None.

## Impact

The change affects the structured path of `usw-run-flow`, its Python
orchestrator and checkpoint schema, structured-flow references and skill
instructions, developer-local checkpoint layout, and flow-orchestrator tests.
It introduces no external runtime dependency and does not change plain
Markdown flow execution or flow files created by users.
