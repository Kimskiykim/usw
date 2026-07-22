## Why

Пользователь должен запускать flow как обычный Markdown-документ, передавая
только задачу и имя flow. Текущий `usw-run-flow` требует знания строгих схем и
смешивает простой пользовательский сценарий с экспериментальным workflow
runtime.

## What Changes

- Сделать default-контрактом `usw-run-flow` вызов вида «задача + имя flow»:
  найти именованный `.md` в существующих shared/local roots, прочитать его и
  выполнить описанный порядок действий.
- Принимать по умолчанию любой Markdown без обязательной версии, DSL,
  постоянных action names, bindings или предварительной компиляции плана.
- Оставить разрешение файлов, базовые проверки безопасности, внешние
  permissions и наблюдаемый HANDOFF begin/outcome частью default-пути.
- Передать создание и обновление структурированных flow в ответственность
  `usw-create-flow`; `usw-run-flow` не переписывает исходный документ.
- **BREAKING**: строгий parser/runtime версий `1` и `version-2`, typed
  executors, gates, loops, parallel, cursor/checkpoint и data binding больше не
  активируются по содержимому документа. Они доступны только через явный
  экспериментальный opt-in.
- Не требовать action-specific input map даже в экспериментальном режиме;
  binding остаётся дополнительной возможностью строгого runtime.

## Capabilities

### New Capabilities

- `structured-flow-runtime`: default-запуск любого Markdown-flow и явно
  включаемый экспериментальный runtime для строгих v1/v2 контрактов.

### Modified Capabilities

Нет.

## Impact

Изменение затрагивает `usw-run-flow`, `usw-create-flow`, поиск shared/local
flow, Python parser/orchestrator, HANDOFF integration, README и
контрактные/регрессионные тесты. Новая зависимость, новый DSL и отдельный
scheduler не добавляются.
