# Удаление старых миграций HANDOFF

## Why

Владелец подтвердил отсутствие установок, которым нужны старые форматы, и
поручил удалить совместимость сейчас, без ожидания мажорного выпуска.
Автоматические преобразования усложняют чтение и изменение состояния.

## What Changes

- **BREAKING**: single-state HANDOFF больше не преобразуется в router.
- **BREAKING**: operation documents без `Summary`, `Started` и `Workspace`
  больше не читаются и не обновляются до актуальной формы.
- Старые файлы отклоняются без изменения их байт, router и candidates.
- Существующая работа актуальных routed operations сохраняется.

## Scope

Оставшиеся ветки совместимости в `handoff_state.py`, их тесты, спецификация
`live-operation-state`, skill, reference, context и описание ограничения в README.

## Non-goals

Новая миграция или команда конвертации, удаление пользовательского состояния,
изменение активации handoff, других решений AUD-I07 и новых статусов.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `live-operation-state`: только routed HANDOFF и актуальные operation documents;
  отказ от двух автоматических преобразований старого состояния.

## Impact

`skills/usw-manage-handoff/scripts/handoff_state.py`, handoff skill/reference,
`tests/test_handoff_state.py`, fixtures `tests/test_platform_support.py`, context
и README. Новые зависимости не нужны. Старое состояние сохраняется на диске,
но его чтение/обновление не поддерживается. Role-based формат уже отклоняется.
