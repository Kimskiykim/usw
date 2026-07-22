# Task 4.2: Проверить канонический structured-контракт

## Artifact model

- `v1`

## Result

Contract test закрепляет human-readable markers, static checklist и bounded controls.

## Scope

- Добавить минимальные assertions в существующий test module.

## Non-scope

- Parser-level test fixtures.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Tasks 2.1–3.2.

## Definition of done

- Focused structured-contract test passes.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
