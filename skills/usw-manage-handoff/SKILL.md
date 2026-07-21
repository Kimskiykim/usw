---
name: usw-manage-handoff
description: Save, finish, inspect, or resume developer-local work through .usw/HANDOFF.md without a separate runtime state.
---

# Manage USW Handoff

Treat `.usw/HANDOFF.md` as mutable developer-local state, never as a shared
project artifact or historical audit log. This capability writes only
`local-checkpoint`; it never chooses or invokes the next executor.
Return point: immediately after one confirmed begin, outcome, save, resume, or
finish operation; return control to `usw-run-flow`.

Find the nearest Git root. If `.usw/HANDOFF.md` is missing, stop and tell the
user to run `/usw-init`.

## Operation summary

Keep the existing section order and metadata header. Use metadata as follows:

- `Subject`: exact task/change scope;
- `Role`: Analysis, Development, or Testing;
- `Attempt`: current flow name and step, for example `dev-test:1/2`;
- `Current operation`: task-local `op-NNN`;
- `Status`: `in_progress`, `completed`, `failed`, `blocked`,
  `decision_required`, or `paused`;
- `Updated`: ISO 8601 timestamp with timezone.

The first `Session journal` row is the current operation. One completed row per
flow step is enough; do not log tool calls, reads, or separate begin/end events.

```markdown
| Operation | Actor | Executor | Flow cursor | Intent | Declared writes | Status | Result | Actual areas | Started |
|---|---|---|---|---|---|---|---|---|---|
| op-001 | codex | skill:openspec-apply-change | dev-test:1/2 | Implement the selected change. | implementation, implementation-tests, task-index | in_progress | none | none | 2026-07-21T18:00:00+03:00 |
```

Use `Verification`, `Next action`, `References`, and `Trusted source snapshot`
for compact facts only. Refer to specifications and evidence by path; never copy
their contents into HANDOFF.

## Begin

Begin is available only to an already validated flow orchestrator.

1. Read the current HANDOFF. `idle` permits a new operation. Any non-idle state
   permits only the same flow/scope; otherwise stop and offer resume or
   `/usw-handoff finish`.
2. If `.usw/FLOW.json` exists, stop. Do not merge, overwrite, or delete it.
3. Choose the next `op-NNN`, preserve completed rows, and write `in_progress`
   with actor, exact executor, flow cursor, one-line intent, declared writes,
   started timestamp, `Result: none`, and `Actual areas: none`.
4. Read `.usw/HANDOFF.md` back. Confirm every required value is present and
   matches the planned executor. On any mismatch or write failure, return a
   `local-state-boundary`; the executor must not run.
5. Return the HANDOFF reference to `usw-run-flow` immediately.

## Outcome

1. Compare reported writes with declared writes and the flow authority.
2. Update the current row with status, one-line result, actual changed areas,
   verification references, updated timestamp, and cursor. Advance the cursor
   only for `completed`.
3. Read the file back and confirm the outcome. On failure, leave the operation
   treated as possibly `in_progress` and stop before another executor.
4. Return the HANDOFF reference and next action to `usw-run-flow`.

## Save

For an explicit `/usw-handoff`, inspect current work and write only factual
state. Record checks actually run; otherwise use `not-run`. Preserve the current
operation journal rather than creating a second history.

## Resume

1. Read HANDOFF only; do not open references yet.
2. If state is `idle`, report that no work is available and stop.
3. Summarize scope, actor, executor, intent, status, verification, and next action.
4. `in_progress` with no result means the executor may have been interrupted.
   Never retry automatically. Inspect current source and references only as
   needed, then require an explicit scoped decision before mutation.
5. A different flow/scope remains blocked until resume of the saved work or
   `/usw-handoff finish`.

## Finish

Only an explicit finish/clear request may replace HANDOFF with the initialized
idle template. Do not archive the journal and do not touch product files.
