# text-flow-execution Specification

## Purpose
Define the single production path for model-executed Markdown flows.

## Requirements

### Requirement: Один immutable Markdown invocation
USW SHALL read the selected flow exactly once, compute identity from the same
bytes, decode them as UTF-8 and pass separate immutable `flow_markdown` and
`user_input` values to the model.

#### Scenario: Flow changes after loading
- **WHEN** the file changes after an invocation has been prepared
- **THEN** the invocation uses the already loaded Markdown and its original identity

### Requirement: Безопасное разрешение text flow
USW SHALL resolve only a safe kebab-case name inside the selected local or
shared root. It MUST check containment, every existing path component, reject
symbolic links and require a regular final file before reading. Traversal and
the final read SHALL be descriptor-relative with no pathname re-open after a
component is trusted.

#### Scenario: Intermediate symlink
- **WHEN** any component leading to the selected flow is a symbolic link
- **THEN** USW stops before reading the flow or invoking the model

### Requirement: Модель следует тексту без machine guarantees
USW SHALL interpret the complete Markdown as a human-readable process until
`completed`, `failed`, `blocked`, `decision_required`, a permission boundary or
an explicit pause. Flow text MUST NOT grant additional authority.

#### Scenario: Structured marker is ambiguous
- **WHEN** `CALL`, `GATE`, `LOOP`, `PARALLEL` or prose permits materially different actions
- **THEN** USW returns `decision_required` rather than a parse error or a guess

### Requirement: Снятый runtime имеет понятную миграцию
USW SHALL reject `--experimental-structured` and retired internal commands
before mutation with guidance to use the ordinary `$usw-run-flow` command.

#### Scenario: Старый structured invocation
- **WHEN** the user supplies `--experimental-structured`
- **THEN** USW tells them to remove the flag and run the same Markdown as text

### Requirement: Legacy FLOW state не используется
USW MUST NOT read, modify or delete `.usw/FLOW.json` and SHALL show at most one
warning about its presence per invocation.

#### Scenario: Legacy state exists
- **WHEN** text execution starts while `.usw/FLOW.json` exists
- **THEN** execution continues through the text path and the legacy file remains unchanged
