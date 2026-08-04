# guided-flow-authoring Specification

## Purpose
Define bounded, human-controlled design guidance applied after a Markdown flow
is created, without silently changing the saved flow or inventing capabilities.

## Requirements

### Requirement: Successful creation includes a bounded design scan
After the initial save and report of the requested flow, `usw-create-flow` SHALL
automatically perform a read-only design scan and return no more than three
applicable suggestions.

#### Scenario: Flow has several design gaps
- **WHEN** more than three recipes could improve a saved flow
- **THEN** the skill returns the three most relevant suggestions without
  changing the file

#### Scenario: Flow has no concrete design gap
- **WHEN** none of the recipes addresses a concrete risk or missing outcome
- **THEN** the skill reports that there are no useful suggestions and returns

### Requirement: Suggestions use a bounded recipe library
The design scan SHALL consider verification, human decision, external-action
approval, error handling, bounded refinement, independent checks and explicit
capability reuse, and MUST NOT recommend a recipe merely for completeness.

#### Scenario: Result is not verified
- **WHEN** a flow can complete without an observable check of its result
- **THEN** the skill suggests a verification step and, only if outcomes require
  different actions, a decision gate after that verification

#### Scenario: Retry has no safety contract
- **WHEN** repetition could help but no exit criterion, attempt limit or safe
  repeat behavior is known
- **THEN** the skill does not suggest an unbounded or automatic retry

#### Scenario: Repeated work has an external side effect
- **WHEN** a candidate refinement would repeat an external write or other
  non-idempotent action
- **THEN** the skill keeps that action and its approval outside the loop

#### Scenario: Checks are not independent
- **WHEN** candidate checks depend on one another or have overlapping writes
- **THEN** the skill does not suggest parallel execution

### Requirement: Every suggestion is actionable
Each suggestion MUST identify what to add, explain why it matters to the saved
flow and provide ready Markdown with `применить`, `изменить` and `пропустить`
choices.

#### Scenario: Ordinary flow receives guidance
- **WHEN** the saved flow uses ordinary Markdown
- **THEN** the proposed fragment uses ordinary prose without structured markers

#### Scenario: Structured flow receives guidance
- **WHEN** the saved flow uses structured authoring
- **THEN** the proposed fragment MAY use only applicable `CALL`, `GATE`, `LOOP`
  and `PARALLEL` markers

### Requirement: Capability reuse requires an explicitly available skill
The skill MUST suggest `CALL SKILL` only when the user or current flow explicitly
names a skill present in the current available-skills list. It MUST NOT discover
contracts or suggest `CALL FLOW` in this version.

#### Scenario: No capability is named
- **WHEN** a flow contains a generic step without an explicitly named skill from
  the current available-skills list
- **THEN** the skill does not discover, invent or recommend a skill target

### Requirement: Revision remains human-controlled
`usw-create-flow` MUST change the saved flow only after the user explicitly
selects a suggestion and MUST preserve the selected origin and authoring style.

#### Scenario: User selects one suggestion
- **WHEN** three suggestions are shown and the user applies only one
- **THEN** only that revision is written and the other suggestions have no
  effect

#### Scenario: User asks to change a suggestion
- **WHEN** the user chooses `изменить`
- **THEN** the skill previews a revised fragment and does not write until a
  later explicit `применить`

#### Scenario: User skips all suggestions
- **WHEN** the user selects no proposed revision
- **THEN** the saved flow remains byte-for-byte unchanged
