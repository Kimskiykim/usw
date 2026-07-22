# Task 3.2: Проверять ссылки на executors

## Artifact model

- `v1`

## Result

Skills, scripts и nested flows разрешаются безопасно до успешного возврата.

## Scope

- Проверить exact skill names, safe scripts, literal args и selected-root nested flows.

## Non-scope

- Создание отсутствующих executors.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Task 3.1.

## Definition of done

- Неразрешимая или небезопасная ссылка блокирует успешное создание.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
