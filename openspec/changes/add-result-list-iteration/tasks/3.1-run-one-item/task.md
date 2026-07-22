# Task 3.1: Добавить исполнение одного элемента за вызов

## Artifact model

- `v1`

## Result

`usw-run-flow` вручную обрабатывает ровно один текущий элемент `FOR EACH` за
вызов и сохраняет результат до возврата управления.

## Scope

- Разрешать только ссылку `<action>.<list>` на завершённый источник.
- Создавать и проверять snapshot до первого дочернего executor.
- Подставлять текущую item reference в контекст одного дочернего действия.
- Завершать пустой обход без executor.
- Возобновлять первый незавершённый элемент только по сохранённому snapshot.
- Обновить `usw-manage-handoff` для отображения и завершения iteration state.

## Non-scope

- Автоматическая обработка всего списка одним вызовом.
- Параллельный или вложенный `FOR EACH`.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/result-list-iteration/spec.md`

## Dependencies

- Task 1.1.
- Task 2.1.

## Definition of done

- Один вызов выполняет не более одного item executor.
- Следующий элемент становится доступен только после подтверждённого `completed`.
- Declared и actual writes проверяются для каждого элемента.

## Verification

- Run: `python3 -m unittest tests.test_flow_orchestrator tests.test_package_layout -v`
- Expect: one-item boundary and skill contracts pass.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
