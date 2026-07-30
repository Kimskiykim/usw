## Context

The current router searches flows, decides whether a flow is useful, may author
one, waits for approval and then runs it. Existing `usw-create-flow` and
`usw-run-flow` already own authoring and execution, so the router duplicates
their coordination while remaining an explicit command.

## Goals / Non-Goals

**Goals:**

- Give one explicit intent a read-only lookup over existing runnable flows.
- Reuse the runner's configuration and safe resolution rules.
- Return enough information for the user to invoke the selected flow directly.

**Non-Goals:**

- Classifying task complexity.
- Creating, adapting or executing flows.
- Searching packaged examples, external catalogs or other projects.
- Adding an index, parser, score, registry or runtime state.

## Decisions

### Finder is a terminal read-only capability

`usw-find-flow` returns after `match`, `ambiguous` or `no-match`. It never
delegates to another skill. This keeps discovery separate from the existing
authoring and execution capabilities and removes the router's approval state.

### Search only runnable project flows

Discovery enumerates direct safe `*.md` entries in developer-local and
configured shared roots. It compares names first and loads only plausible
candidates through the existing safe resolver. Packaged examples are excluded
because they are authoring inputs, not runnable flows.

### Model-driven semantic match remains visible

The model compares the supplied intent with candidate Markdown. A unique match
returns its name, origin, path, rationale and an explicit-origin
`usw-run-flow` command. Materially tied candidates return `ambiguous`; no
candidate causes creation or adaptation.

### Old router is removed on forced installation

The package and command are renamed without an alias. `install.sh --force`
removes installed `usw-route-task` files so obsolete behavior does not remain
beside the finder.

## Risks / Trade-offs

- [Model matching may vary] → Expose the rationale and stop on material ties.
- [Large catalogs consume context] → Inspect names first and load only plausible
  candidates; add indexing only after a measured need.
- [Breaking command rename] → Document the direct replacement and remove the old
  installed files only during explicit forced installation.
