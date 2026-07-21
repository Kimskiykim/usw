## Context

`flows.root` is the shared, project-configured source of standard and custom
flows. `.usw/` is already the ignored developer-local state boundary, but the
custom-flow skills do not currently expose a way to select it.

## Goals / Non-Goals

**Goals:**

- let developers explicitly create and run custom flows in `.usw/flows/`;
- preserve every existing shared-flow invocation;
- keep local and shared flows deterministic even when their names match;
- prevent a resumed operation from switching between local and shared origins.

**Non-Goals:**

- configuring another local root in `usw.yaml`;
- searching both roots or defining shadowing precedence;
- allowing local variants of the three standard role scenarios;
- migrating existing shared flows.

## Decisions

### Explicit selector instead of multi-root discovery

Both `usw-create-flow` and `usw-run-flow` accept equivalent `--local` and `-l`
selectors. Without a selector they retain the configured `flows.root`; with a
selector they use exactly `<project>/.usw/flows`. The runner never searches the
other root.

This avoids name precedence, ambiguity handling, and accidental execution of a
personal flow when a shared flow was intended.

### Fixed local path instead of configuration

The local root is a convention under the existing `.usw` boundary. No
`local_root` field is added to `usw.yaml`, because user-specific paths do not
belong in shared configuration and there is only one supported local location.

### Origin is part of flow identity

A loaded custom flow records `shared` or `local`, and the origin participates in
its resume identity. Equal bytes and names in the two roots therefore remain
different flows for HANDOFF/checkpoint validation.

### Standard role flows remain shared

Local selection is valid only for named custom flows. Analysis, Development,
and Testing continue to load exclusively from configured `flows.root` so a
developer-local file cannot invisibly change the team lifecycle.

## Risks / Trade-offs

- [A local directory or file is symlinked] → apply the same regular-file and
  no-symlink checks used by existing local state before creation or execution.
- [Users forget the selector on resume] → persist the origin in flow identity
  and report a stale/different-flow boundary instead of switching roots.
- [Two roots contain the same name] → explicit selection makes both valid and
  removes the need for shadowing rules.
