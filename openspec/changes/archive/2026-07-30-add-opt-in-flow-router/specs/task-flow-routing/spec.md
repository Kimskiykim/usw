## ADDED Requirements

### Requirement: Routing is explicitly scoped to one task
USW SHALL expose `$usw-route-task "<task>"` as an explicitly invoked workflow
for the supplied task and MUST NOT enable persistent or implicit routing.

#### Scenario: User invokes the router
- **WHEN** a user invokes `usw-route-task` with one task
- **THEN** the router assesses only that task and does not change project configuration

### Requirement: Simple tasks return without execution
The router SHALL recommend direct execution when a separate flow would add no
material value and MUST stop without executing the task, writing a flow or
changing HANDOFF.

#### Scenario: Supplied task is simple
- **WHEN** the router determines that the task does not benefit from a flow
- **THEN** it returns a direct-execution recommendation and performs no mutation

### Requirement: Discovery is bounded to available USW catalogs
The router SHALL search safe regular Markdown flows in developer-local storage,
the configured shared flow root and packaged examples, and MUST NOT perform
external or cross-project discovery.

#### Scenario: Catalogs contain candidates
- **WHEN** the router assesses a task that benefits from a flow
- **THEN** it compares candidates from all three allowed catalogs without following symlinks

#### Scenario: Packaged example is relevant
- **WHEN** a packaged example is the closest candidate
- **THEN** the router treats it only as an authoring source for a new saved flow

### Requirement: Every routed flow has an approval preview
The router MUST show the complete selected or proposed flow, its origin and
path, and the selection rationale before any save or execution, then stop for
explicit human approval.

#### Scenario: Exact match is found
- **WHEN** one existing runnable flow matches the task
- **THEN** the router previews that exact flow and performs no mutation before approval

#### Scenario: Match is partial or absent
- **WHEN** no existing runnable flow fully matches the task
- **THEN** the router previews a new named flow and includes its source and differences when adapted

#### Scenario: User does not approve
- **WHEN** the user rejects or does not approve the preview
- **THEN** no flow, HANDOFF or product file is changed and nothing is executed

### Requirement: Generated flows are saved before execution
After approval, the router SHALL save every new or adapted flow through
`usw-create-flow` before delegating the original task and exact saved name to
`usw-run-flow`. Exact existing matches SHALL skip authoring and delegate
directly to `usw-run-flow`.

#### Scenario: New flow is approved
- **WHEN** the user approves a new or adapted preview
- **THEN** the router saves it, verifies it and executes the saved flow against the original task

#### Scenario: Existing flow is approved
- **WHEN** the user approves an exact existing match
- **THEN** the router executes that origin and name without rewriting the flow

### Requirement: Destination is selected conservatively
The router SHALL select shared storage for project-specific or team-relevant
flows and developer-local storage for personal, experimental or ambiguous
flows, and MUST include the destination in the approval preview.

#### Scenario: Destination is ambiguous
- **WHEN** the router cannot establish that a proposed flow belongs to the project
- **THEN** it previews the flow in developer-local storage

### Requirement: Routing does not grant additional authority
Router preview or approval MUST NOT grant authority for commit, push, pull
request, deployment, release, destructive actions or other external effects
beyond the original user request and platform permissions.

#### Scenario: Flow reaches a permission boundary
- **WHEN** an approved flow requests an action requiring separate permission
- **THEN** `usw-run-flow` stops at its existing permission boundary
