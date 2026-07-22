## MODIFIED Requirements

### Requirement: Clarification artifacts are local and non-normative
USW MUST store clarification sessions under `.usw/refinements/<refinement-id>/` with `session.md`, `decisions.md`, and an optional `outcome.md`. These artifacts MUST remain developer-local and MUST NOT be treated as backlog, specification, provider-owned planning state, or evidence of completed work.

The clarification capability MUST reject unsafe or symlinked local paths, but MUST NOT inspect or enforce Git tracked/ignore state. Repository tracking policy belongs to the user.

#### Scenario: New clarification starts
- **WHEN** no matching local session exists
- **THEN** USW creates the session only under `.usw/refinements/` and does not create or modify a shared refinement root

#### Scenario: Clarification is resumed
- **WHEN** a later invocation supplies the same refinement ID and compatible goal
- **THEN** USW resumes from the saved local current case without reconstructing accepted decisions from conversation history

#### Scenario: Local path is unsafe
- **WHEN** `.usw/refinements/` resolves through a symbolic link or outside the project
- **THEN** the capability stops before writing and reports a path error

#### Scenario: Local clarification state is tracked
- **WHEN** `.usw/refinements/` contains a Git-tracked entry
- **THEN** the capability leaves tracking unchanged and continues according to the local artifact contract

### Requirement: Existing shared refinement data is preserved
USW MUST NOT automatically discover, read, move, merge, delete, or rewrite existing sessions under configured or historical shared refinement roots. Historical data MUST NOT block creation or resumption of local clarification state, including a local session with the same refinement ID.

#### Scenario: Legacy shared session has the same ID
- **WHEN** a historical shared session and a requested local clarification use the same refinement ID
- **THEN** USW leaves the shared session byte-for-byte unchanged and creates or resumes only the local session without requiring migration
