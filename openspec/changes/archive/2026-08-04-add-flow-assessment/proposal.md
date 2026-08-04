## Why

USW can create and execute text-first Markdown flows, but it has no explicit
read-only way to assess whether a flow has a coherent executable path. Logical
gaps, missing dependencies and unbounded cycles are therefore discovered only
during execution.

## What Changes

- Add an explicitly invoked `usw-assess-flow` capability for semantic,
  evidence-backed assessment of one safely resolved local or shared flow.
- Report one of four verdicts together with terminal-path, dependency and
  finding details, plus an optional trace for a supplied scenario input.
- Add a read-only `inspect` loader command that exposes exact immutable flow
  content without preparing an execution invocation.
- Treat a proven contract-invalid mandatory invocation without handled fallback
  as a blocking reachable dead end.
- Treat an irreversible action inside a repeat loop as unsafe unless it is
  idempotent; one approval before the loop is not sufficient protection.
- Keep semantic acceptance fixtures and raw reports in the change so observed
  verdicts remain independently inspectable.
- Package and document the new skill and command for all supported agents.
- Keep assessment outside `usw-create-flow` and `usw-run-flow`; it never
  executes a flow, changes HANDOFF state or introduces a machine DSL.

## Capabilities

### New Capabilities

- `flow-assessment`: Defines safe flow selection, semantic executability and
  loop analysis, dependency reporting, verdicts and read-only behavior.

### Modified Capabilities

None.

## Impact

- Adds `skills/usw-assess-flow` and `commands/usw-assess-flow.md`.
- Extends the text-flow loader CLI with a backward-compatible `inspect`
  subcommand while retaining the existing `resolve` contract.
- Updates installer/package surfaces, user documentation and their regression
  tests. No new runtime dependency or persisted state is introduced.
- Adds checked-in semantic smoke fixtures and reports under the change's
  acceptance evidence.
