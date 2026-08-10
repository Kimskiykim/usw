# intent-clarification Specification

## Purpose
Define intent clarification as an ordinary adaptable Markdown-flow rather than
an installed backend skill.

## Requirements

### Requirement: Intent clarification is a packaged example flow
USW SHALL package `refine-intent.md` under `<flows.root>/examples/`. It SHALL
clarify at most one material decision per user turn and MUST NOT start planning
or implementation.

#### Scenario: User copies the example
- **WHEN** the user copies `refine-intent.md` to a runnable flow path
- **THEN** the flow can be adapted and executed through the ordinary
  `usw-run-flow` path without a `usw-refine-intent` skill or command

### Requirement: Clarification state is local and minimal
The example SHALL use one developer-local Markdown file under
`.usw/refinements/` for confirmed facts, assumptions, open questions,
decisions and the current formulation. It MUST NOT treat that file as backlog,
specification, planning state or evidence of completed implementation.

#### Scenario: One decision is confirmed
- **WHEN** the user unambiguously answers the current question
- **THEN** the flow records that decision before selecting at most one next
  material question

#### Scenario: A decision is revised
- **WHEN** the user replaces an earlier decision
- **THEN** the prior decision remains visible as `superseded`

### Requirement: Clarification may stop independently
The flow SHALL allow a completed formulation, a human decision request or an
unresolved stop without requiring another flow.

#### Scenario: Formulation is sufficient
- **WHEN** no material questions remain
- **THEN** the flow records the current formulation, returns its local reference
  and completes without choosing downstream work

### Requirement: Removed skill state is preserved
Installation with `--force` SHALL remove the obsolete
`usw-refine-intent` skill and command but MUST NOT delete existing
`.usw/refinements/` artifacts.

#### Scenario: Existing refinement notes are present
- **WHEN** USW is upgraded after the skill is removed
- **THEN** installed skill metadata is cleaned up and project-local notes remain
  unchanged
