## Why

Routed handoffs make concurrent operations independently recoverable, but the
current operation document is difficult to identify in a multi-operation list
and does not retain enough time or worktree context for a safe later resume.
The router should remain minimal while each operation regains a compact,
factual recovery snapshot.

## What Changes

- Add a one-line human-readable summary and immutable start timestamp to every
  newly created operation document.
- Add a compact workspace section that records the operation's expected writes
  and the worktree changes observed at the latest confirmed outcome/save.
- Show the summary and update time when several registered operations require a
  user selection.
- Read existing routed operation documents without these additions and upgrade
  them only during an explicit mutation, without inventing prior workspace
  facts.
- Keep `HANDOFF.md` as an operation-ID router and keep handoff free of a session
  journal or retained audit history.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `live-operation-state`: operation recovery state gains human identification,
  start time, bounded workspace context and backwards-compatible enrichment.

## Impact

The change affects the handoff parser/renderer and CLI in
`skills/usw-manage-handoff/scripts/handoff_state.py`, the handoff and flow skill
contracts, and focused handoff/end-to-end tests. It adds no dependency and does
not change router paths, operation identity, locking, or finish semantics.
