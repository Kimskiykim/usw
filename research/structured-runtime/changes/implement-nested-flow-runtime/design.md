## Context

The structured v2 parser accepts `CALL FLOW`, and the runtime reference already
describes same-origin lookup, cycle rejection, and terminal child outcomes.
The production orchestrator does not register a flow executor, however.
`resolve_custom_executors` therefore returns `missing_executor` unless a test or
embedding supplies a synthetic `TypedExecutor(("flow", target))`.

The current structured state is one `FlowState` serialized to the singleton
developer-local `.usw/FLOW.json` with schema versions 1–3. It can represent one
flow cursor, loop counters, inputs, and completed results, but it lets one run
overwrite another and conflates equal local/shared flow names. Plain Markdown
follows a separate single-operation HANDOFF path and must remain unaffected.

## Goals / Non-Goals

**Goals:**

- make direct and parallel structured `CALL FLOW` executable without injected
  test adapters;
- preserve the selected local or shared root throughout the nested graph;
- reject unsafe graph structure and unavailable descendants before mutation;
- preserve authority, inputs, outcomes, evidence, and exact resume position;
- keep one user-visible root operation and existing permission boundaries;
- retain compatibility with non-nested flows and checkpoint schemas 1–3.

**Non-Goals:**

- interpret nested calls in default plain Markdown;
- let a child select another origin, root, or packaged fallback;
- add arbitrary jumps, unbounded loops, dynamic flow names, or a new DSL;
- change how a subagent internally interprets its own payload;
- grant script, delivery, Git, deployment, or release permissions through
  nesting;
- add an external scheduler, state service, or runtime dependency.

## Decisions

### 1. Register a built-in flow adapter in the structured runner

The structured runner will construct a production executor for `kind=flow`
from the already selected project root, flow root, and origin. Callers may
continue injecting typed executors for human, subagent, and test boundaries,
but they will not need to inject one executor per child-flow name.

The adapter will receive the existing `CallInvocation`, load the preflighted
child model, and return one normalized `ActionOutcome`. A completed child
returns the union of actual writes plus ordered output references. A
non-completed child preserves its status, outcome, detail, partial writes, and
references, so existing parent stop logic remains authoritative.

Alternative considered: keep `CALL FLOW` as an embedding hook. This preserves
the current small core but leaves the documented syntax unusable in the
packaged skill and cannot provide common safety or resume behavior.

### 2. Resolve children from an immutable run context

At root resolution, create a run context containing project root, exact flow
root, origin, task, scope, source identity, available executors, inputs, and
explicit permissions. Every descendant uses that context and loads only
`<selected-root>/<safe-name>.md`.

Root and path components are checked with `lstat`; symlinks and non-regular
flow files are rejected. Child lookup never performs local-first fallback and
never consults packaged templates. Checkpoints store logical origin and flow
identities rather than duplicating absolute paths or flow contents.

Alternative considered: call the public local-first resolver for each child.
That would let a local namesake silently enter a shared graph and would make
resume depend on changing precedence rather than the selected root.

### 3. Compile the complete nested graph before the first executor

Use an iterative depth-first graph walk over every `CALL FLOW` in top-level and
parallel actions. Cache parsed flows by selected origin, safe name, and
identity. Maintain ancestor identities per traversal path: encountering an
ancestor is a cycle, while reusing a completed node from another branch is a
valid DAG.

After structural loading, resolve all reachable skills, scripts, typed
executors, and aggregate child declarations. Parent authority checks use the
union of descendant executor declarations. Permission prompts remain runtime
boundaries and do not become approvals during preflight.

The walk is iterative rather than recursively limited, so users are not given
an arbitrary nesting-depth restriction. The finite file graph and cycle check
bound the traversal.

Alternative considered: resolve a child only when its parent action runs. That
could discover a missing descendant after earlier actions have mutated the
workspace, violating the existing preflight promise.

### 4. Represent nested progress as an execution tree

Each structured root run receives a UUID and stores its state at
`.usw/states/flows/<origin>/<flow-name>/<run-id>/flow.json`. The checkpoint
records the same run ID and origin and resume requires the exact run ID.
Directories are developer-local, reject symlinks and unsafe filesystem types,
and checkpoint replacement remains atomic with file mode `0600`.

Existing `.usw/FLOW.json` files remain readable as legacy checkpoints but are
never overwritten, moved, merged, or selected when a run ID is supplied.
Schemas 1–3 accept the run envelope only in run-scoped storage; their existing
state payload remains unchanged.

Introduce checkpoint schema version 4 for runs whose graph contains
`CALL FLOW`. The root node and every nested node hold the existing per-flow
state: name, origin, identity, cursor, loop counts, action inputs, completed
results, and source identity. An active call records its parent action and
child node. A parallel action records ordered branch nodes and outcomes.

The checkpoint also distinguishes a boundary that is ready from one written
as `in_progress` without a result. State is written atomically before each
executor and again after its outcome. Only the coordinator writes the
run-scoped `flow.json`; parallel workers report state transitions to it,
preventing concurrent file replacement.

Sequential resume descends to the deepest unfinished child before advancing
any ancestor. Parallel resume retains all completed branch outcomes and
continues only branches known not to have started. A branch left
`in_progress` without a result is never retried automatically; the runner
reports its ancestry and waits for an explicit recovery decision.

Schemas 1–3 keep their current payload loader and behavior. Schema 4 is written
only when nested state is needed. No user-authored flow is migrated or
rewritten.

Alternative considered: store a flat child cursor beside the parent. It cannot
represent multiple levels or parallel branches and makes stale descendant
validation ambiguous.

### 5. Drive a child to terminal status inside one parent boundary

One parent `CALL FLOW` is one top-level structured boundary. The adapter may
advance multiple child actions, checkpointing each transition, until the child
is completed or reaches a stop status. The parent cursor remains on the call
for all non-completed outcomes and advances only after completed child
aggregation.

For a nested flow inside `PARALLEL`, the existing parallel coordinator starts
the preflighted branch concurrently with siblings. Child action order remains
sequential inside that branch. Results are aggregated in document order even
when completion order differs.

Alternative considered: return to the user after every child action. That
would expose child cursors as parent boundaries, contradict the documented
terminal-child contract and complicating result binding.

### 6. Preserve one HANDOFF lifecycle

The root invocation writes the single HANDOFF Begin and terminal Outcome.
Nested adapters do not call `usw-manage-handoff` and do not create child
operations. The run-scoped `flow.json` remains the private machine checkpoint
and is written atomically with mode `0600`; HANDOFF records its run ID and
state reference, may report the active ancestry, and continues to identify the
root operation.

Task and flow content are not duplicated per frame. Existing action inputs and
completed results are persisted only where required for deterministic resume.
Commit, push, pull request, deployment, release, script execution, and other
permission-gated effects retain their existing checks at the exact executor
boundary.

Alternative considered: create a HANDOFF operation for each child. The current
lifecycle permits one active operation, so child operations would collide with
their parent and force the user to manage implementation detail manually.

## Risks / Trade-offs

- [Schema 4 adds state complexity] → isolate serialization and validation in
  typed helpers, reject unknown or partial nodes, and retain focused loaders
  for schemas 1–3.
- [Parallel workers could race checkpoint updates] → make one coordinator own
  all atomic writes and preserve branch results in document order.
- [Two coordinators could resume one run] → require the exact run ID now and
  add a lease only when concurrent resume is introduced.
- [Full graph preflight may inspect an ultimately unused branch] → accept the
  up-front cost to guarantee no late missing-flow or authority failure after
  mutation.
- [A process can stop after an executor side effect but before its outcome is
  saved] → persist `in_progress` first and require explicit recovery rather
  than silently repeating the executor.
- [Deep but acyclic graphs consume time and memory] → use iterative traversal
  and cache identical graph nodes without imposing an arbitrary user limit.
- [Existing documentation overstates current support] → update the run
  reference and tests together with the production adapter.

## Migration Plan

1. Add run-scoped checkpoint paths while retaining the legacy singleton reader.
2. Add nested graph and state models while retaining schema 1–3 readers.
3. Add safe graph compilation and the built-in flow adapter behind
   `--experimental-structured`.
4. Add schema 4 atomic persistence and conservative sequential/parallel resume.
5. Wire normalized outcomes, bindings, authority, HANDOFF reporting, and
   permission propagation.
6. Update skill/reference documentation and add focused plus full regression
   coverage.

Rollback removes the adapter and schema 4 writer while preserving schema 1–3.
If a schema 4 checkpoint exists, the older runtime must stop with an
unsupported-checkpoint error rather than discard or reinterpret it.

## Open Questions

None.
