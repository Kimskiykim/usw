## Why

Текущий `usw-run-flow` исполняет только три захардкоженных role-сценария и не
позволяет проекту описать собственную проверяемую последовательность действий.
Нужен project-owned формат составного flow, который остаётся обычным Markdown,
но даёт гарантии порядка, полномочий, остановки и возобновления.

## What Changes

- Ввести общий Markdown-контракт линейного составного flow без ветвлений и
  циклов.
- Разрешить шаги двух типов: вызов установленного skill и запуск безопасно
  разрешённого project-local script.
- Загружать flow по явному имени из настроенного `flows.root` и проверять его до
  любого исполнения.
- Выполнять ровно один шаг за раз, переходить дальше только после `completed` и
  сохранять позицию для безопасного продолжения.
- Проверять declared writes, пути scripts и permission boundaries до mutation.

## Capabilities

### New Capabilities

- `validated-composite-flows`: Поиск, валидация и последовательное исполнение
  project-owned Markdown flows с единым контрактом шагов и остановки.

### Modified Capabilities

Нет.

## Impact

- `skills/usw-run-flow`: загрузка flow, общий parser/validator и исполнение
  последовательности.
- Atomic USW skills: разрешение skill-шагов через существующие capability
  contracts.
- Tests: структура Markdown flow, безопасное разрешение имён и путей,
  полномочия, остановка и resume.
- Новые runtime dependencies и произвольное выполнение shell-строк не
  вводятся.
