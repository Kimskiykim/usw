## Context

The refocused USW runtime has two intentionally separate capabilities:
`usw-create-flow` writes one human-readable Markdown flow and returns without
execution, while `usw-run-flow` safely resolves and executes one existing named
flow. Neither capability decides whether a task needs a flow or selects one.

The router must preserve that separation, remain explicitly invoked for one
task, and work in Codex, Qwen Code and Gigacode without introducing another
runtime or configuration surface.

## Goals / Non-Goals

**Goals:**

- Assess one supplied task and distinguish direct work from work that benefits
  from a flow.
- Reuse exact matches and derive new named flows from partial matches.
- Require a visible human approval boundary before any flow write or execution.
- Reuse existing authoring, resolver, handoff and permission contracts.

**Non-Goals:**

- Implicit or persistent routing for every task.
- Deterministic semantic matching, scoring, parsing or machine checkpoints.
- External flow search or a cross-project user library.
- Automatic improvement, deletion or replacement of existing flows.

## Decisions

### One explicit instruction-only router

Add `usw-route-task` with implicit invocation disabled. The skill accepts the
original task, performs routing in prose and returns at either the direct-work
recommendation or preview boundary. This is preferred to a configuration flag
or hook because the first release is intentionally opt-in for one task.

### Model-driven discovery over existing safe primitives

The router enumerates direct Markdown entries in developer-local
`.usw/flows`, configured `flows.root`, and the packaged examples directory
without following symlinks. It uses the existing safe resolver to load
local/shared candidates and reads examples only from their known packaged
location. The model compares task intent with candidate content; no index,
embedding store, scoring schema or discovery script is added.

Packaged examples are authoring references. Selecting one always produces a
new saved flow; examples never become a runtime fallback.

### Preview is the only pre-execution state

For an exact match, the preview contains the selected name, origin, path, full
Markdown and selection rationale. For a partial or absent match, it contains
the proposed name, selected local/shared destination, full Markdown, rationale
and the source/differences when adapting an existing flow.

The router does not write a draft or begin HANDOFF while awaiting approval.
Cancellation therefore has no cleanup path. If conversational context is lost,
the user reruns the router.

### Existing capabilities own mutation and execution

After approval, exact matches delegate directly to `usw-run-flow` with an
explicit origin selector. New or adapted flows first delegate to
`usw-create-flow`, then return to the router, which delegates the saved name to
`usw-run-flow` in the same continuation. The source flow remains unchanged.

Project-specific and team-relevant flows use configured shared storage.
Personal, experimental or ambiguous flows use developer-local storage. The
preview exposes this decision so approval covers both content and destination.

### No authority inheritance

Approval authorizes only the displayed save, when needed, and execution of the
displayed flow against the original task. Commit, push, pull request, deploy,
release, destructive and other external actions keep their normal permission
boundaries.

## Risks / Trade-offs

- [Semantic selection varies between models] → Show the complete selected or
  proposed flow and require approval before action.
- [Large catalogs consume context] → Inspect names first and load plausible
  candidates; add indexing only after measured need.
- [A saved flow may be too task-specific] → Default ambiguous scope to local
  and make destination part of approval.
- [Approval context can be lost] → Persist nothing before approval and require
  a fresh routing pass rather than guessing.

## Migration Plan

Add the skill and package references without changing existing configuration or
flow files. Rollback removes the new skill and its package/documentation
references; flows explicitly approved and saved by users remain ordinary USW
flows.

## Open Questions

None.
