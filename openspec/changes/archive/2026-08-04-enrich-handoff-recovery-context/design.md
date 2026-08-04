## Context

The routed handoff design correctly separates the authoritative operation-ID
router from mutable per-operation recovery state. Each operation currently
records exact input, progress, checks and references, but multi-operation
discovery exposes only a flow name, status and opaque operation hash. The state
also keeps only the latest `Updated` time and has no bounded description of the
worktree context an interrupted operation expects.

The handoff remains developer-local recovery state. It is not an audit log, a
write lock, or proof that a reported path was changed by one operation rather
than another concurrent process.

## Goals / Non-Goals

**Goals:**

- Make concurrent operation selection understandable without opening every
  operation file.
- Retain the start boundary separately from the latest update.
- Preserve small, factual expected-write and observed-change hints for resume.
- Keep current routed operation files readable and safely upgradable.
- Leave the router and operation identity unchanged.

**Non-Goals:**

- Restore role-based execution, flow cursors, attempts or a session journal.
- Detect, prevent, attribute or merge overlapping product writes.
- Reintroduce a full product-tree source digest or machine checkpoint.
- Retain history after Finish.

## Decisions

### New operations use an enriched document shape

`Summary` and `Started` are added to metadata. `Summary` is a normalized,
bounded one-line label supplied at Begin or derived from exact input when the
caller omits it. `Started` is written once with the initial `Updated` value and
is immutable for later Outcome and Save transitions.

A `Workspace` section is appended after `References` and contains three
validated lines: the Git base revision observed at Begin (or an explicit
`unborn`, `not-git` or `unknown` state), a JSON list of expected write areas
supplied at Begin, and a JSON list of changes reported at the latest Outcome.
JSON lists avoid ambiguous comma escaping while remaining compact Markdown
text. Values are informational and never grant write authority.

Alternative considered: restore the old metadata and journal tables. Rejected
because their roles, executors and flow cursors belong to the retired structured
runtime and would again make handoff an audit surface.

Alternative considered: hash the entire product worktree. Rejected because the
full freshness model was deliberately removed and is unnecessary for a bounded
resume hint. A base revision plus reported areas exposes uncertainty without
claiming a complete source identity.

### Begin and Outcome own different workspace facts

Begin records the base revision and expected write hints before model execution.
Outcome preserves both and replaces only observed changes with facts returned
by the root executor. Empty expected writes mean `not-declared`; empty Outcome
changes mean `none-reported`. The runtime does not infer operation ownership
from global `git status`, because concurrent processes make that attribution
unreliable.

### Existing operation documents remain readable

The parser accepts both the current document shape and the enriched shape.
Read-only Show, Resume and parent checks do not rewrite old bytes. Discovery
derives an ephemeral summary from exact input and reports `Started: unknown` for
an old document.

Outcome upgrades an old document as part of the requested mutation: it derives
the summary, records `Started` and base revision as `unknown`, and adds the
reported observed changes. Save may update an old target only with an enriched
candidate; it must not downgrade an enriched target. Unknown values explicitly
preserve missing knowledge instead of treating the old `Updated` time as the
operation start.

### Discovery exposes bounded human context

Multi-operation discovery adds `summary`, `started` and `updated` alongside the
existing operation, flow, status and path. The operation ID remains the only
selector and routing key.

## Risks / Trade-offs

- [Reported paths may be incomplete or shared with another operation] → Label
  them informational and retain the explicit no-attribution boundary.
- [Derived summaries may be similar] → Keep exact operation ID as the selector
  and include timestamps in discovery.
- [Two readable document shapes increase parser complexity] → Accept exactly
  the old or enriched metadata/section sets and always render only the enriched
  shape for new operations.
- [Repository has no commit yet] → Record the explicit base value `unborn`;
  record `not-git` only when no Git metadata is available.
- [Git metadata exists but cannot be inspected] → Record `unknown` rather than
  misclassifying an operational failure as an unborn repository.

## Migration Plan

1. Add parser and discovery tests for old and enriched documents.
2. Render enriched documents for new Begin operations.
3. Upgrade old documents only on Outcome or an explicitly enriched Save.
4. Update the Markdown skill contracts and end-to-end coverage.

Rollback remains possible while old documents exist. Enriched operation files
must be explicitly finished before using an older runtime that does not know the
new shape; the router and product files require no migration.

## Open Questions

None.
