# local-custom-flows Specification

## Purpose
Define safe local/shared selection without changing the text execution mode.

## Requirements

### Requirement: Explicit origin selection
The system SHALL treat `--local` and `-l` as equivalent explicit selectors for
developer-local flows and `--shared` as the explicit shared selector.

#### Scenario: Create a local flow
- **WHEN** a user creates a named flow with `--local` or `-l`
- **THEN** the system writes only `.usw/flows/<name>.md`

#### Scenario: Run a shared flow
- **WHEN** a user runs a named flow with `--shared`
- **THEN** the system loads only `<flows.root>/<name>.md`

### Requirement: Implicit lookup is local-first
Without an explicit selector the system SHALL look in `.usw/flows` first and
then in configured `flows.root`.

#### Scenario: Both origins contain the same name
- **WHEN** a local and shared flow have the same safe name
- **THEN** the local file is selected and its origin is reported

### Requirement: Local и shared используют единый text path
After origin selection USW SHALL create the same immutable Markdown invocation.
Metadata, origin and `version-2` markers MUST NOT select a different executor.
Identity SHALL include origin even when names and Markdown bytes are equal.

#### Scenario: Equal content in different origins
- **WHEN** local and shared flows have equal names and Markdown
- **THEN** each selected invocation has an origin-specific identity and the same execution semantics

### Requirement: Local flow paths stay inside safe local state
The system MUST reject a local root or target that traverses a symbolic link or
resolves to a non-regular flow file.

#### Scenario: Local flow path is unsafe
- **WHEN** `.usw`, `.usw/flows`, an intermediate component or the selected file is unsafe
- **THEN** creation or execution stops before reading, writing or invoking the flow
