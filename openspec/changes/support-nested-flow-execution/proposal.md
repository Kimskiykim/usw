## Why

USW stores all local recovery state in one project-wide `.usw/HANDOFF.md`, so
one recoverable operation blocks both independent top-level flows in different
chats and named child flows inside a root execution. Operation identities are
already unique per invocation, so recovery can be routed by that identity
without treating the whole project as one long-lived operation slot.

## What Changes

- Turn `.usw/HANDOFF.md` into a local router from operation identity to a
  separate `.usw/handoffs/<operation-id>.md` state document.
- Allow independent top-level flow invocations to own concurrent durable
  operations while serializing only their short router and state transitions.
- Address Outcome, Save, Resume and Finish to an exact operation identity;
  preserve exact-input validation and stale-writer rejection within each
  operation.
- Keep terminal operations inspectable until their own explicit Finish instead
  of letting an unrelated Begin replace them.
- Add an explicit nested-flow execution context owned by the active root
  invocation and bound to its operation identity when handoff is enabled.
- Let independent subagents resolve and execute named nested flows in parallel
  without creating their own Begin or Outcome.
- Keep each root executor as the only writer of its operation state and require
  it to aggregate its nested results into that operation's Outcome.
- Require nested execution to match the exact active parent operation identity
  when handoff is enabled; do not expose a general handoff-bypass mode.
- Define failure, pause, blocker and decision propagation from nested flows to
  the root executor without adding a parser, machine cursor or durable
  per-branch state.
- Preserve the `handoff: false` boundary, migrate existing generic single-state
  HANDOFF content and keep legacy state recovery-only until explicit Finish.
- **BREAKING local state format**: router-aware USW versions replace generic
  single-state HANDOFF with a routed layout that older versions cannot read.

## Capabilities

### New Capabilities

- `nested-flow-execution`: Resolve and execute named flows as child work inside
  one active root operation, including independent parallel branches and result
  propagation to the root executor.

### Modified Capabilities

- `text-flow-execution`: Distinguish root execution from authorized nested
  execution while preserving immutable Markdown invocations and normal
  permission boundaries.
- `live-operation-state`: Replace the single project-wide operation with a
  router and independently addressed operation states while preserving
  serialized transitions and stale-writer protection.
- `project-initialization`: Initialize the routed handoff layout when the
  capability is enabled while preserving the disabled and create-only
  boundaries.

## Impact

The change affects `usw-run-flow`, `usw-manage-handoff`, project initialization,
README documentation and their contract tests. It introduces no new
dependency, machine DSL, automatic retry or product-file locking. Concurrent
operations remain a user-declared coordination choice and USW does not detect
or serialize overlapping product-file writes. Rollback to a single-state USW
version requires finishing routed operations and restoring generic idle state.
