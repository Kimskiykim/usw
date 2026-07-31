## ADDED Requirements

### Requirement: Explicit intent finds an existing runnable flow
USW SHALL expose `usw-find-flow` as an explicitly invoked read-only capability
that searches direct developer-local and configured shared Markdown flows for
one supplied intent.

#### Scenario: One flow is the clear match
- **WHEN** one existing runnable flow clearly matches the supplied intent
- **THEN** the finder returns its name, origin, path, rationale and an
  explicit-origin `usw-run-flow` command containing the original intent

### Requirement: Discovery uses safe bounded resolution
The finder MUST inspect only safe kebab-case regular `*.md` entries directly
inside the local and shared flow roots and MUST load candidates through the
same contained, no-symlink resolution boundary as `usw-run-flow`.

#### Scenario: Candidate is a symlink
- **WHEN** a catalog entry or one of its path components is a symbolic link
- **THEN** the finder excludes or rejects it without reading the flow

### Requirement: Discovery has no side effects
The finder MUST NOT create, adapt or execute a flow, invoke HANDOFF, change
configuration or search packaged examples, external catalogs or other
projects.

#### Scenario: No flow matches
- **WHEN** no runnable local or shared flow matches the supplied intent
- **THEN** the finder returns `no-match` without writing state and may name
  `usw-create-flow` as a separate next action

### Requirement: Ambiguous matches stop visibly
The finder MUST return `ambiguous` when materially tied candidates would lead
to different processes and MUST NOT choose or execute either candidate.

#### Scenario: Local and shared flows are equally plausible
- **WHEN** local and shared candidates both materially match the intent and
  neither is clearly preferable
- **THEN** the finder returns both candidates with their origins and stops

### Requirement: Legacy router is absent
USW MUST NOT package or advertise `usw-route-task`, and forced installation
SHALL remove previously installed router skill and command files.

#### Scenario: Force upgrade from a router release
- **WHEN** a user runs `install.sh --force` over an installation containing
  `usw-route-task`
- **THEN** the old skill and command are removed and `usw-find-flow` is
  installed
