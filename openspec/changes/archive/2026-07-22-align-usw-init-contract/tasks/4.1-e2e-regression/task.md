# Task 4.1: Run initialization and OpenSpec regression verification

## Artifact model

- `v1`

## Result

The complete change is apply-ready with validated OpenSpec artifacts and a green repository test suite.

## Scope

- Run the complete Python unittest suite.
- Validate the OpenSpec change strictly.
- Confirm no user-owned OpenSpec artifacts are created or overwritten by initialization fixtures.
- Confirm deferred transactionality and concurrent TOCTOU work did not enter the diff.
- Record exact pass, skip and failure counts in task evidence if implementation workflow requires it.

## Non-scope

- Fixing unrelated pre-existing failures.
- Implementing deferred hardening.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- All delta specs under `../../specs/`

## Dependencies

- Tasks 1.1, 1.2, 2.1, 2.2 and 3.1 are complete.

## Definition of done

- All repository tests pass or any unrelated pre-existing failure is explicitly evidenced and accepted.
- `openspec validate align-usw-init-contract --strict` passes.
- Git diff contains only the agreed implementation, documentation, test and change artifacts.

## Verification

- Run: `python3 -m unittest discover -s tests -v && openspec validate align-usw-init-contract --strict`
- Expect: unittest exits zero and OpenSpec reports a valid change.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
