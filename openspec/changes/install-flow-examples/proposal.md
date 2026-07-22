## Why

Fresh initialization currently installs three role-scenario files into the
executable flow namespace even though the current default runner treats them as
ordinary Markdown and does not enforce their legacy scenario contract. This
makes examples look normative and runnable under semantics they no longer have.

## What Changes

- Replace the three root-level `flow-scenario-*` initializer outputs with five
  explicitly non-normative examples under `<flows.root>/examples/`.
- Rewrite the Analysis, Development and Testing examples as ordinary Markdown
  guidance compatible with the current default flow model.
- Package the current `chat-review` and `dev-test` flows as two additional
  examples.
- State in every example that it is not executed in place and must be copied to
  `<flows.root>/<name>.md` and adapted before use.
- Preserve all existing project files, including legacy `flow-scenario-*`
  files; initialization never migrates or deletes them.

## Capabilities

### New Capabilities

- `flow-examples`: Defines the five packaged, non-normative flow examples and
  their copy-before-use contract.

### Modified Capabilities

- `project-initialization`: Changes the exact provider-specific inventory from
  three executable-looking role scenarios to five nested examples.
- `flow-orchestration`: Separates optional project-owned executable role
  scenarios from examples installed by initialization.

## Impact

- Initializer Python and LLM fallback inventory.
- Packaged flow templates and package-layout checks.
- README initialization tree and flow documentation.
- Initialization, flow-scenario and end-to-end tests that currently assume the
  three root-level role-scenario files are created.
