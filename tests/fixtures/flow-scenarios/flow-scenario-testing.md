# Flow scenario: Testing

## Purpose

- Role: `Testing`
- Lifecycle: `Analysis -> Development -> Testing -> Delivery`

## Inputs

- Accepted Development handoff and exact product source identity.
- Normative product contract and current Development evidence.

## Ordered actions

1. `check-inputs`
2. `restore-context`
3. `confirm-scope`
4. `independent-verification`
5. `write-testing-evidence`
6. `internal-review`
7. `propose-handoff`
8. `transition-review-delivery`

## Branches

- `confirm-scope:ambiguous` -> `stop:user-decision`
- `independent-verification:implementation-finding` -> `stop:owner-return-development`
- `independent-verification:specification-finding` -> `stop:owner-return-analysis`
- `internal-review:rejected` -> `independent-verification`
- `transition-review-delivery:rejected` -> `independent-verification`
- `transition-review-delivery:accepted` -> `stop:delivery`

## Write authority

- `independent-tests`
- `testing-findings`
- `testing-evidence`
- `review-receipt`
- `local-checkpoint`

## Stop conditions

- `user-decision`
- `blocker`
- `invalid-artifact-state`
- `permission-boundary`
- `owner-return-analysis`
- `owner-return-development`
- `delivery`

## Outputs

- Independently tested source identity and Testing internal receipt.
- Transition receipt owned by the delivery owner with sender `Testing` and receiver `Delivery owner`.
- Delivery scope, current evidence, observations, and owner; no implicit external action authority.
