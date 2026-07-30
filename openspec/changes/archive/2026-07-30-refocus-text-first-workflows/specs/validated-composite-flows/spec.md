## REMOVED Requirements

### Requirement: Именованный project-owned flow
**Reason**: Safe lookup переносится в `text-flow-execution`.
**Migration**: Использовать общий text-flow resolver.

### Requirement: Минимальный Markdown-контракт
**Reason**: Обязательная версия и normalized representation удалены.
**Migration**: Использовать любой читаемый Markdown.

### Requirement: Линейные типизированные шаги
**Reason**: Typed step parser удалён.
**Migration**: Описывать порядок текстом.

### Requirement: Разрешение skill
**Reason**: Executor preflight удалён.
**Migration**: Модель использует доступные capabilities и обычные boundaries.

### Requirement: Безопасный project-local script
**Reason**: Специальный SCRIPT executor удалён.
**Migration**: Любой запуск script проходит обычные tool и permission rules.

### Requirement: Единый результат и остановка
**Reason**: Per-action outcome model удалена.
**Migration**: Использовать status всей text operation.

### Requirement: Проверка полномочий
**Reason**: Flow-level write-authority schema удалена.
**Migration**: Flow не предоставляет полномочия; действуют user и platform boundaries.

### Requirement: Возобновление с незавершённого шага
**Reason**: Machine cursor и JSON checkpoint удалены.
**Migration**: Generic HANDOFF хранит narrative recovery context.

### Requirement: Существующие role flows не изменяются
**Reason**: Standard role flows больше не зарезервированы.
**Migration**: Существующие Markdown-файлы продолжают исполняться как текст.
