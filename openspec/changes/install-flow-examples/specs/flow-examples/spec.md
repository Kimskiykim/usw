## ADDED Requirements

### Requirement: Initialization installs exactly two flow examples
USW SHALL package and initialize exactly these non-normative examples under
`<flows.root>/examples/`:

- `chat-review.md`;
- `dev-test.md`.

The examples directory MUST NOT contain an additional executable flow contract
or hidden runtime fallback.

#### Scenario: Fresh project receives examples
- **WHEN** `/usw-init` initializes a project whose configured flow root does not
  contain the example files
- **THEN** it creates both files under `<flows.root>/examples/`

### Requirement: Every installed example is explicitly non-normative
Every example SHALL state that it is guidance rather than a normative workflow
contract, MUST NOT be executed in place, and SHALL instruct the user to copy it
to `<flows.root>/<name>.md` and adapt it before execution.

#### Scenario: User reads an installed example
- **WHEN** a user opens any file under `<flows.root>/examples/`
- **THEN** the file clearly explains its example status and copy-before-use path

### Requirement: Examples follow the current project flows
The `chat-review` and `dev-test` examples SHALL reflect the current
project-owned flows at package time while remaining examples rather than
runtime fallbacks.

#### Scenario: Example content is inspected
- **WHEN** package tests inspect the two example assets
- **THEN** both examples match their current project-owned source flows
