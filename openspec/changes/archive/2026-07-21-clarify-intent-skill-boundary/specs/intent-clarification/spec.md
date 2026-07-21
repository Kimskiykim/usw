## ADDED Requirements

### Requirement: Intent clarification has one bounded responsibility
USW SHALL expose `usw-refine-intent` as a conversational capability whose only
responsibilities are to conduct dialogue, clarify one decision case per user
turn, and save local non-normative notes.

#### Scenario: User brings an ambiguous idea
- **WHEN** the user asks to formulate an idea, problem, request, or decision
- **THEN** `usw-refine-intent` opens or resumes a local clarification session
  and discusses only its current decision case

#### Scenario: User confirms a decision
- **WHEN** the user unambiguously answers the current clarification question
- **THEN** the capability records the decision and advances to at most one next
  open case without starting planning or implementation

### Requirement: Clarification artifacts are local and non-normative
USW MUST store clarification sessions under
`.usw/refinements/<refinement-id>/` with `session.md`, `decisions.md`, and an
optional `outcome.md`. These artifacts MUST remain under the developer-local
ignored `.usw/` namespace and MUST NOT be treated as backlog, specification,
provider-owned planning state, or evidence of completed work.

#### Scenario: New clarification starts
- **WHEN** no matching local session exists
- **THEN** USW creates the session only under `.usw/refinements/` and does not
  create or modify a shared refinement root

#### Scenario: Clarification is resumed
- **WHEN** a later invocation supplies the same refinement ID and compatible goal
- **THEN** USW resumes from the saved local current case without reconstructing
  accepted decisions from conversation history

#### Scenario: Local state is not safely ignored
- **WHEN** `.usw/refinements/` could be tracked or resolved through an unsafe path
- **THEN** the capability stops before writing and reports a privacy or path error

### Requirement: A clarification may end without downstream work
`usw-refine-intent` SHALL allow a session to finish with a standalone formulated
outcome, a paused state, or unresolved questions. It MUST NOT require or imply a
backlog item, OpenSpec change, implementation plan, executable task, or next flow.

#### Scenario: Formulation is sufficient
- **WHEN** the user accepts the current formulation and requests no further work
- **THEN** the capability writes the current outcome, marks the session ready,
  returns its local references, and stops with no recommended flow required

#### Scenario: User later wants planning
- **WHEN** the user explicitly requests promotion of a ready outcome into planning
- **THEN** `usw-refine-intent` returns its references and leaves all
  provider-owned writes to a separate authorized capability

### Requirement: Intent clarification is distinct from solution evaluation
USW SHALL route the standard `clarify-intent` action to
`usw-refine-intent`. Solution comparison SHALL remain a separate capability
that accepts a bounded problem, compares approaches, recommends one, and returns
without writing clarification state.

#### Scenario: Analysis needs missing intent details
- **WHEN** a validated Analysis flow selects `clarify-intent`
- **THEN** the runner invokes `usw-refine-intent` for one decision case

#### Scenario: Analysis needs an approach choice
- **WHEN** a validated Analysis flow selects `select-approach`
- **THEN** the runner invokes the solution-evaluation capability rather than
  continuing the clarification dialogue implicitly

### Requirement: Existing shared refinement data is preserved
The change MUST NOT automatically move, merge, delete, or rewrite existing
sessions under configured or historical shared refinement roots.

#### Scenario: Legacy shared session exists
- **WHEN** USW detects an existing `usw/refinements/<refinement-id>/` session
- **THEN** it leaves the session byte-for-byte unchanged and requires an explicit
  user-directed migration before using it as local clarification state

### Requirement: Public skill identity reflects intent clarification
The packaged capability SHALL be named `usw-refine-intent`; public metadata,
documentation, runtime references, and tests SHALL use that identity instead of
`usw-refine-task`.

#### Scenario: Installed package is inspected
- **WHEN** a supported harness discovers packaged skills
- **THEN** it exposes `usw-refine-intent` with its bounded description and does
  not advertise `usw-refine-task` as an equivalent active capability
