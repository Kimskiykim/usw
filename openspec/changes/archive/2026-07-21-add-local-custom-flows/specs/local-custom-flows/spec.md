## ADDED Requirements

### Requirement: Explicit local custom-flow selection
The system SHALL treat `--local` and `-l` as equivalent explicit selectors for
developer-local custom flows in both flow creation and flow execution.

#### Scenario: Create a local custom flow
- **WHEN** a user creates a named custom flow with `--local` or `-l`
- **THEN** the system writes and validates only `.usw/flows/<name>.md`

#### Scenario: Run a local custom flow
- **WHEN** a user runs a named custom flow with `--local` or `-l`
- **THEN** the system loads only `.usw/flows/<name>.md`

### Requirement: Shared behavior remains the default
The system SHALL continue to use the configured `flows.root` when neither local
selector is present.

#### Scenario: Invoke without a local selector
- **WHEN** a user creates or runs a custom flow without `--local` or `-l`
- **THEN** the system uses `<flows.root>/<name>.md` with existing behavior

### Requirement: Local flows cannot replace standard role scenarios
The system MUST reject local selection for the standard Analysis, Development,
and Testing flows.

#### Scenario: Select a standard flow locally
- **WHEN** a user supplies `--local` or `-l` for a standard role flow
- **THEN** the system stops before execution with a clear unsupported-selection error

### Requirement: Resume preserves custom-flow origin
The system SHALL distinguish local and shared custom flows in operation identity
even when their names and Markdown bytes are equal.

#### Scenario: Resume with a different origin
- **WHEN** saved operation state belongs to one origin and resume loads the other origin
- **THEN** the system rejects resume as a stale or different flow

### Requirement: Local flow paths stay inside safe local state
The system MUST reject a local-flow root or target that traverses a symbolic link
or resolves to a non-regular flow file.

#### Scenario: Local flow path is unsafe
- **WHEN** `.usw`, `.usw/flows`, or the selected flow file is an unsafe path type
- **THEN** creation or execution stops before reading, writing, or invoking the flow
