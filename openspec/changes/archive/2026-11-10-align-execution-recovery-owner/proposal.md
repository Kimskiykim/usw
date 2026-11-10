# Proposal

## Why

AUD-T08 подтверждён в baseline: `execution-artifacts` направляет pause и
replanning в `.usw/HANDOFF.md`, а `live-operation-state` определяет этот файл
как router и назначает recovery content точному operation document.

## What Changes

- Согласовать три requirements `execution-artifacts` с routed operation
  contract: владелец состояния, generic handoff, replanning.
- Сохранить task/evidence/review нормы и все незатронутые scenarios.
- Добавить адресные stable-token проверки recovery owner; после проверки
  синхронизировать main spec и закрыть только AUD-T08 в карточке/индексе.

## Scope

Один наблюдаемый результат: обе действующие спецификации направляют pause и
replanning одной операции в authoritative operation document, HANDOFF остаётся
router. Полный исполнимый контракт — leaf `tasks/1.1-align-recovery-owner/task.md`.

## Non-goals

F04, backend/CLI/state format, повторное доказательство Resume/same-ID,
изменения skills, runtime, установка, миграция существующего state и новые
artifact roles. Специальные model CLI/API прогоны не входят в change.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `execution-artifacts`: согласовать место recovery state с
  `live-operation-state`, сохранив остальные обязанности artifacts.

## Impact

План будущего apply: `openspec/specs/execution-artifacts/spec.md`, адресный
stable-token test, `usw/backlog/AUD-T08.md`, строка и счётчик P2 в
`usw/BACKLOG.md`. `live-operation-state` и поставляемые skills уже задают
выбранный owner и не требуют правки. Planning не меняет эти product files.
