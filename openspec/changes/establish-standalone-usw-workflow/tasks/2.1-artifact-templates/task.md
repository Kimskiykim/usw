# Задача 2.1: Добавить канонические templates и review receipts

## Результат

Package содержит полный standalone layout для change, task и reviewer receipts,
а каждый вид состояния имеет одного документированного и проверяемого владельца.

## Область

- Добавить templates для proposal, design, capability spec, task index,
  granular task contract, step plan, evidence и optional task handoff.
- Добавить template неизменяемого reviewer receipt с gate, subject/source
  identity, reviewer, verdict, timestamp и ссылками на findings/evidence.
- Кодировать стабильные task IDs и ссылки из `tasks.md` в `task.md`.
- Валидировать, что completion checkboxes существуют только в `tasks.md`.
- Требовать от handoff ссылаться на receipt и канонические artifacts без копий.
- Сохранить `.usw/HANDOFF.md` как pointer, а не копию shared state.

## Вне области

- Выполнение tasks, tests или human review.
- Порядок flow scenarios.
- OpenSpec planning-artifact mapping.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/execution-artifacts/spec.md`

## Зависимости

- Задача 1.1.

## Критерии готовности

- Каждый artifact из standalone layout имеет packaged template.
- Receipt template не копирует requirements или evidence content.
- Ownership и checkbox invariants проверяются автоматически.
- Generated leaf task содержит scope, non-scope, dependencies, definition of
  done и verification с ожидаемым наблюдением.

## Проверка

- Запустить: `python3 -m unittest tests.test_package_layout tests.test_artifact_contract -v`
- Ожидание: templates упакованы, а authority, receipt и checkbox invariants
  проходят.
