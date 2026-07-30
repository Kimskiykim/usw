## REMOVED Requirements

### Requirement: Existing authoring boundaries remain active
**Reason**: Требование сохраняет strict validator-backed authoring.
**Migration**: Сохраняются write и execution boundaries, но не machine validation.

## ADDED Requirements

### Requirement: Structured authoring не запускает validator
Authoring SHALL проверять только выбранный безопасный файл и читаемость
документа. Оно MUST NOT вызывать retired runtime и MUST NOT выполнять flow.

#### Scenario: Structured revision сохранена
- **WHEN** автор завершает `version-2` revision
- **THEN** отчёт предлагает обычный text-first run без experimental flag
