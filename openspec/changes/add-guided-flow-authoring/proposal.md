## Why

Creating a readable flow still requires the user to recognize missing
verification, decisions, failure paths and safety boundaries. `usw-create-flow`
can reduce that design burden without taking ownership of the final choices.

## What Changes

- Run a short read-only design scan after the initial successful flow save.
- Show at most three applicable suggestions with a reason and ready Markdown.
- Draw suggestions from seven bounded recipes: verification, human decision,
  external-action approval, error handling, bounded refinement, independent
  checks and explicit available-skill reuse.
- Apply only suggestions explicitly selected with `применить`; `изменить`
  produces a new preview without writing.

## Capabilities

### New Capabilities

- `guided-flow-authoring`: Post-save design guidance and human-selected revision
  for ordinary and structured flows.

### Modified Capabilities

None.

## Impact

The change updates only the `usw-create-flow` instruction contract, README and
focused tests. It adds no parser, registry, discovery mechanism, runtime state
or dependency.
