# flow-authoring-assistance Specification

## Purpose
Define optional analysis and revision after a flow is safely authored.

## Requirements

### Requirement: Requested flow is completed before optional analysis
`usw-create-flow` SHALL first create or update the requested Markdown and report
the result without adding unrequested improvements. It MUST NOT execute the flow.

#### Scenario: Flow creation succeeds
- **WHEN** the selected safe file has been written and read back
- **THEN** the skill reports the created result before offering analysis

#### Scenario: Flow creation fails
- **WHEN** creation does not complete successfully
- **THEN** the skill reports the failure without describing a completed result

### Requirement: Improvement analysis uses a neutral opt-in
After a successful result, `usw-create-flow` MAY offer to study the flow and
propose improvements. It MUST NOT claim that recommendations already exist or
change the file without consent.

#### Scenario: User declines analysis
- **WHEN** the user declines or does not authorize optional analysis
- **THEN** the skill returns without recommendations or additional writes

### Requirement: Analysis is proportional and read-only
After explicit consent, analysis SHALL identify only concrete risks or missing
outcomes and present recommendations before revision. It MAY consider
verification, review, HITL, complete branches, bounded loops, escalation and
resumability when relevant.

#### Scenario: Checklist item is not applicable
- **WHEN** a mechanism does not address a concrete risk
- **THEN** the skill does not recommend it merely for completeness

### Requirement: Revision requires separate selection
The skill MUST apply only recommendations explicitly selected by the user and
MUST preserve the selected origin and ordinary/structured authoring style.

#### Scenario: User selects some recommendations
- **WHEN** only a subset is approved
- **THEN** only that subset is written to the same safe flow file

### Requirement: Structured authoring не запускает validator
Authoring SHALL check only safe selection, successful Markdown persistence and
obvious readability. It MUST NOT invoke the retired runtime or validator.

#### Scenario: Structured revision сохранена
- **WHEN** a `version-2` revision is complete
- **THEN** the report offers an ordinary text-first run without an experimental flag
