# Спецификация local-custom-flows

## Purpose
Определяет безопасный выбор local/shared без изменения режима text execution.

## Requirements

### Requirement: Явный выбор origin
Система SHALL считать `--local` и `-l` равнозначными явными selectors для
developer-local flows, а `--shared` — явным selector shared origin.

#### Scenario: Создание local flow
- **WHEN** пользователь создаёт именованный flow с `--local` или `-l`
- **THEN** система записывает только `.usw/flows/<name>.md`

#### Scenario: Запуск shared flow
- **WHEN** пользователь запускает именованный flow с `--shared`
- **THEN** система загружает только `<flows.root>/<name>.md`

### Requirement: Неявный lookup использует local-first
Без явного selector система SHALL сначала искать в `.usw/flows`, а затем в
настроенном `flows.root`.

#### Scenario: Оба origin содержат одинаковое имя
- **WHEN** local и shared flows имеют одинаковое safe name
- **THEN** выбирается local file и возвращается его origin

### Requirement: Local и shared используют единый text path
После выбора origin USW SHALL создавать одинаковый immutable Markdown
invocation. Metadata, origin и markers `version-2` MUST NOT выбирать другой
executor. Identity SHALL включать origin, даже если names и Markdown bytes
совпадают.

#### Scenario: Одинаковый content в разных origins
- **WHEN** local и shared flows имеют одинаковые names и Markdown
- **THEN** каждый выбранный invocation получает origin-specific identity и
  одинаковую execution semantics

### Requirement: Paths local flow остаются внутри безопасного local state
Система MUST отклонять local root или target, проходящий через symbolic link
либо разрешающийся в flow file, который не является regular.

#### Scenario: Path local flow небезопасен
- **WHEN** `.usw`, `.usw/flows`, intermediate component или выбранный file
  небезопасен
- **THEN** создание или execution останавливается до чтения, записи или вызова
  flow
