## Context

The initializer currently installs three root-level files using the legacy role
scenario schema. The current public runner defaults to ordinary Markdown and
does not route those files through the role-scenario validator. Two useful
project-owned flows, `chat-review` and `dev-test`, are not installed at all.

## Goals / Non-Goals

**Goals:**

- Make initialized flow assets unambiguously educational.
- Install five examples without making them directly executable by name.
- Align Python initialization, LLM fallback, README, specs and tests.
- Preserve every existing project file, including legacy role scenarios.

**Non-Goals:**

- Removing the legacy role-scenario parser or one-action engine.
- Migrating or deleting existing project flows.
- Automatically enabling or executing any example.
- Changing local custom-flow behavior.

## Decisions

### Store examples in a nested directory

Examples live under `<flows.root>/examples/`. The runner accepts a flat safe
kebab-case name and resolves `<name>.md`, so nested examples cannot be selected
accidentally. Keeping them under the configured flow root still makes them easy
to discover.

Alternative: keep examples at the root with an `example-` prefix. Rejected
because they would remain directly executable and the label would be the only
guard against confusing guidance with a supported contract.

### Use ordinary Markdown and explicit copy-before-use notices

The three role examples are rewritten as concise human guidance. Every file
starts with the same non-normative notice and tells the user to copy it to a
flat flow filename before adapting and running it.

Alternative: retain the legacy Purpose/Inputs/Branches schema. Rejected because
that schema is precisely what currently overstates runtime enforcement.

### Keep current project flows and packaged examples synchronized

The packaged `chat-review` and `dev-test` examples copy the current shared flow
content after adding the standard example notice. Tests compare the example
body with the project-owned source so later edits cannot silently drift.

### Preserve legacy files additively

The initializer replaces its expected inventory but never removes old
`flow-scenario-*` files. Existing workspaces therefore keep user-owned content;
fresh workspaces receive only the five examples.

## Risks / Trade-offs

- [Existing projects retain obsolete-looking files] → Document that re-init is
  create-only and legacy cleanup is a user decision.
- [Duplicated chat-review/dev-test assets can drift] → Add an exact parity test
  after stripping the standard example notice.
- [Users may expect examples to run in place] → Use a nested non-resolvable path
  and repeat copy-before-use guidance in every file and README.

## Migration Plan

1. Ship the new packaged example inventory.
2. New initialization creates only the five nested examples.
3. Re-initialization creates missing examples and preserves all old files.
4. Rollback restores the previous package inventory without deleting examples
   already created in user projects.

## Open Questions

None. The owner selected five non-normative examples and create-only legacy
preservation.
