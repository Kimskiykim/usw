# Прямой ручной вызов handoff

## Why

Общая просьба сохранить состояние может означать запись в другой файл.
Владелец решил активировать ручной handoff только при прямом обращении к нему,
сохранив служебные вызовы внутри flow по конфигурации USW.

## What Changes

- Запретить неявную активацию handoff в metadata.
- До чтения конфигурации и состояния отделять прямой ручной вызов от общих
  просьб сохранить состояние или продолжить работу.
- Сохранить служебные Begin/Outcome runner и запрет доступа при `handoff: false`.

## Scope

Handoff skill, metadata, публичные команды, `live-operation-state`, README,
проверка manifest и адресные behavior scenarios.

## Non-goals

Изменение Python CLI, форматов хранения, find/assess, установки глобальных
skills, дополнительное подтверждение уже разрешённых действий.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `live-operation-state`: граница ручной активации и служебного вызова handoff.
- `flow-behavior-evaluation`: нейтральная вводная для проверки активации skill.

## Impact

`skills/usw-manage-handoff/`, `commands/usw-handoff.md`, `commands/usw-resume.md`,
`tests/test_package_layout.py`, `evals/scenarios/` и вводная eval harness для
activation scenarios, README. Изменение ограничивает
выбор моделью skill; runtime не получает сведения о намерении пользователя.
