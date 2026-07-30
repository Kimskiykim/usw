## REMOVED Requirements

### Requirement: Examples follow the current project flows
**Reason**: Existing requirement наследует обязательный role lifecycle.
**Migration**: Examples демонстрируют независимые text-first processes.

## ADDED Requirements

### Requirement: Examples не обещают machine execution
Каждый устанавливаемый пример SHALL быть обычным Markdown и MUST NOT заявлять
strict validation, machine cursor или обязательный role lifecycle.

#### Scenario: Пользователь читает пример
- **WHEN** init устанавливает примеры
- **THEN** они описывают model-executed process и обычную run command
