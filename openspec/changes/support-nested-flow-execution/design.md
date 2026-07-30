## Context

USW currently stores one generic operation in the project-wide
`.usw/HANDOFF.md`. Begin holds the filesystem lock only for its transition, but
the resulting recoverable status acts as a logical project-wide mutex until
Finish. This prevents both independent top-level flows in separate chats and a
root flow from reusing `$usw-run-flow` for named child work.

Every Begin already creates a unique operation identity from a fresh invocation
token, flow origin, flow identity and exact-input digest. Outcome already names
that identity to reject stale writers. The same identity can therefore route
recovery state without introducing a user-defined workstream key.

The runtime remains text-first: `CALL`, `PARALLEL` and statuses are readable
model instructions, not a parser, scheduler or checkpoint DSL. Handoff remains
optional, developer-local recovery state. Effective `handoff: false` must
prevent every router and operation-state read or write.

## Goals / Non-Goals

**Goals:**

- Use `.usw/HANDOFF.md` as the human-readable router for independently
  addressable operation states.
- Let independent top-level invocations execute concurrently without weakening
  exact-operation and stale-writer checks.
- Let one root flow delegate named child flows, including independent parallel
  branches, while keeping one durable state owner for that root operation.
- Preserve safe flow resolution, immutable Markdown/input, explicit recovery
  and normal permission boundaries.
- Keep router contention limited to short serialized state transitions.
- Migrate current generic single-state HANDOFF content without losing
  recoverable work.

**Non-Goals:**

- Detection, prevention or merging of overlapping product-file writes.
- User-defined workstream names as a required routing key.
- Durable per-child state, independent child resume or automatic child retry.
- An audit log or retained history after an operation's explicit Finish.
- Atomic execution, deterministic scheduling, cancellation guarantees or a
  machine parser for Markdown control markers.
- A security boundary against a malicious local process.

## Decisions

### 1. Operation identity is the routing key

`.usw/HANDOFF.md` becomes an authoritative Markdown router whose entries map an
exact `usw-operation:<sha256>` identity to a generated relative file below
`.usw/handoffs/`. The operation filename is derived only from the validated
hex identity suffix; router content cannot select an arbitrary path.

The router stores membership and immutable routing data only. Mutable status,
input and recovery sections live exclusively in the operation file, so Outcome
does not need a two-file status update. Show and Resume read the validated
operation file to present flow, input, status and current position.

Alternative considered: require a human label such as `ui` or `backend`.
Rejected because the invocation identity is already unique and exact. A label
may be displayed as optional metadata later, but it is not needed for routing.

Alternative considered: derive the active set by scanning the operation
directory and make HANDOFF a disposable view. Rejected because the explicit
router gives one deterministic recovery entry point and makes unregistered
partial files non-active by definition.

### 2. Router membership and operation content have separate authority

The router is authoritative for whether an operation is registered. A
registered operation file is authoritative for that operation's status and
recovery content. Every lookup validates both the router entry and the regular
operation file through descriptor-relative, no-symlink, contained access.

Begin creates the unique identity before model execution and then, under the
existing exclusive `.usw` directory lock:

1. validates the router and rejects an impossible identity collision;
2. lazily creates or validates the contained `.usw/handoffs/` directory;
3. atomically writes and exact-byte verifies the `in_progress` operation file;
4. atomically adds and exact-byte verifies its router entry.

The executor MUST NOT start until both files are confirmed. If a handled error
occurs before registration, Begin removes only the candidate file created by
that attempt. A process crash before router registration can leave an orphan,
but no executor was authorized to start and the orphan is not recoverable
state. A crash after router registration remains a conservative registered
`in_progress` operation and is never retried automatically.

The lock serializes complete read-check-write transitions, not model execution.
Two concurrent Begin calls therefore receive different identities and may both
register successfully in a deterministic order.

Alternative considered: atomically replace router and operation content as one
filesystem transaction. Rejected because portable file replacement is atomic
per file, not across both files; ordered writes plus the execution boundary
provide the required recovery guarantee.

### 3. Every state mutation addresses one exact operation

Outcome, Save and Finish require the exact operation identity returned by
Begin. Under the directory lock they resolve that identity through the router,
validate the operation document and apply the transition only if its embedded
identity and immutable context still match.

Save uses an operation-scoped candidate such as
`.usw/handoffs/<identity>.next.md`; concurrent chats never share the current
global `HANDOFF.next.md`. Outcome changes only the operation file because the
router does not duplicate status.

Generic `in_progress`, `paused`, `blocked` and `decision_required` remain
recoverable. `failed` and `completed` remain inspectable until Finish for that
same identity. A new Begin creates another route and never replaces an
unrelated terminal operation.

Finish first atomically removes the route and confirms the router, then removes
only the exact operation file and its candidate if present. A crash after
unregistration can leave a non-routable orphan but cannot revive or overwrite
another operation. Operation files are not history and are not retained after
successful Finish.

Alternative considered: let any new Begin remove terminal entries. Rejected
because with concurrent roots there is no principled terminal operation for an
unrelated invocation to replace.

### 4. Discovery is explicit when more than one operation exists

Show and Resume accept an operation identity. Without one they behave as
follows:

- no registered operations means there is no work to inspect or resume;
- one registered operation is selected without an extra decision;
- multiple registered operations return a concise list derived from validated
  state documents and require the user to select an identity.

`in_progress` still means mutation may have been interrupted and MUST NOT
trigger automatic repetition. Finish without an identity follows the same
zero/one/many selection rule.

The active chat already holds the exact Begin identity for Outcome and Save.
The router exists primarily for discovery and recovery by a different chat.

### 5. Nested flows borrow the parent identity without owning state

Every root invocation owns a root execution identity. With handoff enabled it
is the exact registered operation identity returned by Begin. With handoff
disabled it is a unique ephemeral identity that is neither persisted nor
checked against local state.

The root executor may pass a child subagent an internal nested context
containing its root identity, effective handoff mode, branch label, child flow
selector and original child input. Ordinary user input and child Markdown
cannot create or replace this context.

Before nested model execution, a read-only `assert-current` operation resolves
the parent through the router and confirms that its operation file has the
exact identity and a recoverable status. The check does not modify router or
state. Nested execution never calls Begin, Outcome, Save or Finish. The child
returns its identity, status and factual result to the root, and the root
remains the only writer of its operation Outcome.

Multiple nested branches under one root and nested branches belonging to
different concurrent roots can therefore run without competing for durable
state ownership. Parallel product writes remain safe only when the flow
declares genuinely independent work.

Alternative considered: give every child its own durable operation. Rejected
because independent child recovery, aggregation and lifecycle are unnecessary
for nested composition; routed state is for independent top-level roots.

### 6. Existing state migrates at the handoff boundary

Initialization with enabled handoff creates an empty router and leaves
`.usw/handoffs/` lazy until the first Begin. With disabled handoff it creates
and inspects neither artifact.

When an enabled handoff command encounters the current generic format:

- generic idle becomes an empty router;
- generic non-idle state is copied byte-for-byte to the path derived from its
  validated embedded operation identity, then the router is atomically written
  to reference it;
- the old file remains authoritative until the router replacement succeeds, so
  a failed migration does not lose recovery state.

Legacy role-based HANDOFF has no compatible operation identity and remains
read-only for Show and Resume. It blocks Begin and is not migrated
automatically. Explicit Finish replaces it with an empty router.

Rollback to a version that understands only single-state HANDOFF is safe only
after all routed operations are explicitly finished and the empty router is
replaced by legacy generic idle state. Product files and flows require no
migration.

### 7. Disabled handoff remains a hard boundary

When effective `handoff` is `false`, initialization, root execution, nested
execution, Show, Resume, Save and Finish do not inspect `.usw/HANDOFF.md`,
`.usw/handoffs/` or an existing candidate. Root execution uses an ephemeral
identity only for in-memory nested coordination.

This boundary is checked before router parsing or directory validation so an
invalid existing local state cannot affect disabled execution.

## Risks / Trade-offs

- [Independent operations may edit the same product files] → Document that
  concurrency is user-declared and provide no false isolation guarantee.
- [Terminal routes can accumulate] → Keep them inspectable but require explicit
  per-operation Finish; do not turn local recovery state into automatic
  history.
- [A crash can leave an unregistered operation file] → Treat router membership
  as authoritative, never execute before registration and report safe orphans
  during handoff inspection without resuming them.
- [A root crash can lose unsummarized child results] → Preserve conservative
  parent `in_progress` recovery and prohibit automatic child retry.
- [A stale child may continue computation after parent Finish] → Check the
  parent immediately before child execution and reject every later state
  mutation whose exact operation route no longer exists.
- [Older USW versions cannot parse the router] → Document the local-state
  migration and require explicit operation cleanup before rollback.
- [Child status aggregation can be ambiguous] → Follow root Markdown and use
  `decision_required` instead of hidden status precedence.

## Migration Plan

1. Add router and operation-document parsing, safe path derivation and
   migration tests without changing flow execution.
2. Update initialization to create the empty router and keep the operation
   directory lazy.
3. Address Begin, Outcome, Save, Show, Resume and Finish by operation identity
   and cover concurrent transitions, partial writes and orphan behavior.
4. Add read-only routed parent verification.
5. Update root and nested execution contracts and cover sequential and
   parallel nested flows across one or more roots.
6. Update documentation with concurrent-chat, selection, cleanup, disabled
   handoff and product-write boundaries.

## Open Questions

None. Optional display labels and explicit orphan cleanup can be separate
future usability changes because neither is required for correct routing or
recovery.
