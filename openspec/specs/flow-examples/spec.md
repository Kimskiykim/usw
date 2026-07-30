# flow-examples Specification

## Purpose
Define the exact non-normative text-first examples installed with USW.

## Requirements

### Requirement: Initialization installs exactly two flow examples
USW SHALL package and initialize exactly `chat-review.md` and `dev-test.md`
under `<flows.root>/examples/`. The directory MUST NOT provide a hidden runtime
fallback.

#### Scenario: Fresh project receives examples
- **WHEN** initialization finds either example absent
- **THEN** it creates the missing file under `<flows.root>/examples/`

### Requirement: Every installed example is explicitly non-normative
Each example SHALL state that it is guidance, MUST NOT be executed in place and
SHALL instruct the user to copy it to `<flows.root>/<name>.md` before execution.

#### Scenario: User reads an example
- **WHEN** a user opens an installed example
- **THEN** its example status and copy-before-use path are clear

### Requirement: Examples не обещают machine execution
Each example SHALL be ordinary readable Markdown and MUST NOT claim strict
validation, a machine cursor, deterministic control flow or a mandatory role
lifecycle.

#### Scenario: Example content is inspected
- **WHEN** package tests inspect both assets
- **THEN** they describe a model-executed process and an ordinary run command
