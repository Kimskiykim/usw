# Задачи: граница `usw-refine-intent`

Каждая исполнимая leaf task имеет стабильный ID и granular `task.md`. Checkbox
в этом файле является единственным источником completion state.

## 1. Локальная capability уточнения

- [x] 1.1 [Переименовать skill и сузить его публичный контракт](tasks/1.1-rename-clarify-intent/task.md)
- [x] 1.2 [Перенести state writer в `.usw/refinements`](tasks/1.2-local-refinement-state/task.md)
- [x] 1.3 [Убрать shared refinement default из инициализации](tasks/1.3-initialization-boundary/task.md)

## 2. Оркестрационная граница

- [x] 2.1 [Развести clarification и solution evaluation в registry](tasks/2.1-route-capabilities/task.md)

## 3. Интеграция

- [x] 3.1 [Обновить документацию и проверить change end-to-end](tasks/3.1-docs-e2e/task.md)
