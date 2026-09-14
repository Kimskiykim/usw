## Why

USW flows are currently limited to one Markdown file directly under a flow
root, so a flow cannot own scripts, references, or assets with stable relative
paths. Adding a skill-like package layout lets one named flow remain a single
discoverable unit while carrying the resources needed to execute it.

## What Changes

- Add `<flow-root>/<name>/FLOW.md` as the canonical layout for newly created
  flows, with sibling `scripts/`, `references/`, `assets/`, or other resources.
- Keep existing `<flow-root>/<name>.md` flows runnable and editable without
  migration.
- Resolve package-relative resource references from an explicit resolver-owned
  `flow_directory` supplied with the immutable flow invocation, without
  changing relative-path semantics of compatible flat flows.
- Detect and reject an origin that contains both layouts for the same name
  instead of choosing one silently.
- Extend safe execution, inspection, assessment, and discovery to packaged
  flows without recursive catalog traversal or symlink following.
- Preserve local-first origin selection and all existing permission boundaries.

## Capabilities

### New Capabilities

- `packaged-flow-layout`: Defines the skill-like flow directory, canonical
  `FLOW.md` entrypoint, resource base directory, compatibility, and ambiguity
  rules.

### Modified Capabilities

- `text-flow-execution`: Resolve either compatible layout safely and expose the
  selected flow directory to root and nested invocations.
- `local-custom-flows`: Create new flows as packages, edit either existing
  layout in place, and preserve local-first selection.
- `flow-discovery`: Discover direct packaged flows alongside direct flat
  Markdown flows without arbitrary recursive traversal.
- `flow-assessment`: Inspect and report packaged flows through the same exact
  safe resolver and immutable invocation data.
- `guided-flow-authoring`: Preserve the selected flat or packaged layout when
  applying an approved post-creation revision.

## Impact

- `skills/usw-run-flow/scripts/run_flow.py` and its CLI JSON contracts.
- Authoring, finder, assessor, and runner skill instructions.
- Flow resolver, package-layout, and skill-contract tests.
- README and normative OpenSpec documentation.
- No new dependency, migration, parser, recursive registry, or additional
  execution authority is introduced.
