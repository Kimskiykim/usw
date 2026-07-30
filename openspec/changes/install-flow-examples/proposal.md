## Why

The package currently installs five flow examples, but the generic Analysis,
Development and Testing documents duplicate normal agent behavior without
providing a distinct reusable workflow.

## What Changes

- Package only `chat-review` and `dev-test` as explicitly non-normative
  examples under `<flows.root>/examples/`.
- State in every example that it is not executed in place and must be copied to
  `<flows.root>/<name>.md` and adapted before use.
- Preserve all existing project files; initialization never removes examples
  already copied into a project.

## Capabilities

### New Capabilities

- `flow-examples`: Defines the two packaged, non-normative flow examples and
  their copy-before-use contract.

### Modified Capabilities

- `project-initialization`: Reduces the exact provider-specific inventory to
  two nested examples.
- `flow-orchestration`: Separates optional project-owned executable role
  scenarios from examples installed by initialization.

## Impact

- Initializer Python and LLM fallback inventory.
- Packaged flow templates and package-layout checks.
- README initialization tree and flow documentation.
- Initialization, package-layout, flow and end-to-end tests.
