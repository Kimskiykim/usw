# Flow scenario: Analysis

## Purpose

- Role: `Analysis`
- Lifecycle: `Analysis -> Development -> Testing -> Delivery`

## Inputs

- Raw intent or owner-routed findings with canonical artifact references.
- Explicit step, task, or change scope before any execution-capable action.

## Ordered actions

1. `check-inputs`
2. `restore-context`
3. `confirm-scope`
4. `clarify-intent`
5. `select-approach`
6. `write-proposal-and-specs`
7. `assess-spec-complexity`
8. `internal-review`
9. `propose-handoff`
10. `transition-review-development`

## Branches

- `confirm-scope:ambiguous` -> `stop:user-decision`
- `assess-spec-complexity:split-proposed` -> `stop:user-decision`
- `internal-review:rejected` -> `clarify-intent`
- `transition-review-development:rejected` -> `clarify-intent`
- `transition-review-development:accepted` -> `stop:scope-complete`

## Write authority

- `refinement-state`
- `proposal`
- `capability-specs`
- `review-receipt`
- `local-checkpoint`

## Stop conditions

- `user-decision`
- `blocker`
- `invalid-artifact-state`
- `permission-boundary`
- `scope-complete`

## Outputs

- Reviewed proposal/spec identities and Analysis internal receipt.
- Transition receipt owned by Development with sender `Analysis` and receiver `Development`.
- Findings return to Analysis; repair resumes at the earliest invalidated gate.
