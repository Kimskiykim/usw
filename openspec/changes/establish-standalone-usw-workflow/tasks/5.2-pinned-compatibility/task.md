# Задача 5.2: Добавить release-blocking compatibility suite для pinned версии

## Результат

Development и CI выполняют реальные end-to-end provider scenarios с одной
записанной версией OpenSpec, ошибка которой блокирует release readiness.

## Область

- Выбрать и записать initial pinned OpenSpec version в одном source of truth.
- Добавить isolated test installer/runner для точной версии.
- Проверить initialization detection, explicit provider selection, role
  frontier, artifact discovery, change planning, validation, provider-neutral
  review receipts и missing-capability errors.
- Настроить pinned compatibility job как release-blocking.

## Вне области

- Требование OpenSpec для standalone installation или runtime.
- Проверка каждой исторической версии OpenSpec.
- Автоматическое обновление pinned version.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/openspec-compatibility/spec.md`

## Зависимости

- Задача 5.1.

## Критерии готовности

- Точная pinned version хранится в version control и показывается test output.
- Compatibility tests используют реальную isolated OpenSpec installation.
- Ошибка любого required pinned scenario завершает release-blocking job ошибкой.
- Standalone tests не зависят от compatibility installation.

## Проверка

- Запустить: `./tests/run_openspec_compatibility.sh pinned`
- Ожидание: runner показывает точную recorded version, а все required реальные
  OpenSpec scenarios проходят.
