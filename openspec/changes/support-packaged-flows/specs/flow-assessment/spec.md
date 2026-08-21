## MODIFIED Requirements

### Requirement: Assessment uses exact safely resolved Markdown
USW SHALL provide a read-only loader applying the execution resolver's
kebab-case, compatible-layout, ambiguity, containment, descriptor-relative
traversal, no-symlink, regular-file and UTF-8 rules. It SHALL return `name`,
`origin`, `identity`, `path`, exact absolute `flow_directory`, exact `markdown`
and `warnings` without execution input. The assessor MUST use only returned
Markdown, MUST NOT reopen `path` or any sibling package resource, and SHALL
report a named package resource as an unverified dependency. Inspection MUST NOT
inspect legacy state, HANDOFF or `.usw/FLOW.json`. Existing flat-flow `resolve`
behavior MUST remain compatible.

#### Scenario: Flow changes after inspection
- **WHEN** the entrypoint changes after exact Markdown and identity are returned
- **THEN** assessment continues from that returned Markdown and identity

#### Scenario: Selected flow traverses a symlink
- **WHEN** an origin root, package directory, intermediate component or final entrypoint is a symlink
- **THEN** inspection stops before semantic assessment

#### Scenario: Packaged flow is inspected
- **WHEN** assessment resolves `<name>/FLOW.md`
- **THEN** its report identifies the exact entrypoint and exact absolute `<flow-root>/<name>` as `flow_directory` without reading sibling resources

#### Scenario: Packaged flow names a sibling resource
- **WHEN** assessed packaged Markdown references `scripts/check.py`
- **THEN** assessment records an unverified dependency without opening that script
