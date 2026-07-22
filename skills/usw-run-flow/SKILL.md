---
name: usw-run-flow
description: Run one validated shared role-flow action or one boundary of a shared or developer-local Markdown custom flow version 1 or version-2 with observable HANDOFF begin/outcome boundaries.
---

# Run a USW flow

Treat `--local` and `-l` as exact aliases. With either selector, accept only a
named custom flow and use exactly `<project>/.usw/flows`; reject local
`analysis`, `development`, and `testing`. Without a selector, read `usw.yaml`
and resolve `flows.root`; when configuration is absent, use the documented
standalone default `usw/flows`. Load only the explicitly selected root, never
search the other root, and never use a packaged template as a runtime fallback.

Validate the selected document with `scripts/run_flow.py` before mutation. For
custom version `1`, use the linear rules below. For `version-2`, after the
validator selects that exact version, read
[references/version-2.md](references/version-2.md) completely and follow it.
Do not load the v2 reference for role scenarios or version `1`.

## Preflight

Before any mutation:

1. Resolve exactly one scope and exactly one next action or orchestration
   boundary. If several are valid, stop for a user decision.
2. Resolve every executor required by the whole custom flow by exact type and
   target. For `PARALLEL`, resolve all children; for `CALL SUBAGENT`, also
   validate its complete nested payload. Missing capability or contract
   mismatch stops the flow before any invocation.
3. Read `.usw/HANDOFF.md`. A non-idle state permits only the same flow origin,
   identity, scope, action name and control cursor. If legacy `.usw/FLOW.json`
   exists, stop for manual recovery; never merge or delete it.
4. Ask `usw-manage-handoff` to perform Begin. It must write `in_progress` and
   read it back successfully. Without a confirmed Begin, do not invoke an
   executor.

## One boundary

Invoke exactly one selected version-1 step or version-2 top-level boundary.
`CALL SUBAGENT`, `CALL FLOW` and a complete `PARALLEL` block are each one parent
boundary even though their executor owns nested work. Require a structured
outcome with status, outcome, written artifact roles, output references, actual
changed areas, verification references, and any blocker, decision or permission
boundary.

Compare reported writes with executor declarations. Then ask
`usw-manage-handoff` to record Outcome before selecting another action:

- `completed`: append one compact journal row and advance the applicable cursor;
- `failed`, `blocked`, `decision_required`, or permission boundary: keep the
  cursor on the same boundary and stop;
- contract violation: record `failed` and stop.

Return control after this boundary. Never launch the following top-level action
in the same invocation.

## Resume

Read only the HANDOFF summary first. Resume only the same flow origin, identity,
scope, action name and v2 loop counters. `in_progress` without result is a
possible interruption inside executor: inspect current state as needed and
never retry mutation automatically. A stale or unknown source requires explicit
reconciliation.

## Standard role flow

Preserve the existing Analysis, Development, Testing, review, and Delivery
branches. Human review executors create their own receipts. At Delivery report
scope, tested source identity, current evidence, observations, and delivery
owner. Commit, push, PR, deploy, and release always require separate permission.

## Custom flow version 1

Version `1` contains `Контракт` and `Порядок действий`, with consecutive linear
skill or safe project-local script steps. It may use the concise form or the
legacy complete `Пишет` plus `Полномочия записи` form. Arguments are separate
literal values with no shell semantics. Execute one numbered step, take the
skill write contract from its executor for concise flows, and preserve all
legacy write checks. Branches and loops remain invalid in version `1`.

Validate a local flow with `python3 <validator> validate --local <project-root>
<name>`; `-l` has the same meaning. Persist `shared` or `local` in flow identity.

## Custom flow version-2

Use the v2 reference only after exact version selection. It defines permanent
action names, typed calls, composite payload, gates, bounded loops, parallel
execution, cursor transitions and typed executor adapters. Prose outside the
canonical executable positions remains documentation and never authorizes an
inferred transition.
