## Why

USW can author and run named flows, but the user must already know which
operation to invoke. A one-task opt-in router provides a safe step toward the
north star where an agent recognizes that a task needs a workflow, reuses an
available flow when possible, or authors one before execution.

## What Changes

- Add `$usw-route-task "<task>"` as an explicitly invoked, one-task routing
  workflow.
- Classify simple tasks as direct-execution recommendations without performing
  work or writing state.
- Search developer-local, configured shared and packaged example flows without
  external discovery.
- Preview an exact match or a proposed new/adapted flow and require human
  approval before saving or executing it.
- Reuse `usw-create-flow` and `usw-run-flow` after approval, preserving their
  path, handoff and permission boundaries.
- Keep persistent or implicitly activated routing out of scope.

## Capabilities

### New Capabilities

- `task-flow-routing`: Opt-in task assessment, bounded flow discovery,
  preview/approval and delegation to existing authoring and execution
  capabilities.

### Modified Capabilities

None.

## Impact

The change adds one instruction-only skill and its Codex metadata, then updates
the installer, package manifests, README and contract tests. It adds no
configuration field, parser, execution runtime, external dependency or machine
checkpoint.
