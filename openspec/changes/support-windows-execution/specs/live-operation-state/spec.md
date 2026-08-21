## MODIFIED Requirements

### Requirement: Handoff transitions are serialized
Begin, Outcome, Save, Finish and Cleanup SHALL serialize their complete
read-check-write transition under the project-local handoff lock, on every
supported platform and without depending on a locking primitive that is absent on
one of them. Begin SHALL
write and verify the operation document before registering it and MUST NOT
start model execution before both writes are confirmed. Outcome SHALL update
only the selected authoritative operation document and then refresh the
human-readable status snapshot in the router.

Save MUST use an operation-scoped candidate and MUST NOT replace legacy state,
rewrite a terminal operation, change operation identity or immutable context,
or target an unregistered operation. Finish SHALL unregister only the selected
identity before removing only its exact operation document and candidate.
Cleanup SHALL first unregister all terminal identities and then remove only
their exact operation documents and candidates.

#### Scenario: Two Begin calls overlap
- **WHEN** two processes create different operation identities concurrently
- **THEN** both operations may be registered in serialized transitions without losing either router entry

#### Scenario: Concurrent operations write Outcome
- **WHEN** two registered roots reach natural stops concurrently
- **THEN** each Outcome changes only its exact operation document and both routes remain registered

#### Scenario: Begin stops before registration
- **WHEN** Begin cannot confirm its router entry after creating a candidate operation document
- **THEN** model execution does not start and the candidate is removed on a handled failure or remains a non-routable orphan after a process crash

#### Scenario: Finish selects one of two operations
- **WHEN** Finish names one of two registered operation identities
- **THEN** only that route and its exact files are removed while the other operation remains unchanged

#### Scenario: Queued Save arrives after Finish
- **WHEN** a candidate for a prior operation is saved after its route was removed
- **THEN** every registered operation remains unchanged and the candidate is rejected

#### Scenario: Handoff transition on a platform without POSIX locking
- **WHEN** any handoff transition runs on a supported platform that has no `fcntl`
- **THEN** the transition is serialized by that platform's locking primitive and its state files are read and written through the shared safe-access boundary
