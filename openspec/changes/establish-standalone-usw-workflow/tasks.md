# Задачи: самостоятельный USW workflow

Используйте стабильные ID и связывайте каждую исполнимую leaf task с её
granular `task.md`. Checkbox в этом файле является единственным источником
текущего completion state coding task.

## Artifact model registry

- Activation task: `2.1`.
- Legacy task IDs: `1.1`, `1.2`, `2.1`, `2.2`, `3.1`, `3.2`, `3.3`, `4.1`,
  `5.1`, `5.2`, `5.3`, `6.1`.
- После завершения 2.1 legacy list является immutable. Новая task ID, которой
  нет в этом списке, MUST использовать `Artifact model: v1`; отсутствие model
  либо попытка добавить новый legacy ID отклоняются validator.

## 1. Основа workspace

- [ ] 1.1 [Реализовать общий контракт конфигурации v1 и review root](tasks/1.1-config-contract/task.md)
- [ ] 1.2 [Переключить инициализацию на standalone default](tasks/1.2-standalone-init/task.md)

## 2. Модель execution artifacts

- [ ] 2.1 [Добавить канонические templates и review receipts](tasks/2.1-artifact-templates/task.md)
- [ ] 2.2 [Определить безопасный replanning и повторное открытие coding task](tasks/2.2-safe-replanning/task.md)

## 3. Оркестрация flow

- [ ] 3.1 [Определить три role scenarios и human review gates](tasks/3.1-flow-scenario-contract/task.md)
- [ ] 3.2 [Добавить оркестратор `usw-run-flow`](tasks/3.2-flow-orchestrator/task.md)
- [ ] 3.3 [Согласовать и дополнить atomic capabilities](tasks/3.3-align-atomic-skills/task.md)

## 4. Итеративный refinement

- [ ] 4.1 [Завершить и упаковать persistent task refinement](tasks/4.1-package-refinement/task.md)

## 5. Совместимость с OpenSpec

- [ ] 5.1 [Реализовать явный OpenSpec provider mapping и role frontier](tasks/5.1-openspec-provider/task.md)
- [ ] 5.2 [Добавить release-blocking compatibility suite для pinned версии](tasks/5.2-pinned-compatibility/task.md)
- [ ] 5.3 [Добавить видимый неблокирующий latest probe](tasks/5.3-latest-probe/task.md)

## 6. Release integration

- [ ] 6.1 [Документировать и проверить оба workspace mode и Delivery contract](tasks/6.1-release-docs-e2e/task.md)
