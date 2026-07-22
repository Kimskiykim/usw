# Task 3.4: Разделить отчёты версий 1 и version-2

## Artifact model

- `v1`

## Result

Версия `1` получает прежнюю run command, а `version-2` — только static-check report.

## Scope

- Описать разные completion reports двух контрактов.

## Non-scope

- Запуск `version-2` текущим runner.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Tasks 1.3 and 3.3.

## Definition of done

- Structured report явно сообщает отсутствие current runner support и не содержит run command.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
