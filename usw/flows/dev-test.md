# Flow: dev-test

Реализует выбранное OpenSpec-изменение, затем проверяет получившийся diff на
избыточную сложность. Замечания Ponytail не исправляются автоматически.

## Контракт

- Версия: `1`

## Порядок действий

1. Скилл: `openspec-apply-change`
   - Пишет: `implementation` `implementation-tests` `task-index`
2. Скилл: `ponytail-review`
   - Пишет: нет

## Полномочия записи

- `implementation`
- `implementation-tests`
- `task-index`
