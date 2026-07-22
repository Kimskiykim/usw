## MODIFIED Requirements

### Requirement: Явный контракт flow scenario
Каждый project-owned исполнимый role scenario SHALL быть описан artifact
`flow-scenario-<name>.md` с sections Purpose, Inputs, Ordered actions, Branches,
Write authority, Stop conditions и Outputs.

Исполнимые role scenarios MUST разрешаться только из configured project
`flows.root`. Initialization MUST NOT создавать role scenarios автоматически,
а packaged examples под `<flows.root>/examples/` MUST NOT использоваться как
scenario либо скрытый runtime fallback.

#### Scenario: Валидация полного project-owned scenario
- **WHEN** пользовательский scenario содержит все обязательные sections и ссылается на доступные actions
- **THEN** USW принимает его как исполнимый orchestration contract

#### Scenario: Отклонение неполного scenario
- **WHEN** пользовательский scenario не содержит Write authority или Stop conditions
- **THEN** USW отклоняет его до запуска любого action

#### Scenario: Project scenario отсутствует во время запуска
- **WHEN** orchestrator не находит выбранный scenario в configured flow root
- **THEN** flow останавливается как invalid artifact state и не выполняет packaged example неявно
