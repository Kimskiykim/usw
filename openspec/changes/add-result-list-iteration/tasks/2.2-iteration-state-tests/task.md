# Task 2.2: Проверить lifecycle последовательного обхода

## Artifact model

- `v1`

## Result

Модульные проверки доказывают snapshot, продвижение, остановку и совместимость
состояния обхода.

## Scope

- Проверить создание непустого и пустого snapshot.
- Проверить завершённый элемент, текущий элемент и следующий resume.
- Проверить duplicate names, missing references и изменение snapshot.
- Проверить `failed`, `decision_required` и `outcome_unknown`.
- Проверить чтение существующих idle и legacy HANDOFF.

## Non-scope

- Исполнение реальных skills, scripts или внешних действий.
- End-to-end проверка Markdown flow.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/result-list-iteration/spec.md`

## Dependencies

- Task 2.1.

## Definition of done

- Каждый переход состояния имеет один прямой модульный тест.
- `outcome_unknown` не продвигает cursor и не разрешает автоматический retry.
- Legacy fixtures проходят без миграции.

## Verification

- Run: `python3 -m unittest tests.test_handoff_state -v`
- Expect: iteration and compatibility cases pass.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
