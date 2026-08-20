## MODIFIED Requirements

### Requirement: Один immutable Markdown invocation
For every root or nested invocation, USW SHALL read the selected flow exactly
once, compute identity from the same bytes, decode them as UTF-8 and pass
separate immutable `flow_markdown`, exact absolute `flow_directory` and
`user_input` values to the model. `flow_directory` SHALL identify the selected
entrypoint's containing directory, originate only from the safe resolver, and
SHALL NOT be derived from Markdown or user input. A root
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

#### Scenario: Packaged child flow is prepared
- **WHEN** a nested invocation resolves `<name>/FLOW.md`
- **THEN** the child receives the exact absolute `<flow-root>/<name>` as `flow_directory` without gaining a durable route or additional authority

### Requirement: Безопасное разрешение text flow
USW SHALL resolve only a safe kebab-case name as either `<name>.md` or
`<name>/FLOW.md` inside the selected local or shared root. It MUST check
containment, every existing path component, reject symbolic links and require a
regular final entrypoint before reading. Traversal and the final read SHALL be
descriptor-relative with no pathname re-open after a component is trusted. If
both layouts exist in one selected origin, resolution MUST stop with
`ambiguous_flow_layout`.
The existing Windows flat-flow pathname fallback MAY remain compatible where
descriptor-relative APIs are unavailable, but packaged entrypoints and package
resources MUST stop with `unsupported_safe_flow_platform` on that fallback.

#### Scenario: Intermediate symlink
- **WHEN** any component leading to the selected flat or packaged flow is a symbolic link
- **THEN** USW stops before reading the flow or invoking the model

#### Scenario: Both layouts exist
- **WHEN** one selected origin contains safe flat and packaged entrypoints for the requested name
- **THEN** USW returns `ambiguous_flow_layout` without reading either as the selected invocation

#### Scenario: Windows fallback resolves a legacy flat flow
- **WHEN** descriptor-relative APIs are unavailable and only the compatible `<name>.md` entrypoint exists
- **THEN** USW retains the pre-existing flat-flow fallback and does not extend it to packaged entrypoints or resources
