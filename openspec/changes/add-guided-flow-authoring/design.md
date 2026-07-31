## Context

`usw-create-flow` already saves one safe Markdown file and can optionally offer
analysis afterward. The opt-in offer is easy to miss and gives the model no
bounded recipe library for turning a concrete design gap into an actionable
flow fragment.

## Goals / Non-Goals

**Goals:**

- Make useful design guidance visible after every successful save.
- Keep suggestions concrete, proportional and controlled by the user.
- Cover the most common flow-design gaps with a small recipe library.

**Non-Goals:**

- Automatically revising or executing a flow.
- Discovering skills or flows, building a registry or validating a DSL.
- Requiring every recipe in every flow.

## Decisions

### Scan after the initial save without another opt-in

The requested flow remains the first completed result. A read-only design scan
then returns zero to three suggestions, so creation stays reliable while
guidance becomes visible. A revision does not recursively start another scan.

### Recipes stay inside the skill contract

Seven prose recipes live directly in `SKILL.md`: verification, human decision,
external-action approval, error handling, bounded refinement, independent
checks and explicit capability reuse. A separate parser, data file or selection
algorithm would add machinery without improving model guidance.

### Suggestions are style-aware

Every suggestion contains the gap, its relevance and ready Markdown. The scan
ranks concrete safety and outcome gaps ahead of optional convenience. Ordinary
flows receive ordinary prose. Structured flows may receive `CALL`, `GATE`,
`LOOP` and `PARALLEL`; verification produces evidence before a `GATE` branches
on it.

### Revision remains a separate human choice

The saved file changes only after the user chooses `применить`. Choosing
`изменить` returns a revised fragment for another preview and still performs no
write. Selected revisions preserve origin and authoring style. In this first
version capability reuse is suggested only for a skill that is explicitly named
and present in the current available-skills list. There is no contract discovery
and no `CALL FLOW` suggestion.

## Risks / Trade-offs

- [Suggestions become boilerplate] → Limit them to three concrete gaps and
  report no useful suggestions when none apply.
- [Structured markers become cargo cult] → Require the semantic condition for
  each recipe and provide ordinary prose for ordinary flows.
- [A named skill is unavailable] → Require it to be present in the current
  available-skills list; do not search for or invent another target.
