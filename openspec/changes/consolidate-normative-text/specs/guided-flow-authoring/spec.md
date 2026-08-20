## MODIFIED Requirements

### Requirement: Successful creation includes a bounded design scan
After the initial save and report of the requested flow, `usw-create-flow` SHALL
automatically perform one read-only design scan. The scan SHALL read the recipe
catalog `references/recipes.md` first and select, by the catalog's stated
conditions, no more than three most relevant recipes, ranking gaps in safety and
result verifiability first. The skill SHALL read only the selected recipes'
files under `references/recipes/`; other applicable recipes SHALL be named in a
single line from the catalog without reading their files. After an explicitly
selected revision the design scan MUST NOT run again.

#### Scenario: Flow has several design gaps
- **WHEN** more than three recipes could improve a saved flow
- **THEN** the skill returns the three most relevant suggestions without
  changing the file, and reads only those three recipe files

#### Scenario: Flow has no concrete design gap
- **WHEN** none of the recipes addresses a concrete risk or missing outcome
- **THEN** the skill reports that there are no useful suggestions and returns

#### Scenario: More recipes apply than the scan may detail
- **WHEN** applicable recipes remain beyond the selected three
- **THEN** the skill names them in one line each, without detail and without
  reading their files

#### Scenario: A revision was applied
- **WHEN** the user selects a suggestion and the revision is written
- **THEN** the skill does not start another design scan

### Requirement: Suggestions use a bounded recipe library
The design scan SHALL select only from the recipe catalog
`references/recipes.md`, which covers result verification, human decision,
external-action approval, error handling, bounded refinement, independent
checks, subagent review, subagent orchestration, escalation, variant selection,
input preflight, list processing, external event wait, adaptive intensity and
explicit capability reuse. A recipe SHALL be suggested only when its catalog
condition holds for the saved flow, and MUST NOT be recommended merely for
completeness.

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

#### Scenario: Control intensity adapts to risk
- **WHEN** a suggested flow varies its control intensity by declared risk
  signals
- **THEN** the signals are observable facts, mandatory confirmation of an
  irreversible external action is not disabled at any level, and uncertain
  signals select the higher level

### Requirement: Every suggestion is actionable
Each suggestion MUST identify what to add, explain why it matters to the saved
flow and provide ready Markdown with `применить`, `изменить` and `пропустить`
choices. When a fragment is rendered in ordinary prose from a recipe whose
example carries backticked contract tokens — statuses and decision options the
human types back — those tokens SHALL be kept verbatim rather than translated.

#### Scenario: Ordinary flow receives guidance
- **WHEN** the saved flow uses ordinary Markdown
- **THEN** the proposed fragment uses ordinary prose without structured markers

#### Scenario: Structured flow receives guidance
- **WHEN** the saved flow uses structured authoring
- **THEN** the proposed fragment MAY use only applicable `CALL`, `GATE`, `LOOP`
  and `PARALLEL` markers

#### Scenario: A recipe's contract tokens survive prose conversion
- **WHEN** a recipe example's backticked tokens such as `approve`, `change` and
  `cancel` are embedded into an ordinary flow
- **THEN** the tokens stay verbatim while the surrounding markers become plain
  prose

### Requirement: Revision remains human-controlled
`usw-create-flow` MUST change the saved flow only after the user explicitly
selects a suggestion and MUST preserve the selected origin and authoring style.

#### Scenario: User selects one suggestion
- **WHEN** three suggestions are shown and the user applies only one
- **THEN** only that revision is written and the other suggestions have no
  effect

#### Scenario: User asks to change a suggestion
- **WHEN** the user chooses `изменить`
- **THEN** the skill previews a revised fragment, explicitly re-offers
  `применить`, `изменить` and `пропустить` for it, and does not write until a
  later explicit `применить`

#### Scenario: User skips all suggestions
- **WHEN** the user selects no proposed revision
- **THEN** the saved flow remains byte-for-byte unchanged

## ADDED Requirements

### Requirement: Designing from a goal is agreed before writing
When the user describes a goal rather than ready steps, `usw-create-flow` SHALL
read the recipe catalog first, propose a draft of linear numbered happy-path
steps, and name only the blocks whose catalog conditions genuinely hold for the
goal, each with a one-sentence reason. The structure MUST be agreed with the
user before writing. Agreed blocks SHALL be embedded into the written flow from
their recipe files; rejected blocks MUST NOT be embedded.

#### Scenario: Some blocks are agreed and some rejected
- **WHEN** the user approves part of the proposed blocks and rejects the rest
- **THEN** the written flow embeds every approved block and none of the
  rejected ones

#### Scenario: An ordinary flow is designed from a goal
- **WHEN** the flow being written is ordinary Markdown
- **THEN** embedded blocks use plain numbered prose without `CALL`, `GATE`,
  `LOOP` or `PARALLEL` markers

#### Scenario: The goal needs no structural blocks
- **WHEN** no catalog condition holds for the described goal
- **THEN** the draft remains linear and no block is proposed for completeness

### Requirement: Complexity signals warn without blocking
`usw-create-flow` SHALL check the flow text before writing and during the
design scan against declared complexity signals: more than about twelve steps
at one level, a `GATE` with more than four branches, a `LOOP` inside a `LOOP`
or containing `PARALLEL` or another flow call, a `PARALLEL` with more than
three or with dependent branches, and implicit "return to step N" transitions.
On any signal the skill SHALL warn that the flow may execute unreliably,
propose one concrete simplification and recommend running
`$usw-assess-flow [--local|--shared] <name>` after saving. The write MUST NOT
be blocked: the decision stays with the user.

#### Scenario: An overloaded draft is submitted
- **WHEN** the flow text triggers a complexity signal before writing
- **THEN** the skill warns, proposes a concrete simplification, recommends
  `$usw-assess-flow`, and still writes the flow if the user keeps it

#### Scenario: No signal is present
- **WHEN** the flow text triggers no complexity signal
- **THEN** the skill writes without a complexity warning
