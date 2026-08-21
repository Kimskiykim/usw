## MODIFIED Requirements

### Requirement: Безопасное разрешение text flow
USW SHALL resolve only a safe kebab-case name inside the selected local or
shared root. It MUST check containment, every existing path component, reject
symbolic links and require a regular final file before reading. Traversal and
the final read SHALL go through the shared safe-access boundary, which is
descriptor-relative with no pathname re-open after a component is trusted on
platforms that support `dir_fd`, and pathname-based with per-component reparse
point rejection and re-verified containment on platforms that do not. Both flow
layouts and packaged resources SHALL resolve on every supported platform;
`unsupported_safe_flow_platform` MUST NOT be the ordinary outcome of resolving a
packaged flow on a supported platform.

#### Scenario: Intermediate symlink
- **WHEN** any component leading to the selected flow is a symbolic link
- **THEN** USW stops before reading the flow or invoking the model

#### Scenario: Packaged flow on a platform without descriptor-relative access
- **WHEN** a packaged `<name>/FLOW.md` is resolved on a supported platform that lacks `dir_fd`
- **THEN** USW resolves it through the pathname-based backend and returns the same name, origin, identity, path, flow directory and exact Markdown as it would elsewhere

#### Scenario: Packaged resource on a platform without descriptor-relative access
- **WHEN** packaged Markdown names a sibling resource on such a platform
- **THEN** the resource is read through the same boundary, bound to the original flow identity and entrypoint, and rejected on any link, escape or unexpected filesystem type
