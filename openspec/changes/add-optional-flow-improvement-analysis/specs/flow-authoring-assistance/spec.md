## ADDED Requirements

### Requirement: Requested flow is completed before optional analysis
`usw-create-flow` SHALL first create or update the requested flow, perform the
applicable validation, and present the result without adding unrequested
improvements. It MUST NOT prepare or claim a set of improvement ideas before
the user opts into a separate analysis.

#### Scenario: Flow creation succeeds
- **WHEN** the requested flow has been written and validated
- **THEN** the skill reports the created result before offering any improvement analysis

#### Scenario: Flow creation fails
- **WHEN** creation or validation does not complete successfully
- **THEN** the skill reports the failure without offering analysis of a completed flow

### Requirement: Improvement analysis uses a neutral opt-in
After a successful result, `usw-create-flow` SHALL offer to study the flow and
propose possible improvements. The invitation MUST describe analysis as future
work and MUST NOT state that ideas already exist.

#### Scenario: Skill offers follow-up analysis
- **WHEN** the created or revised flow has been reported successfully
- **THEN** the skill asks whether it may separately study the flow and propose possible improvements

#### Scenario: User declines analysis
- **WHEN** the user declines or does not authorize the optional analysis
- **THEN** the skill returns without generating recommendations or changing the flow

### Requirement: Analysis is proportional and read-only
After explicit analysis consent, `usw-create-flow` SHALL inspect the flow for
applicable improvements and present recommendations before any revision. Each
recommendation MUST identify a concrete risk or missing outcome. The analysis
SHALL consider verification and review explicitly when the flow creates new
artifacts or relies on reasoning to make decisions, and SHALL consider HITL,
complete branches, bounded feedback loops, escalation, and resumability when
relevant.

#### Scenario: Creative or reasoning-heavy flow is analyzed
- **WHEN** the authorized analysis examines a flow that creates a new artifact or makes a reasoning-dependent decision
- **THEN** it evaluates whether verification or independent review would reduce a concrete risk

#### Scenario: Checklist item is not applicable
- **WHEN** a verification, review, HITL, branch, loop, escalation, or resume mechanism does not address a concrete flow risk
- **THEN** the skill does not recommend that mechanism merely to satisfy a checklist

#### Scenario: Recommendations are presented
- **WHEN** the authorized analysis finds possible improvements
- **THEN** the skill presents them without changing the saved flow

### Requirement: Revision requires separate selection
`usw-create-flow` MUST revise the flow after analysis only when the user
explicitly selects or approves recommendations. The revision SHALL include only
the approved changes and SHALL repeat the validation applicable to the selected
flow mode.

#### Scenario: User selects some recommendations
- **WHEN** the user approves only a subset of presented improvements
- **THEN** the skill applies only that subset and validates the revised flow

#### Scenario: User rejects all recommendations
- **WHEN** the user rejects all presented improvements
- **THEN** the skill leaves the saved flow unchanged

### Requirement: Existing authoring boundaries remain active
The optional analysis and revision phases SHALL preserve shared/local root
selection, ordinary/structured mode selection, path safety, write scope, and
the prohibition on executing the created flow.

#### Scenario: Structured flow is revised after analysis
- **WHEN** the user approves an improvement to a structured flow
- **THEN** the skill preserves structured mode and runs the experimental structured validator without executing the flow

#### Scenario: Ordinary flow is revised after analysis
- **WHEN** the user approves an improvement to an ordinary Markdown flow
- **THEN** the skill preserves ordinary Markdown without introducing structured syntax solely for validation
