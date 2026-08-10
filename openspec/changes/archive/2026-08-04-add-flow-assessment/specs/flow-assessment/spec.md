## ADDED Requirements

### Requirement: Assessment is explicitly selected and read-only
USW SHALL expose `$usw-assess-flow [--local|-l|--shared] <flow-name> [<scenario-input>]` only through explicit invocation. It MUST NOT create, update, execute or repair a flow, or read/change HANDOFF, execution state or product files. Only leading tokens before the safe name SHALL be origin selectors; invalid combinations SHALL yield `insufficient-data`, and trailing text SHALL remain opaque scenario input.

#### Scenario: Assessment has no origin selector
- **WHEN** a user supplies one safe flow name and optional scenario input
- **THEN** USW assesses local first and otherwise shared without execution

#### Scenario: Assessment has conflicting selectors
- **WHEN** both `--local` and `--shared` precede the flow name
- **THEN** USW returns `insufficient-data` before reading a flow

### Requirement: Assessment uses exact safely resolved Markdown
USW SHALL provide a read-only loader applying the execution resolver's kebab-case, containment, descriptor-relative traversal, no-symlink, regular-file and UTF-8 rules. It SHALL return `name`, `origin`, `identity`, `path`, exact `markdown` and `warnings` without execution input. The assessor MUST use only returned Markdown and MUST NOT reopen `path`; inspection MUST NOT inspect legacy state, HANDOFF or `.usw/FLOW.json`. Existing `resolve` behavior MUST remain compatible.

#### Scenario: Flow changes after inspection
- **WHEN** the file changes after exact Markdown and identity are returned
- **THEN** assessment continues from that returned Markdown and identity

#### Scenario: Selected flow traverses a symlink
- **WHEN** an origin root, intermediate component or final entry is a symlink
- **THEN** inspection stops before semantic assessment

### Requirement: Assessment returns a structured semantic verdict
USW SHALL return one verdict: `executable`, `executable-with-risks`, `not-executable` or `insufficient-data`. The report SHALL identify the flow, summarize terminal paths, list dependencies and give each material finding an invocation-local ID, `blocking|risk` severity, type, exact evidence, impact and minimal Markdown fix. A proven blocking defect SHALL yield `not-executable`; otherwise inadequate semantics SHALL yield `insufficient-data`, material risks SHALL yield `executable-with-risks`, and a coherent flow without material findings SHALL yield `executable`.

#### Scenario: Coherent finite flow
- **WHEN** required steps and dependencies reach declared outcomes without material risk
- **THEN** the report returns `executable` with no findings

#### Scenario: Prose cannot support a path
- **WHEN** no coherent next action or terminal interpretation is supported
- **THEN** the report returns `insufficient-data` and identifies missing semantics

### Requirement: Assessment detects logical and termination defects
USW SHALL examine reachability, branch/error outcomes, required data, contradictory actions, explicit `LOOP` markers and implicit returns. For each reachable cycle it SHALL assess exit, finite bound or escalation, observable progress and repeated irreversible side effects. An unconditional cycle without exit and an unsafe irreversible repeat SHALL be blocking; uncertain eventual exit SHALL be a risk; a bounded cycle with terminal fallback SHALL not be blocking. A one-time approval outside a loop SHALL NOT make an irreversible action inside that loop safe. Unless the action has an idempotency guarantee, both the action and its approval SHALL remain outside the loop.

#### Scenario: Two sections return forever
- **WHEN** A reaches B and B unconditionally returns to A with no exit
- **THEN** the report returns `not-executable` with a blocking cycle finding

#### Scenario: Retry has a finite fallback
- **WHEN** attempts are limited and exhaustion returns `failed` or `decision_required`
- **THEN** the loop creates no blocking non-termination finding

#### Scenario: Exit depends on eventual success
- **WHEN** a flow repeats until successful without bound or escalation
- **THEN** the report records a risk, not a definite infinite loop

#### Scenario: Irreversible action is repeated
- **WHEN** a reachable cycle can repeat an irreversible action without an idempotency guarantee
- **THEN** the report returns a blocking `unsafe-repeat` finding

#### Scenario: Approval precedes an unsafe repeat
- **WHEN** one approval occurs before a loop that can repeat an irreversible action
- **THEN** the report still returns a blocking `unsafe-repeat` finding

### Requirement: Dependency results preserve uncertainty
USW SHALL inspect declared dependencies and named skill, command or flow calls without executing them. Each SHALL be `confirmed`, `missing` or `unverified`; the first two require authoritative evidence. Available contracts SHALL be checked for required inputs and retired selectors, but child flows MUST NOT be recursively assessed. A missing mandatory dependency without handling SHALL be blocking; explicit terminal handling SHALL prevent absence alone from blocking. A proven contract-invalid mandatory invocation, including a missing required input or retired selector, without handled terminal fallback SHALL be blocking as a reachable dead end even when the dependency itself is confirmed.

#### Scenario: Mandatory dependency is absent without handling
- **WHEN** authoritative lookup proves it absent and no fallback/terminal response exists
- **THEN** the report returns a blocking dependency finding

#### Scenario: Missing dependency leads to a decision
- **WHEN** unavailability explicitly returns `decision_required`
- **THEN** absence is reported but is not itself blocking

#### Scenario: Mandatory invocation violates a confirmed contract
- **WHEN** a mandatory call uses a proven retired selector and has no terminal fallback
- **THEN** the report returns `not-executable` with a blocking reachable-dead-end finding

### Requirement: Semantic acceptance evidence is reproducible
USW SHALL keep the fixture Markdown and raw reports used for semantic acceptance checks inside the change. Acceptance summaries SHALL distinguish expected mappings from actually observed reports and identify the invocation boundary. If the assessment skill was not executed, the summary MUST label the mappings expected-only and MUST NOT claim observed semantic behavior.

#### Scenario: Semantic smoke is reported as observed
- **WHEN** acceptance evidence labels a verdict as observed
- **THEN** the corresponding checked-in fixture and raw assessment report identify how that verdict was produced

### Requirement: Optional scenario produces a subordinate trace
When scenario input exists, USW SHALL keep it separate from immutable Markdown and trace likely steps, gates and stop/ambiguity. The trace MUST NOT weaken findings on other declared paths.

#### Scenario: Scenario selects one healthy branch
- **WHEN** the scenario terminates but another declared branch is blocking
- **THEN** the trace terminates while the overall verdict retains the finding

### Requirement: Assessment makes no machine guarantee
USW SHALL describe the result as semantic model analysis and MUST NOT claim a parser-backed proof, deterministic transition graph, persistent cursor, recursive validation or execution authority.

#### Scenario: Report is presented
- **WHEN** assessment returns any verdict
- **THEN** it states that the result is evidence-backed semantic analysis, not a machine guarantee
