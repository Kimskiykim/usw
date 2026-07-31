## Why

`usw-route-task` combines discovery, authoring, approval and execution while
remaining explicitly invoked, so it adds ceremony without removing a user
decision. USW needs only a small read-only capability for users who know their
intent but not the name of an existing flow.

## What Changes

- **BREAKING** Replace `usw-route-task` with `usw-find-flow`.
- Search only runnable developer-local and shared flows for an explicit intent.
- Return the best match and a ready-to-copy `usw-run-flow` command, or
  `no-match`.
- Never create, adapt or execute a flow and never touch HANDOFF.

## Capabilities

### New Capabilities

- `flow-discovery`: Read-only intent-based discovery of existing runnable
  Markdown flows.

### Modified Capabilities

None.

## Impact

The packaged skill, command metadata, plugin description, installer lists,
README and focused package tests replace the old router name and contract. No
runtime, configuration or dependency is added.
