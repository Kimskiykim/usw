## REMOVED Requirements

### Requirement: Structured-flow остаётся человекочитаемым контрактом
**Reason**: Существующее требование связывает readable Markdown со strict
executable contract.
**Migration**: Использовать text-first authoring convention.

### Requirement: Составитель выполняет лёгкую статическую проверку
**Reason**: Structured parser и validator удалены.
**Migration**: Проверять только безопасный путь, сохранение Markdown и очевидную
читаемость.

### Requirement: Новая версия 1 не дублирует write-contract
**Reason**: Strict version 1 больше не является production contract.
**Migration**: Существующие файлы выполняются как обычный Markdown.

### Requirement: Обе strict-версии сохраняют свои границы
**Reason**: Production больше не выбирает strict version.
**Migration**: Версия внутри файла является документацией.

### Requirement: Детали выбранного режима раскрываются по требованию
**Reason**: Отдельного execution mode больше нет.
**Migration**: `--structured` влияет только на authoring style.

## ADDED Requirements

### Requirement: Version-2 является authoring convention
`--structured` SHALL создавать читаемый Markdown с `version-2` и применимыми
`CALL`, `GATE`, `LOOP`, `PARALLEL`, но MUST NOT заявлять validator, deterministic
transitions, atomic parallelism или durable cursor.

#### Scenario: Structured flow создан
- **WHEN** пользователь явно выбирает `--structured`
- **THEN** автор получает читаемый Markdown и обычную `$usw-run-flow` команду
