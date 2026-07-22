# Task 1.3: Сохранить совместимость версии 1

## Artifact model

- `v1`

## Result

Новая линейная форма версии `1` стала concise, а существующая verbose-форма,
executors и shared/local roots остаются совместимыми.

## Scope

- Сохранить чтение и исполнение прежнего шаблона и команду validation версии `1`.

## Non-scope

- Structured-конструкции внутри версии `1`.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Task 1.1.

## Definition of done

- Существующий v1 contract test проходит без миграции.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`

## Contract revision

- `cr-002`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
| 2 | concise version-1 | `cr-002` | `usw-source-v1:fb982e192c3b67bf24ad3f61a46958df71379cb6440d13b653d03ea6bc91f17a` | verified | `development-evidence.md` |
