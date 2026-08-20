## ADDED Requirements

### Requirement: Packaged flow has one canonical entrypoint
USW SHALL recognize `<flow-root>/<name>/FLOW.md` as a packaged flow for the safe
kebab-case selector `<name>` and SHALL use that layout for newly created flows.
It SHALL continue to recognize the compatible flat
`<flow-root>/<name>.md` layout.

#### Scenario: Create a new packaged flow
- **WHEN** a safe flow name does not exist in the selected origin and the user creates it
- **THEN** USW writes only `<flow-root>/<name>/FLOW.md` as its entrypoint

#### Scenario: Run an existing flat flow
- **WHEN** only `<flow-root>/<name>.md` exists for the selected name and origin
- **THEN** USW resolves and runs that flat flow without migration

### Requirement: One name has one layout per origin
USW MUST reject a selected origin with `ambiguous_flow_layout` when both
`<flow-root>/<name>.md` and `<flow-root>/<name>/FLOW.md` are runnable
entrypoints. It MUST NOT use layout preference to hide the ambiguity.

#### Scenario: Both entrypoints exist in local flows
- **WHEN** the local flow root contains both layouts for one requested name
- **THEN** resolution stops with `ambiguous_flow_layout` before shared fallback or model execution

### Requirement: Package resources use a contained resolver-owned flow directory
USW SHALL expose the selected entrypoint's exact absolute `flow_directory`
separately from Markdown and input. A relative resource named in packaged
`flow_markdown` SHALL resolve from the resolver-owned directory in that
invocation and MUST be rejected at its use boundary if its path is absolute,
escapes with `..`, traverses a discovered symbolic link, or does not have the
filesystem type required by the requested operation. The same path supplied
only through `user_input` MUST NOT become a package dependency. Resource content
MUST NOT be loaded automatically and MUST NOT grant additional authority. At
explicit use, the boundary MUST read the final regular file through its held
no-follow descriptor, return immutable content and a separate resource identity,
and treat the pathname as report-only metadata that MUST NOT be reopened.

#### Scenario: Packaged flow references a sibling script
- **WHEN** `<name>/FLOW.md` explicitly references `scripts/check.py`
- **THEN** USW reads exact immutable bytes through the held package boundary and applies normal permission boundaries before interpreting or executing them

#### Scenario: Resource escapes its package
- **WHEN** packaged Markdown references `../other-flow/FLOW.md` as a package resource
- **THEN** USW rejects the resource path before reading or executing it

#### Scenario: User input names a package path
- **WHEN** only user input, and not packaged `flow_markdown`, names `scripts/check.py`
- **THEN** USW keeps it as user input and does not treat it as a package dependency

#### Scenario: Flat relative reference remains compatible
- **WHEN** a compatible flat flow contains a relative workspace reference used before packaged-flow support
- **THEN** USW preserves its prior project/workspace-relative interpretation instead of rebasing it to `flow_directory`
