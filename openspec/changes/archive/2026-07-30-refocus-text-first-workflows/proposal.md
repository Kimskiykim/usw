## Why

USW currently maintains both a model-executed Markdown path and an experimental
machine runtime with parsing, typed executors, control state and JSON
checkpoints. The machine path adds substantial product and specification
complexity before its deterministic guarantees are needed, while ordinary
Markdown already provides the useful authoring and execution experience.

## What Changes

- Make every named flow an opaque Markdown document executed by the model with
  the exact user input through one text-first path.
- Keep `version-2` and `CALL`, `GATE`, `LOOP` and `PARALLEL` as readable
  authoring conventions without parser, cursor, atomic-parallel or deterministic
  transition guarantees.
- **BREAKING** Remove `--experimental-structured` and the production
  `validate`, `run-script`, `checkpoint-save` and `checkpoint-resume` behavior;
  legacy invocations return migration guidance.
- Reduce the production runner to safe local/shared resolution, one-time byte
  loading, identity calculation and an immutable model-invocation envelope.
- Add top-level `handoff: true|false` configuration with backwards-compatible
  default `true`, a generic Markdown handoff format and an explicit state
  transition matrix.
- Stop using `.usw/FLOW.json`. Leave an existing file untouched and warn at
  most once per flow invocation.
- Preserve the removed runtime, its transitive support files, specialized tests
  and the two superseded active changes under `research/structured-runtime/`.
  Production code and packaging must not depend on that snapshot.
- Remove normative role-lifecycle, strict-flow and machine-state guarantees
  from the main specifications and documentation.
- Add a non-normative roadmap from text flow to a possible future compiler,
  machine flow and iterator without fixing their APIs.

## Capabilities

### New Capabilities

- `text-flow-execution`: Safe opaque Markdown loading, immutable model
  invocation, text interpretation, stop conditions and legacy runtime guidance.

### Modified Capabilities

- `workspace-configuration`: Add the optional boolean `handoff` setting.
- `project-initialization`: Create or skip generic handoff state according to
  configuration.
- `local-custom-flows`: Run local and shared Markdown through the same path.
- `markdown-flow-composition`: Recast structured markers as non-machine
  authoring conventions.
- `flow-authoring-assistance`: Remove strict validation from structured
  authoring.
- `flow-examples`: Remove mandatory role lifecycle and machine-runtime claims.
- `live-operation-state`: Replace role/cursor state with optional generic
  handoff state.
- `execution-artifacts`: Remove mandatory roles, write authority and evidence
  fields from handoff.
- `intent-clarification`: Remove the remaining validated Analysis runner
  routing requirement while keeping clarification and solution evaluation
  separate capabilities.
- `flow-orchestration`: Remove the mandatory
  `Analysis → Development → Testing` lifecycle.
- `structured-flow-runtime`: Retire the production parser and machine runtime.
- `validated-composite-flows`: Retire strict validation, typed execution and
  JSON checkpoint requirements.

## Impact

The change affects `usw-run-flow`, `usw-create-flow`,
`usw-manage-handoff`, `usw-initialize-project`, their Python helpers, README,
plugin metadata, package contracts and tests. Existing Markdown flow files need
no migration. Existing `.usw/FLOW.json` and role-based `HANDOFF.md` files are
preserved. The current full production baseline is 160 passing tests; removed
runtime tests move to an explicit research-only suite.
