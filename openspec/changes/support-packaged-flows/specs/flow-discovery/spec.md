## MODIFIED Requirements

### Requirement: Explicit intent finds an existing runnable flow
USW SHALL expose `usw-find-flow` as an explicitly invoked read-only capability
that searches direct developer-local and configured shared flat or packaged
flows for one supplied intent.

#### Scenario: One flow is the clear match
- **WHEN** one existing runnable flat or packaged flow clearly matches the supplied intent
- **THEN** the finder returns its name, origin, entrypoint path, rationale and an
  explicit-origin `usw-run-flow` command containing the original intent

### Requirement: Discovery uses safe bounded resolution
The finder MUST inspect only safe kebab-case regular `*.md` entries and direct
safe kebab-case directories containing a regular `FLOW.md` inside the local and
shared flow roots. It MUST NOT recurse into package directories and MUST load
candidates through the same contained, descriptor-relative, no-symlink
resolution boundary as `usw-run-flow`.

#### Scenario: Candidate is a symlink
- **WHEN** a flat entry, package directory, `FLOW.md`, or one of its path components is a symbolic link
- **THEN** the finder excludes or rejects it without reading the flow

#### Scenario: Package contains nested Markdown resources
- **WHEN** a direct package contains Markdown under `references/` or another resource directory
- **THEN** the finder considers only the package's direct `FLOW.md` entrypoint

## ADDED Requirements

### Requirement: Discovery exposes layout ambiguity
The finder MUST return `ambiguous` with `ambiguous_flow_layout` evidence when
one origin contains both compatible entrypoints for a safe name. It MUST NOT
read, skip, or rank either layout as a runnable candidate.

#### Scenario: Catalog contains both layouts for one name
- **WHEN** finder cataloging observes safe `<name>.md` and `<name>/FLOW.md` in the same origin
- **THEN** it returns `ambiguous` identifying both entrypoint paths and the `ambiguous_flow_layout` cause
