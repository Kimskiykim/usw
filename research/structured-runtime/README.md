# Structured runtime research snapshot

This directory preserves the unsupported structured-runtime experiment as it
existed when production USW moved to text-first Markdown execution.

It includes the parser, typed executors, gates, loops, parallel execution,
bindings, JSON checkpoints, role-scenario validator, specialized tests and the
superseded `add-result-list-iteration` and `implement-nested-flow-runtime`
changes. The snapshot also preserves the in-progress run-scoped UUID checkpoint
work that was present in the working tree.

The superseded role-authorized planning-artifact and review-receipt writer is
preserved under `legacy/usw-manage-artifacts/` with its contract validator under
`runtime/artifact_contract.py`. It is not a production skill and is not
installed by the default installer.

Nothing under this directory is installed, imported by production code,
normative for current USW behavior or included in the main test discovery.
Tests are preserved as historical material and are not guaranteed to run from
their relocated paths.

The production roadmap may use this material as input to a future compiler or
iterator proposal. Such a proposal must define a derived machine
representation, explicit input, durable state and a next-step or terminal
outcome API; this snapshot does not establish those contracts.
