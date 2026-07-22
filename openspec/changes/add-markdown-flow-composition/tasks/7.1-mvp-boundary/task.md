# Task 7.1: Убрать зависимости и полномочия записи из version-2

## Artifact model

- `v1`

## Result

Creation-only MVP `version-2` не содержит полей `После`, деклараций `Пишет`
и раздела полномочий записи.

## Scope

- Удалить dependency и write-authority contract из proposal, design и spec.
- Упростить canonical example и статический checklist.
- Закрепить отсутствие полей контрактным тестом.

## Non-scope

- Версия `1`, parser, runtime и будущая модель зависимостей или полномочий.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Task 6.1.

## Definition of done

- `version-2` не содержит `После`, `Пишет` и раздел полномочий записи.
- Порядок списка и управляющие маркеры полностью описывают MVP.
- Targeted tests, full suite и strict OpenSpec validation проходят.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`
- Run: `python3 -m unittest discover -s tests -v`
- Run: `openspec validate add-markdown-flow-composition --type change --strict`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | MVP boundary | `cr-001` | `usw-source-v1:a8f57e82367218382f421f36170868dec2eb9462b9c4aace29803e8a7899e288` | verified | `development-evidence.md` |
