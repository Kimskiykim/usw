## MODIFIED Requirements

### Requirement: Intent clarification is distinct from solution evaluation
USW SHALL keep `usw-refine-intent` available for iterative clarification.
Solution comparison SHALL remain a separate capability that accepts a bounded
problem, compares approaches, recommends one and returns without writing
clarification state. A text flow MAY name either capability as readable
guidance, but no validated Analysis runner or machine action routing is
required.

#### Scenario: Text flow needs missing intent details
- **WHEN** a Markdown flow explicitly asks to clarify unresolved intent
- **THEN** the model may invoke `usw-refine-intent` for one decision case

#### Scenario: User needs an approach choice
- **WHEN** the bounded problem is clear and the user requests solution comparison
- **THEN** the solution-evaluation capability runs separately rather than continuing clarification implicitly
