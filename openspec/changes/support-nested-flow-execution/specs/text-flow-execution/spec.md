## MODIFIED Requirements

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

## ADDED Requirements

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
