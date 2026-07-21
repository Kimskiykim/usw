## Why

USW фиксирует developer-local handoff только по явной команде, поэтому сбой
внутри atomic flow step не оставляет понятной записи о том, кто и в каком scope
начал работу. Для первой версии достаточно общего Markdown-протокола агентов;
отдельный runtime и новые Python-скрипты создавали бы несоразмерную сложность.

## What Changes

- Расширить `.usw/HANDOFF.md` компактными полями текущей операции, flow cursor,
  intent, result и журналом завершённых шагов.
- Обязать orchestrator после preflight записывать `in_progress` до executor и
  обновлять outcome сразу после его возврата.
- Восстанавливать незавершённую операцию консервативно, без автоматического retry.
- Блокировать другой flow/scope до resume либо `/usw-handoff finish`.
- Описать `.usw/FLOW.json` как устаревший checkpoint, который нельзя смешивать
  с активным HANDOFF.
- Не добавлять и не изменять Python runtime: исполнение остаётся агентным
  Markdown-контрактом.

## Capabilities

### New Capabilities

- `live-operation-state`: Markdown-контракт начала, результата и безопасного
  восстановления одной текущей операции.

### Modified Capabilities

- Нет.

## Impact

- Шаблон `.usw/HANDOFF.md`.
- Инструкции `usw-run-flow` и `usw-manage-handoff`.
- Команды `/usw-handoff`, `/usw-resume` и README.
- Новых runtime dependencies и Python-скриптов нет.
