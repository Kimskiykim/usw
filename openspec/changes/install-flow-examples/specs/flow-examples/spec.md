## ADDED Requirements

### Requirement: Initialization installs exactly five flow examples
USW SHALL package and initialize exactly these non-normative examples under
`<flows.root>/examples/`:

- `analysis.md`;
- `development.md`;
- `testing.md`;
- `chat-review.md`;
- `dev-test.md`.

The examples directory MUST NOT contain an additional executable flow contract
or hidden runtime fallback.

#### Scenario: Fresh project receives examples
- **WHEN** `/usw-init` initializes a project whose configured flow root does not
  contain the example files
- **THEN** it creates all five files under `<flows.root>/examples/`

### Requirement: Every installed example is explicitly non-normative
Every example SHALL state that it is guidance rather than a normative workflow
contract, MUST NOT be executed in place, and SHALL instruct the user to copy it
to `<flows.root>/<name>.md` and adapt it before execution.

#### Scenario: User reads an installed example
- **WHEN** a user opens any file under `<flows.root>/examples/`
- **THEN** the file clearly explains its example status and copy-before-use path

### Requirement: Examples follow the current ordinary Markdown model
The Analysis, Development and Testing examples SHALL be human-readable ordinary
Markdown without the retired packaged role-scenario schema. The `chat-review`
and `dev-test` examples SHALL reflect the current project-owned flows at package
time while remaining examples rather than runtime fallbacks.

#### Scenario: Example content is inspected
- **WHEN** package tests inspect the five example assets
- **THEN** role examples contain no legacy executable scenario contract and the
  two named examples match their current project-owned source flows
