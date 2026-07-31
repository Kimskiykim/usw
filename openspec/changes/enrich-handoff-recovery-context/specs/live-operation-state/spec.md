## ADDED Requirements

### Requirement: Operation document сохраняет bounded recovery context
Every newly begun operation document SHALL contain a non-empty one-line
`Summary`, immutable timezone-aware `Started`, latest `Updated`, and a
`Workspace` section. The workspace section SHALL record the Git base revision
observed at Begin, or an explicit `unborn`, `not-git` or `unknown` state when no
revision can be observed; zero or more expected write hints supplied before
execution; and zero or more changes factually reported at the latest Outcome.

Summary and workspace values MUST remain informational: they MUST NOT change
operation identity, grant write authority, or claim detection or ownership of
concurrent product writes.

#### Scenario: New operation begins
- **WHEN** Begin registers a routed operation
- **THEN** its document contains a bounded summary, equal initial Started and Updated timestamps, the observed base revision, expected write hints and no observed changes

#### Scenario: Operation reaches an outcome
- **WHEN** Outcome records a natural stop and reported changed areas
- **THEN** Started, base revision and expected writes remain unchanged while Updated and observed changes reflect the confirmed Outcome

#### Scenario: Git inspection fails
- **WHEN** Git metadata exists but the base revision cannot be inspected and the repository is not positively identified as unborn
- **THEN** Begin records base revision as `unknown` without claiming an unborn repository

### Requirement: Enriched recovery context остаётся backwards-compatible
USW SHALL read existing generic operation documents that lack Summary, Started
and Workspace without changing their bytes during Show, Resume or parent
verification. Discovery SHALL derive a bounded display summary from exact input
and SHALL report unknown start time for such a document.

An Outcome mutation of an existing document SHALL write the enriched shape,
using explicit `unknown` for unavailable historical start and base revision.
Save MUST NOT replace an enriched operation with the older shape or invent
unavailable historical facts.

#### Scenario: Existing operation is inspected
- **WHEN** Show, Resume or parent verification reads an old routed operation document
- **THEN** the document remains byte-for-byte unchanged and its recovery content remains usable

#### Scenario: Existing operation receives Outcome
- **WHEN** Outcome updates an old recoverable operation
- **THEN** the operation is enriched with a derived summary, unknown historical fields and the newly reported observed changes

#### Scenario: Save attempts a downgrade
- **WHEN** an old-shape candidate targets an enriched operation
- **THEN** Save rejects the candidate and leaves the registered operation unchanged

### Requirement: Multi-operation discovery показывает human context
When more than one operation is registered, Show and Resume SHALL list each
operation's summary, flow, status, start time, latest update time, exact
operation identity and state path. The exact operation identity SHALL remain
the only selector.

#### Scenario: Two operations use the same flow
- **WHEN** discovery finds multiple registered operations with the same flow name
- **THEN** their summaries and timestamps are returned with their distinct exact operation identities without resuming either operation
