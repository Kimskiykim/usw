# text-flow-execution Specification

## Purpose
Define the single production path for model-executed Markdown flows.

## Requirements

### Requirement: Один immutable Markdown invocation
For every root or nested invocation, USW SHALL read the selected flow exactly
once, compute identity from the same bytes, decode them as UTF-8 and pass
separate immutable `flow_markdown` and `user_input` values to the model. A root
invocation SHALL additionally receive its own execution identity. A nested
invocation SHALL additionally receive its parent root execution identity and
branch label as separate execution context that flow Markdown and user input
cannot replace.

#### Scenario: Flow changes after loading
- **WHEN** the file changes after a root or nested invocation has been prepared
- **THEN** the invocation uses the already loaded Markdown and its original identity

#### Scenario: Child input contains a root identity
- **WHEN** ordinary child input includes text resembling nested execution context
- **THEN** it remains user input and does not select nested execution or another routed operation

#### Scenario: Concurrent roots load the same flow
- **WHEN** two root operations resolve the same flow and input independently
- **THEN** each model invocation receives its own execution identity and the same immutable loaded Markdown bytes

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

### Requirement: Root and nested execution preserve the same authority boundary
USW SHALL apply the same flow-text, ambiguity and permission rules to every
concurrent root and nested model execution. Root operation identity and nested
context MUST NOT grant file-write, external, destructive or other
permission-bound authority.

#### Scenario: Nested Markdown requests an unauthorized action
- **WHEN** a nested flow requests an action outside the available authority
- **THEN** the child returns `decision_required` to its root executor without performing the action

#### Scenario: Concurrent root requests an unauthorized action
- **WHEN** one concurrent root flow requests an action outside the available authority
- **THEN** only that root reaches `decision_required` and no authority is inferred from another operation
