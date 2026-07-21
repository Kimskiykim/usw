## Why

Custom flows are currently always stored in the shared configured `flows.root`,
so developers cannot keep personal or experimental flows outside Git without
changing project configuration. USW already reserves `.usw/` for developer-local
state, making `.usw/flows/` the natural explicit local location.

## What Changes

- Add `--local` and `-l` selectors to custom-flow creation and execution.
- Store and load selected local custom flows from `.usw/flows/<name>.md`.
- Preserve the current configured `flows.root` behavior when neither flag is used.
- Reject local selection for standard Analysis, Development, and Testing flows.
- Carry the selected shared/local origin through validation and resume identity.

## Capabilities

### New Capabilities

- `local-custom-flows`: Explicit creation, validation, execution, and resume of developer-local custom flows.

### Modified Capabilities

None.

## Impact

The change affects the `usw-create-flow` and `usw-run-flow` skill contracts,
the custom-flow loader/validator, local-state initialization behavior, tests, and
README examples. It adds no dependency or `usw.yaml` field.
