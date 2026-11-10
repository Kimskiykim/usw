# Proposal

## Why

Реальный рецепт `external-event-wait` безусловно обещает, что resume той же
operation продолжит ожидающий шаг. При `handoff: false` доступ к recovery state
запрещён, поэтому обещание не выполняется; это подтверждённая часть AUD-I13.

## What Changes

- Различить ожидание события и доступность восстановления в guidance автора.
- При выключенном handoff возвращать человеку контекст ручного повторного
  входа; не обещать восстановление той же operation или автоматический курсор.
- При включённом handoff ссылаться на действующий recovery contract и
  фактически сохранённый контекст, сохранив однократную проверку и `blocked`.
- Проверить текст обычным читателем и фактическими локальными действиями;
  добавить узкие stable-token проверки без нового runtime или eval runner.

## Scope

Один результат: готовый блок ожидания внешнего события не обещает недоступное
восстановление. Production scope — только
`skills/usw-create-flow/references/recipes/external-event-wait.md`;
normative delta — `guided-flow-authoring`; tests — адресная проверка
`tests/test_package_layout.py`. Main-spec sync и точная отметка выполненной
части AUD-I13/index входят в будущий конечный source, см. leaf task.

## Non-goals

Другие части AUD-I13 (`external-action-approval`, `input-preflight`), закрытие
всей карточки, изменение run/manage `SKILL.md`, backend/CLI/state/status,
установка, commits/index/push и интеграция. Не добавляются scheduler, polling,
курсор, новый формат recovery, очередь или обязательный файл отчёта.
Специальные CLI/API inference, availability/effort/model probes и платные
before/after серии запрещены текущим поручением.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `guided-flow-authoring`: блок ожидания учитывает действующий handoff и
  различает durable recovery и ручной повторный вход с переданным контекстом.

## Impact

Новых зависимостей и изменений public CLI нет. Действующие нормы
`live-operation-state` и ephemeral root identity сохраняются. Один ordinary
reader воспроизвёл обещание из рецепта, а actual backend Resume отказал при
`handoff: false`; proof и ограничения — в design и локальном evidence.
Planning основан на отдельной копии HEAD `2cee3137`; T01 в неё не включён.
