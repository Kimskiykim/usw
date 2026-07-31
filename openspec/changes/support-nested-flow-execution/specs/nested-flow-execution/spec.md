## ADDED Requirements

### Requirement: Root executor creates nested execution context
After preparing a root invocation, USW SHALL allow that root executor to
dispatch a named flow as nested work with its root execution identity and a
branch label. When handoff is enabled, the root identity MUST be the exact
registered operation identity returned by Begin. When handoff is disabled, it
MUST be a unique ephemeral identity that is neither persisted nor checked
against local handoff artifacts.

Nested context MUST come from the root executor, MUST NOT be derived from child
flow Markdown or ordinary user input and MUST NOT be exposed as a general
handoff-bypass selector.

#### Scenario: Root dispatches a child flow
- **WHEN** an active root executor assigns a named child flow to a subagent
- **THEN** it passes nested context containing its exact root execution identity and branch label

#### Scenario: Handoff is disabled
- **WHEN** a root invocation runs with effective `handoff: false`
- **THEN** its nested context uses a unique ephemeral root identity without reading or modifying local handoff artifacts

#### Scenario: User requests standalone nested mode
- **WHEN** no active root executor supplied nested context
- **THEN** USW treats the request as an independent root invocation and applies the normal Begin boundary

### Requirement: Nested flow is resolved as an immutable invocation
USW SHALL apply the ordinary safe flow resolver to every nested invocation and
SHALL pass the exact resolved Markdown, origin, identity and original child
input to the child model without rereading the path. When handoff is enabled,
it MUST confirm immediately before model execution that the router still
contains the exact parent operation and that its operation document remains
recoverable. When handoff is disabled, it MUST NOT inspect handoff artifacts.

#### Scenario: Nested flow resolves safely
- **WHEN** a child flow is selected inside an active root operation
- **THEN** USW resolves it with the same origin, containment, symlink and exact-byte rules as a root flow

#### Scenario: Parent route is stale
- **WHEN** the parent route is absent or its operation identity or status no longer matches nested context
- **THEN** nested model execution stops without changing any handoff artifact

#### Scenario: Recoverable root is explicitly continued
- **WHEN** the root executor explicitly continues its exact current `paused`, `blocked` or `decision_required` operation and dispatches a child
- **THEN** read-only parent verification accepts the unchanged routed identity

#### Scenario: Disabled handoff has existing routed state
- **WHEN** nested execution is dispatched with effective `handoff: false`
- **THEN** execution proceeds without inspecting or changing the existing router or operation files

### Requirement: Nested execution does not own durable state
A nested invocation MUST NOT call Begin, Outcome, Save or Finish and MUST NOT
create or modify a router or operation document. Multiple nested invocations
bound to the same root operation MAY therefore execute concurrently without
competing for durable state ownership.

#### Scenario: Independent nested branches run concurrently
- **WHEN** a root flow dispatches two independent named flows with the same root execution context
- **THEN** both may execute concurrently while only their root operation remains registered

#### Scenario: Different roots dispatch nested branches
- **WHEN** two concurrent registered roots each dispatch an independent nested flow
- **THEN** each child verifies its own parent identity and neither child changes either root's durable state

#### Scenario: Nested branch reaches a natural stop
- **WHEN** a nested flow completes, fails, pauses, blocks or requires a decision
- **THEN** it returns its status and factual result to its root executor without writing Outcome

### Requirement: Root executor aggregates nested results
The root executor SHALL collect the identity, status and factual result of each
started nested invocation and SHALL remain the sole writer of its registered
operation Outcome. It SHALL follow the root Markdown when interpreting child
statuses; if the required aggregate action is materially ambiguous, it MUST
use `decision_required`. A child permission boundary MUST remain
`decision_required` and MUST NOT gain authority from root or child flow text.

#### Scenario: All parallel branches complete
- **WHEN** every started nested branch returns `completed`
- **THEN** the root executor uses their results in the remaining root flow and writes one Outcome to its exact operation document

#### Scenario: Child requires permission
- **WHEN** a nested child reaches an external-action permission boundary
- **THEN** it returns `decision_required` and the root records the unresolved decision in its own Outcome

#### Scenario: Child status has no declared handling
- **WHEN** a child returns a non-completed status and root Markdown does not determine the aggregate action
- **THEN** the root records `decision_required` rather than guessing or retrying

### Requirement: Nested branches add no durable branch runtime
USW MUST NOT create per-child handoff files, child router entries, a persistent
branch registry, a machine cursor or automatic child retry. `PARALLEL` remains
readable guidance and concurrent execution MUST be limited to work the root
flow identifies as independent.

#### Scenario: Child execution is interrupted
- **WHEN** a nested child exits without returning a reliable result
- **THEN** the root does not repeat the child automatically and represents the unresolved work in its operation

#### Scenario: Parallel branches have dependent actions
- **WHEN** child work is ordered, dependent or has overlapping writes
- **THEN** USW does not infer safe parallel execution from nested context
