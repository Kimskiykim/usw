## REMOVED Requirements

### Requirement: Default run-flow принимает любой Markdown
**Reason**: Поведение переносится в `text-flow-execution`.
**Migration**: Использовать единый text-first runtime.

### Requirement: Фасад разрешает именованный flow в существующих roots
**Reason**: Поведение переносится в `text-flow-execution`.
**Migration**: Использовать единый безопасный resolver.

### Requirement: Default executor следует описанному процессу
**Reason**: Поведение переносится в `text-flow-execution`.
**Migration**: Модель следует immutable Markdown invocation.

### Requirement: Default execution имеет одну operation boundary
**Reason**: Поведение переносится в generic text operation.
**Migration**: Использовать optional generic handoff.

### Requirement: Structured runtime является явным experiment
**Reason**: Experimental runtime удалён из production.
**Migration**: Убрать flag и запустить тот же Markdown как текстовый.

### Requirement: Experimental runtime сохраняет typed control flow
**Reason**: Parser, typed executors и machine control удалены.
**Migration**: Маркеры остаются читаемыми подсказками для модели.

### Requirement: Structured checkpoint изолирован по запуску
**Reason**: JSON checkpoint runtime удалён.
**Migration**: Existing state остаётся нетронутым; resumable context хранится в HANDOFF.

### Requirement: Experimental binding необязателен
**Reason**: Machine bindings удалены.
**Migration**: Вход и зависимости описываются текстом.

### Requirement: Структурированную форму создаёт create-flow
**Reason**: Validator-backed structured form удалена.
**Migration**: `--structured` создаёт authoring convention без machine guarantees.
