## Context

The initializer currently installs five examples. Only `chat-review` and
`dev-test` encode reusable workflows; the three generic role examples duplicate
ordinary agent behavior.

## Goals / Non-Goals

**Goals:**

- Make initialized flow assets unambiguously educational.
- Install two examples without making them directly executable by name.
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

### Keep current project flows and packaged examples synchronized

The packaged `chat-review` and `dev-test` examples copy the current shared flow
content after adding the standard example notice. Tests compare the example
body with the project-owned source so later edits cannot silently drift.

### Preserve legacy files additively

The initializer replaces its expected inventory but never removes files.
Existing workspaces therefore keep previously installed examples; fresh
workspaces receive only the two retained examples.

## Risks / Trade-offs

- [Existing projects retain removed examples] → Document that re-init is
  create-only and cleanup is a user decision.
- [Duplicated chat-review/dev-test assets can drift] → Add an exact parity test
  after stripping the standard example notice.
- [Users may expect examples to run in place] → Use a nested non-resolvable path
  and repeat copy-before-use guidance in every file and README.

## Migration Plan

1. Ship the new packaged example inventory.
2. New initialization creates only the two nested examples.
3. Re-initialization creates missing examples and preserves all old files.
4. Rollback restores the previous package inventory without deleting examples
   already created in user projects.

## Open Questions

None. The owner selected `chat-review` and `dev-test` and create-only
preservation for existing project files.
