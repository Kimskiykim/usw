## ADDED Requirements

### Requirement: Nested execution is an explicit structured capability
The runner SHALL provide a production executor for `CALL FLOW` only when the
root run uses `--experimental-structured`. Plain Markdown execution MUST NOT
interpret flow-to-flow calls as a runtime API.

#### Scenario: Structured parent calls a child
- **WHEN** a valid structured parent reaches `CALL FLOW child-flow`
- **THEN** the runner invokes `child-flow` through the production nested-flow executor instead of returning `missing_executor`

#### Scenario: Plain Markdown mentions another flow
- **WHEN** a default Markdown flow contains prose or metadata resembling `CALL FLOW`
- **THEN** the runner keeps the whole document in the default Markdown executor and does not activate nested structured semantics

### Requirement: Child lookup preserves the selected origin and root
Every child SHALL be resolved by safe name from the exact origin and root
selected for the root flow. The runner MUST NOT apply local-first fallback,
switch origins, follow a symbolic link, accept a non-regular file, or use a
packaged runtime fallback while resolving a child.

#### Scenario: Shared parent has a local namesake child
- **WHEN** a shared parent calls a name that exists in both shared and local roots
- **THEN** the runner loads only the child from the selected shared root

#### Scenario: Local parent calls an unsafe child path
- **WHEN** the local root, an intermediate component, or the selected child is a symbolic link or unsafe filesystem type
- **THEN** the runner stops before reading or invoking the child

### Requirement: The reachable flow graph is preflighted before mutation
Before the first executor of the root run mutates state, the runner SHALL load
and strictly validate every flow reachable through `CALL FLOW`, resolve their
required executors, and verify their declared authority. It MUST reject a
missing or invalid child and MUST reject direct or indirect cycles using the
ancestor flow identities of each traversal path.

#### Scenario: A descendant is invalid
- **WHEN** a valid parent reaches a graph containing a missing, invalid, or unresolvable descendant
- **THEN** graph preflight fails before any executor in the root graph is invoked

#### Scenario: An indirect cycle exists
- **WHEN** flow A calls B, B calls C, and C calls an ancestor identity
- **THEN** graph preflight reports the cycle path and invokes no executor

#### Scenario: A child is reused without recursion
- **WHEN** the same child is reachable from separate branches but is not an ancestor of itself on either path
- **THEN** graph preflight accepts the reuse and does not classify it as a cycle

### Requirement: Nested calls preserve inputs and execution context
The child SHALL receive the root task, selected scope, the parent action's
optional structured input, and the completed parent results allowed by the
existing binding contract. Nested execution MUST NOT broaden the permissions
or write authority of either the parent flow or any child executor.

#### Scenario: Parent action has structured input
- **WHEN** a `CALL FLOW` action has an action-specific input block
- **THEN** the child receives that block together with the root task and selected scope

#### Scenario: Child requires unauthorized writes
- **WHEN** the preflighted child executor declarations exceed the authority available to the parent action or flow
- **THEN** the runner stops before invoking the child executor with an authority mismatch

### Requirement: Parent completion follows the child terminal outcome
The nested-flow executor SHALL drive the child until it produces a terminal
outcome. It SHALL aggregate actual writes and output references from child
actions. The parent action and cursor SHALL advance only after a completed
child outcome; any other child status SHALL stop the parent with the same
status, outcome, detail, and accumulated evidence.

#### Scenario: Child completes
- **WHEN** every required child action completes within authority
- **THEN** the parent `CALL FLOW` action completes with aggregated writes and references and the parent cursor may advance

#### Scenario: Child needs a decision
- **WHEN** a child stops with `decision_required`
- **THEN** the parent remains on its `CALL FLOW` action and returns `decision_required` without invoking a later parent action

#### Scenario: Child violates its write contract
- **WHEN** a child reports actual writes outside its declared or inherited authority
- **THEN** the nested run fails and the parent cursor does not advance

### Requirement: Nested state is durable and conservatively resumable
The structured checkpoint SHALL preserve the root-to-active execution
ancestry, exact flow names, origins and identities, per-frame cursors, loop
counters, inputs, completed results, and active boundary status. Resume SHALL
revalidate the whole graph and source context, continue unfinished child work
before its parent, and MUST NOT automatically retry an executor recorded as
`in_progress` without a result.

Every new structured root run SHALL receive a UUID and store its checkpoint at
`.usw/states/flows/<origin>/<flow-name>/<run-id>/flow.json`. The stored run ID
and origin MUST match the selected path, and resume MUST select an exact run ID.

#### Scenario: Two runs use the same flow
- **WHEN** the same structured flow starts twice
- **THEN** each run has a distinct checkpoint path and neither state overwrites the other

#### Scenario: Local and shared names match
- **WHEN** local and shared structured flows have the same safe name
- **THEN** their checkpoints remain separated by the selected origin

#### Scenario: Sequential child is interrupted between actions
- **WHEN** a child has completed one action and the run stops before its next action
- **THEN** resume continues at that child action before returning to the parent cursor

#### Scenario: Executor may have been interrupted
- **WHEN** the active nested boundary is `in_progress` without a recorded result
- **THEN** resume reports the exact ancestry and executor and requires an explicit recovery decision before mutation

#### Scenario: A descendant changed after checkpoint
- **WHEN** any saved flow identity or applicable source identity differs during resume
- **THEN** the runner rejects automatic resume as stale

### Requirement: Parallel nesting preserves existing parallel semantics
A `CALL FLOW` child inside `PARALLEL` SHALL remain concurrent with its sibling
actions after complete graph preflight. The checkpoint SHALL preserve each
parallel branch independently, completed branch outcomes MUST NOT be repeated,
and an uncertain `in_progress` branch MUST require explicit recovery before
resume.

#### Scenario: Parallel child flows complete
- **WHEN** two preflighted `CALL FLOW` children in one parallel block complete
- **THEN** the runner aggregates their outcomes in document order and opens the next parent action

#### Scenario: One parallel branch is interrupted
- **WHEN** one branch has a completed outcome and another branch is left `in_progress` without a result
- **THEN** resume preserves the completed outcome and does not automatically rerun either branch

### Requirement: Nested execution remains one observable operation
The root run SHALL own one HANDOFF Begin and terminal Outcome. Child flows MUST
NOT create competing HANDOFF operations or require a separate user lifecycle.
The structured machine state SHALL remain in its run-scoped developer-local
checkpoint file, written atomically with private permissions. HANDOFF SHALL
identify the exact run ID and state reference. External or destructive actions
SHALL retain their existing explicit permission gates.

#### Scenario: Parent invokes multiple descendants
- **WHEN** a root flow completes through more than one nested level
- **THEN** HANDOFF records one root operation while the checkpoint represents nested progress

#### Scenario: Child reaches an external action
- **WHEN** a child requests commit, push, pull request, deployment, release, or another separately gated effect
- **THEN** nesting provides no implicit authorization and the existing permission boundary is returned

### Requirement: Existing checkpoints and non-nested flows remain compatible
The runner SHALL continue to read supported checkpoint schema versions for
non-nested v1 and v2 flows. It SHALL introduce nested state without rewriting
user flow documents and without changing successful non-nested execution.

The legacy singleton `.usw/FLOW.json` SHALL remain readable only when resume
does not select a run ID. New saves MUST NOT overwrite, move, or merge it.

#### Scenario: Resume an existing non-nested checkpoint
- **WHEN** a valid schema version 1, 2, or 3 checkpoint is resumed for its unchanged flow
- **THEN** the runner preserves the existing resume behavior

#### Scenario: Exact run resume ignores the legacy singleton
- **WHEN** `.usw/FLOW.json` exists and resume selects a run-scoped UUID
- **THEN** the runner loads only the selected run checkpoint

#### Scenario: Run a structured flow without CALL FLOW
- **WHEN** an existing v1 or v2 flow contains no nested-flow action
- **THEN** its parsing, cursor transitions, outcomes, and permissions remain unchanged
