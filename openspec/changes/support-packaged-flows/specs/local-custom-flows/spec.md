## ADDED Requirements

### Requirement: New authoring uses packages and existing authoring preserves layout
When a requested safe flow name is absent in the selected origin,
`usw-create-flow` SHALL create `<name>/FLOW.md`. When exactly one compatible
flat or packaged entrypoint already exists, it SHALL update that same entrypoint
without moving it or changing its layout. Immediately before writing it MUST
recheck both candidate entrypoints and package components without following
symlinks, and stop if the target or alternate layout appeared, changed, or has
an unexpected filesystem type.

#### Scenario: Create an absent shared flow
- **WHEN** a user creates a new shared flow named `review`
- **THEN** the system writes `<flows.root>/review/FLOW.md`

#### Scenario: Edit an existing flat flow
- **WHEN** `<flows.root>/review.md` is the only existing entrypoint and the user updates `review`
- **THEN** the system updates `review.md` and does not create `review/FLOW.md`

#### Scenario: Safe package directory already contains resources
- **WHEN** `<flows.root>/review/` is a safe directory with resources but no entrypoint and the user creates `review`
- **THEN** the system writes only `review/FLOW.md` and preserves the other directory contents

#### Scenario: Alternate layout appears before write
- **WHEN** authoring selected an absent or packaged flow and `<name>.md` appears before the entrypoint write
- **THEN** authoring stops without overwriting either layout

## MODIFIED Requirements

### Requirement: Explicit origin selection
The system SHALL treat `--local` and `-l` as equivalent explicit selectors for
developer-local flows and `--shared` as the explicit shared selector. Layout
resolution SHALL occur only inside the explicitly selected origin.

#### Scenario: Create a local flow
- **WHEN** a user creates an absent named flow with `--local` or `-l`
- **THEN** the system writes only `.usw/flows/<name>/FLOW.md`

#### Scenario: Run a shared flow
- **WHEN** a user runs a named flow with `--shared`
- **THEN** the system loads the single compatible `<flows.root>/<name>.md` or `<flows.root>/<name>/FLOW.md` entrypoint

### Requirement: Local flow paths stay inside safe local state
The system MUST reject a local root, package directory, entrypoint, or explicitly
used package resource that escapes local state, traverses a symbolic link, or
has an unexpected filesystem type.

#### Scenario: Local flow path is unsafe
- **WHEN** `.usw`, `.usw/flows`, a package or resource component, or the selected entrypoint is unsafe
- **THEN** creation or execution stops before reading, writing or invoking the flow or resource
