## REMOVED Requirements

### Requirement: Три role flows образуют один macro lifecycle
**Reason**: Text-first USW не навязывает один lifecycle.
**Migration**: Описывать нужный процесс непосредственно в Markdown flow.

### Requirement: Каждый flow использует общий управляющий shell
**Reason**: Machine orchestrator удалён.
**Migration**: Модель следует полному Markdown.

### Requirement: Analysis формирует ограниченные спецификации
**Reason**: Role ownership не является обязательным runtime contract.
**Migration**: При необходимости сохранить это правило в конкретном flow.

### Requirement: Development сохраняет authority спецификации
**Reason**: Role ownership не является обязательным runtime contract.
**Migration**: При необходимости сохранить это правило в конкретном flow.

### Requirement: Testing создаёт независимое evidence
**Reason**: Role ownership не является обязательным runtime contract.
**Migration**: При необходимости сохранить это правило в конкретном flow.

### Requirement: Human review разделён на internal и transition gates
**Reason**: Обязательные machine gates удалены.
**Migration**: Описывать нужные review points в Markdown.

### Requirement: Возвраты направляются владельцу и повторяют затронутые gates
**Reason**: Deterministic transition graph удалён.
**Migration**: Описывать recovery и feedback в Markdown.

### Requirement: Явный контракт flow scenario
**Reason**: Role scenario schema удалена.
**Migration**: Использовать свободный или structured Markdown.

### Requirement: Scenario владеет оркестрацией
**Reason**: Scenario parser удалён.
**Migration**: Модель интерпретирует полный документ.

### Requirement: Минимальный набор skills ориентирован на capabilities
**Reason**: Каталог остальных skills не входит в этот change.
**Migration**: Skills остаются независимо вызываемыми.

### Requirement: Scope исполнения выбирается явно
**Reason**: Typed orchestration scope удалён.
**Migration**: User input и flow prose определяют scope.

### Requirement: Write authority проверяется до записи
**Reason**: Role artifact authority не является свойством generic runner.
**Migration**: Применяются user scope, capability и platform permission boundaries.

### Requirement: Delivery использует per-run terminal contract
**Reason**: Per-run machine contract удалён.
**Migration**: Text flow завершает работу общим outcome.

### Requirement: Причина остановки flow наблюдаема
**Reason**: Требование заменено общими text-flow statuses.
**Migration**: Использовать status и blocker generic handoff/result.
