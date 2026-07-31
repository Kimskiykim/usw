# Task 2.1: Добавить состояние snapshot и текущего элемента

## Artifact model

- `v1`

## Result

Существующий HANDOFF state хранит неизменяемый snapshot обхода и наблюдаемый
прогресс элементов без изменения зафиксированного плана.

## Scope

- Минимально расширить `handoff_state.py` структурами iteration snapshot.
- Сохранять имя блока, удостоверение snapshot, порядок имён и ссылки элементов.
- Сохранять текущий элемент, попытку и нормализованный результат экземпляра.
- Проверять уникальность имён, ссылки и неизменяемость snapshot.
- Сохранить чтение существующих idle и legacy состояний.

## Non-scope

- Толкование Markdown, выбор executor или общий collection runtime.
- Копирование содержимого групп в HANDOFF.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/result-list-iteration/spec.md`

## Dependencies

- Change `add-markdown-flow-composition` завершён и архивирован.

## Definition of done

- Валидный snapshot записывается и читается без потери порядка.
- План не меняется при создании snapshot и продвижении по элементам.
- Дубликаты имён и неполные ссылки отклоняются до executor.

## Verification

- Run: `python3 -m unittest tests.test_handoff_state -v`
- Expect: existing HANDOFF cases remain green and new structures round-trip.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
