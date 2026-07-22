# Task 1.1: Добавить structured-selector

## Artifact model

- `v1`

## Result

`-s` и `--structured` эквивалентно выбирают `version-2` независимо от local selector.

## Scope

- Обновить разбор selector в `usw-create-flow`.

## Non-scope

- Добавление CLI parser.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Нет.

## Definition of done

- Structured и local selector можно безопасно сочетать в любом порядке.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
