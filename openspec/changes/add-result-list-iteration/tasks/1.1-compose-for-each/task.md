# Task 1.1: Добавить минимальный контракт `FOR EACH`

## Artifact model

- `v1`

## Result

`usw-create-flow` умеет составить последовательный `FOR EACH` по конечному
списку результата, не вводя общий язык коллекций.

## Scope

- Добавить каноническую форму `FOR EACH <item> IN <action>.<list>`.
- Требовать ранее объявленное действие-источник и одно дочернее действие.
- Описать уникальные имена и ссылки элементов, последовательность и пустой список.
- Добавить короткий пример explorer → groups → обработка каждой группы.
- Проверить структуру skill и запрет исполнения созданного flow.

## Non-scope

- Parser, переменные, выражения, вложенный или параллельный обход.
- Изменение контракта версии `1`.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/result-list-iteration/spec.md`

## Dependencies

- Change `add-markdown-flow-composition` завершён и архивирован.

## Definition of done

- Skill создаёт `FOR EACH` только для динамического конечного списка результата.
- Известные элементы MAY оставаться обычными именованными действиями.
- Точный вызов `$usw-run-flow <name>` сохранён, а flow не исполняется при составлении.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`
- Expect: canonical markers and existing v1 packaging contract pass.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
