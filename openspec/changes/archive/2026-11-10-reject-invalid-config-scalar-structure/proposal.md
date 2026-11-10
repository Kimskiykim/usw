# Proposal

## Why

[AUD-T01](../../../usw/backlog/AUD-T01.md): текст `notes: |` с вложенным
`handoff: false` отключает HANDOFF, а вложенный `flows.root` меняет место
инициализации. Parser теряет границу scalar; подтверждены фактические записи
initializer, а не только расхождение с общей грамматикой YAML.

## What Changes

- **BREAKING для ранее ошибочно принятых документов:** отклонять
  недопустимую scalar/block структуру с `invalid_config` до
  managed writes, сохраняя допустимые неизвестные поля инертными.
- Согласовать ограниченный subset в Python и init fallback; закрепить
  проверки parser, initialization и существующих shared authoring/Handoff callers.

## Scope

Общая конфигурация v1 и её structural validation. Полный контракт выполнения
и proof находятся в [единственной leaf task](tasks/1.1-reject-invalid-scalar-structure/task.md).

## Non-goals

Полный YAML, quoted keys/escapes, Windows paths/T04, новые зависимости,
runtime, очередь и изменение handoff activation или flow execution.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `workspace-configuration`: явная граница допустимой scalar структуры.

## Impact

В пакете меняются `usw-initialize-project/scripts/init_usw.py` и
`references/llm-fallback.md`; downstream callers используют общий parser.
Планируемые tests, main-spec/card/index edits и порядок final source — в design.
