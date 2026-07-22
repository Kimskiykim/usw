# Task 4.1: Проверить выбор structured-контракта

## Artifact model

- `v1`

## Result

Contract tests закрепляют aliases, mandatory question и write-before-choice boundary.

## Scope

- Расширить существующий package-layout test.

## Non-scope

- Новый test framework.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Tasks 1.1–1.2.

## Definition of done

- Focused selection test passes.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
