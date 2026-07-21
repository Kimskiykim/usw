# Task 3.1: Обновить документацию и проверить change end-to-end

## Artifact model

- `v1`

## Result

Documentation, package metadata and the full test suite consistently describe
and verify the new local intent-clarification boundary.

## Scope

- Update README examples, lifecycle diagrams and migration notes.
- Remove stale public references to `usw-refine-task` and shared default refinement storage.
- Verify supported harness packaging and OpenSpec compatibility remain intact.
- Run the complete test suite and validate this OpenSpec change.

## Non-scope

- Implementing optional automatic migration tooling.
- Renaming unrelated skills.
- Archiving the OpenSpec change.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/intent-clarification/spec.md`

## Dependencies

- Tasks 1.1, 1.2, 1.3 and 2.1.

## Definition of done

- User-facing documentation presents clarification as local and non-normative.
- No active package or documentation reference advertises the former skill identity.
- All automated tests pass and OpenSpec validates the change.

## Verification

- Run: `python3 -m unittest discover -s tests -v`
- Expect: the complete repository test suite passes without failures.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | proposal, design, intent-clarification spec |
