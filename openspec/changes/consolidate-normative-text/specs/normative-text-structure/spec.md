## ADDED Requirements

### Requirement: One normative source
USW SHALL keep exactly one normative statement of each rule. `openspec/specs/`
is that source. README SHALL be an overview that links to it, and skill files
SHALL be derived instructions for an executor rather than a second specification.
A rule stated in more than one place MUST be reduced to one, with the others
referring to it.

#### Scenario: A rule changes
- **WHEN** a normative rule is added or altered
- **THEN** it is edited in exactly one file, and no other file restates it in a form that can drift

#### Scenario: A reader needs the authoritative wording
- **WHEN** documentation and a skill appear to disagree
- **THEN** the specification is authoritative and the skill is corrected to match it

### Requirement: Skill files lead with the imperative
Each shipped skill SHALL state what to do first, in short imperative form.
Rationale, edge cases, recipes and worked examples SHALL live in `references/`
and be read on demand. A skill file MUST NOT depend on the reader having
absorbed a preceding wall of qualifications before reaching the instruction.

#### Scenario: An executor reads a skill
- **WHEN** a model invokes a skill
- **THEN** the actions it must take are stated before any justification for them

#### Scenario: A rule needs a long justification
- **WHEN** a rule requires extended explanation to be understood
- **THEN** the explanation goes to `references/` and the skill keeps the rule itself

### Requirement: Meaning is protected by measurement, not by phrase assertions
Tests over instruction text SHALL assert only anchors that are stable by
construction: command names, error codes, file paths and structural markers. A
test MUST NOT assert that a particular sentence appears, because that pins the
wording and prevents the text from being made clearer. Invariants about what a
model must do SHALL be covered by behavior scenarios instead. A phrase assertion
MUST NOT be removed until the invariant it stood for is covered by a scenario.

#### Scenario: Wording improves without meaning changing
- **WHEN** an instruction is rewritten more briefly with its meaning intact
- **THEN** the deterministic suite still passes

#### Scenario: An invariant loses its phrase assertion
- **WHEN** a phrase-level assertion is withdrawn
- **THEN** a behavior scenario covering the same invariant exists first

### Requirement: The normative layer uses one language
The normative body of skills, specifications and README SHALL be Russian. A
single file MUST NOT mix languages within its normative body. Established
technical terms, command names, error codes and identifiers stay in their
original form. Frontmatter `description` fields are harness metadata rather than
normative body and are out of scope.

#### Scenario: A skill written in another language is found
- **WHEN** a shipped skill's body is not Russian
- **THEN** it is translated, keeping command names, error codes and identifiers unchanged

#### Scenario: A rule needs a technical term
- **WHEN** a rule refers to a command, error code or identifier
- **THEN** that token keeps its original form rather than being translated

### Requirement: Restructuring does not change behavior
This restructuring SHALL preserve every rule it moves. A behavior difference
observed during it is a defect to be corrected, not an improvement to be kept.
Behavior scenarios SHALL be measured before and after, and a rate that drops
MUST be investigated before the change proceeds.

#### Scenario: Text is restructured
- **WHEN** a skill is rewritten under this change
- **THEN** its observed scenario rates are measured before and after and are reported together
