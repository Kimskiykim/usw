## MODIFIED Requirements

### Requirement: Revision remains human-controlled
`usw-create-flow` MUST change the saved flow only after the user explicitly
selects a suggestion and MUST preserve the selected origin, authoring style,
and flat or packaged entrypoint layout.

#### Scenario: User selects one suggestion
- **WHEN** three suggestions are shown and the user applies only one
- **THEN** only that revision is written to the existing entrypoint and the other suggestions have no effect

#### Scenario: User asks to change a suggestion
- **WHEN** the user chooses `изменить`
- **THEN** the skill previews a revised fragment and does not write until a
  later explicit `применить`

#### Scenario: User skips all suggestions
- **WHEN** the user selects no proposed revision
- **THEN** the saved flow remains byte-for-byte unchanged

#### Scenario: Packaged flow receives a revision
- **WHEN** an approved suggestion applies to `<name>/FLOW.md`
- **THEN** the skill updates that `FLOW.md` and does not create or rewrite `<name>.md`
