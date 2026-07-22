# Flow scenario: Development

## Purpose

- Role: `Development`
- Lifecycle: `Analysis -> Development -> Testing -> Delivery`

## Inputs

- Accepted Analysis handoff, canonical specifications, and explicit execution scope.
- Current task contract, source identity, and applicable evidence.

## Ordered actions

1. `check-inputs`
2. `restore-context`
3. `confirm-scope`
4. `write-design-and-tasks`
5. `execute-bounded-scope`
6. `local-verification`
7. `write-development-evidence`
8. `internal-review`
9. `propose-handoff`
10. `transition-review-testing`

## Branches

- `confirm-scope:ambiguous` -> `stop:user-decision`
- `execute-bounded-scope:product-decision-missing` -> `stop:owner-return-analysis`
- `internal-review:rejected` -> `execute-bounded-scope`
- `transition-review-testing:rejected` -> `execute-bounded-scope`
- `transition-review-testing:accepted` -> `stop:scope-complete`

## Write authority

- `technical-design`
- `task-index`
- `task-contract`
- `implementation`
- `implementation-tests`
- `development-evidence`
- `review-receipt`
- `local-checkpoint`

## Stop conditions

- `user-decision`
- `blocker`
- `invalid-artifact-state`
- `permission-boundary`
- `owner-return-analysis`
- `scope-complete`

## Outputs

- Verified implementation source and Development internal receipt.
- Transition receipt owned by Testing with sender `Development` and receiver `Testing`.
- Findings return to the artifact owner; repair resumes at the earliest invalidated gate.
