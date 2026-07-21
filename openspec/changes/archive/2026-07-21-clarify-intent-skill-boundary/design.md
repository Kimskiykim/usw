## Context

The current `usw-refine-task` skill persists sessions under a configurable
shared `usw/refinements/` root and presents its outcome as input to a later
flow. That model makes a personal formulation dialogue look like shared
planning state. At the same time, `ACTION_CAPABILITIES` maps both
`clarify-intent` and `select-approach` to `usw-brainstorm-solutions`, although
the former needs stateful dialogue and the latter needs convergent solution
evaluation.

USW must remain provider-neutral: neither local intent clarification nor its
storage may depend on OpenSpec. Provider-owned planning begins only after a
separate explicit request.

## Goals / Non-Goals

**Goals:**

- rename the formulation capability to `usw-refine-intent`;
- make dialogue, one-case clarification, and local notes its complete boundary;
- store all new sessions under `.usw/refinements/`;
- allow an outcome with no backlog, spec, task, or next flow;
- route `clarify-intent` separately from solution evaluation;
- preserve existing shared refinement data without automatic migration.

**Non-Goals:**

- create or update provider-owned planning artifacts;
- implement a generic notes application or shared collaboration store;
- migrate historical sessions automatically;
- rename `usw-brainstorm-solutions` in this change;
- change `task.md`, execution evidence, review receipts, or provider adapters.

## Decisions

### Rename the capability without a compatibility alias

The directory, frontmatter name, metadata, script/test references and public
documentation move from `usw-refine-task` to `usw-refine-intent`. A packaged
alias is rejected because duplicate implicitly invokable skills would preserve
the ambiguous trigger and make harness selection nondeterministic. Release
notes will call out the breaking rename.

### Make `.usw/refinements/` an invariant local root

The capability resolves the project root and writes only beneath
`.usw/refinements/<safe-id>/`. It no longer chooses storage from
`refinement.root` or any provider setting. This matches `.usw/HANDOFF.md`:
both are developer-local resumable state, ignored by Git and outside the shared
artifact graph.

The initializer stops emitting and creating the shared default refinement root.
The legacy `refinement.root` configuration key is accepted only for detection
and migration diagnostics during the compatibility window; it never redirects
new clarification writes. Silently ignoring an existing shared session is
rejected: the capability reports the exact legacy path and asks for an explicit
copy/import decision.

### Preserve the three-file resumable model

`session.md`, `decisions.md`, and optional `outcome.md` remain because they
separate current state, accepted/superseded decisions, and the current
formulation. The templates change terminology from task/change planning to
intent clarification. `outcome.md` permits `Recommended next flow: none` and
does not imply promotion.

A single turn still resolves at most one decision case. This gives the user a
predictable dialogue and makes every saved note attributable to a confirmed
answer rather than an agent assumption.

### Separate clarification from solution evaluation in the registry

The closed registry maps:

```text
clarify-intent  -> usw-refine-intent
select-approach -> usw-brainstorm-solutions
```

`usw-brainstorm-solutions` is narrowed in wording and contracts to accept an
already bounded problem and return solution paths, recommendation, and first
step without writing clarification state. Renaming that skill is deferred so
this change has one public rename.

### Promotion is an external explicit operation

The clarification skill only returns local artifact references. A later user
request may pass `outcome.md` to a provider-aware planning capability, but the
clarification skill never selects the provider, creates a change, or copies its
notes automatically. The local notes therefore remain non-normative even after
another capability uses them as input.

## Risks / Trade-offs

- [Existing automation invokes `usw-refine-task`] → document the breaking rename
  and fail clearly instead of maintaining two ambiguous skill identities.
- [Legacy shared sessions are no longer resumed automatically] → preserve them
  byte-for-byte and report an explicit migration path.
- [`.usw` may be deleted as local state] → make the local/non-durable contract
  explicit; promotion is required when a result must become shared authority.
- [Standard Analysis can become multi-turn] → retain one-action runner semantics;
  each invocation handles one clarification case and returns control.
- [Legacy configuration field remains temporarily parseable] → emit a precise
  deprecation diagnostic and remove it only through a separately versioned
  configuration change if needed.

## Migration Plan

1. Rename the packaged skill and update its public contract and assets.
2. Change its state writer to the fixed local root with privacy/path checks.
3. Stop generating the shared refinement root for new workspaces and diagnose
   legacy `refinement.root` without mutating its contents.
4. Rewire standard action resolution and narrow solution-brainstorm wording.
5. Update documentation, metadata and tests, then run the full suite and
   OpenSpec validation.

Rollback restores the former skill identity and routing. It must not delete
new `.usw/refinements/` sessions or modify preserved legacy shared sessions.

## Open Questions

None for this change. Renaming `usw-brainstorm-solutions` and deciding whether
custom flows belong to core remain separate decisions.
