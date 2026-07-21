# live-operation-state Specification

## Purpose
TBD - created by archiving change add-live-operation-state. Update Purpose after archive.
## Requirements
### Requirement: Единая Markdown-сводка операции
Orchestrator SHALL хранить текущую операцию, flow cursor и компактный журнал в
developer-local `.usw/HANDOFF.md`. Сводка SHALL содержать operation ID, actor,
role, executor, scope, flow step, intent, declared writes, status, timestamps,
result, actual changed areas, verification и references либо явное `none`.

#### Scenario: Начало операции
- **WHEN** preflight выбранного flow step завершён
- **THEN** orchestrator записывает полную `in_progress` сводку до вызова executor

#### Scenario: Результат операции
- **WHEN** executor вернул управление
- **THEN** orchestrator обновляет result, actual areas, verification, cursor и одну compact journal row до выбора следующего шага

### Requirement: Write-before-executor порядок
Orchestrator MUST проверить flow, scope, capability и write authority до записи
начала. Executor MUST NOT вызываться, пока обновлённый HANDOFF не записан и не
прочитан обратно без видимых пропусков обязательных полей.

#### Scenario: Preflight отклонён
- **WHEN** flow, scope, capability или authority не прошли проверку
- **THEN** executor не вызывается и ложная `in_progress` запись не создаётся

#### Scenario: Запись начала не подтверждена
- **WHEN** HANDOFF не удалось записать или прочитать обратно
- **THEN** executor не вызывается, а flow останавливается на local-state boundary

### Requirement: Наблюдаемый outcome
После executor orchestrator SHALL сравнить reported writes с declared writes и
сохранить completed, failed, blocked, decision_required либо permission boundary.
Cursor SHALL продвигаться только после completed.

#### Scenario: Успешный outcome
- **WHEN** executor завершился и reported writes соответствуют authority
- **THEN** cursor переходит к следующему step, а операция добавляется в journal одной строкой

#### Scenario: Нарушение write contract
- **WHEN** reported writes превышают declared writes или flow authority
- **THEN** HANDOFF фиксирует violation, cursor не продвигается и следующий executor не запускается

### Requirement: Консервативный resume
Resume SHALL сначала читать только summary, next action и freshness. Статус
`in_progress` без result MUST считаться возможным прерыванием внутри executor и
MUST NOT приводить к автоматическому retry.

#### Scenario: Возможно прерванный executor
- **WHEN** resume обнаруживает `in_progress` без result
- **THEN** агент показывает actor, executor, scope, intent и writes и требует явного решения перед mutation

#### Scenario: Сводки достаточно
- **WHEN** операция завершена и freshness не требует расследования
- **THEN** referenced artifacts не читаются без необходимости

### Requirement: Ручной lifecycle и совместимость
Любое non-idle состояние SHALL сохраняться до `/usw-handoff finish`. Другой
flow или scope MUST быть заблокирован. Существующий legacy active HANDOFF SHALL
оставаться доступным для show, resume и finish без выдуманных полей.

#### Scenario: Другой flow при active state
- **WHEN** сохранённый flow/scope не совпадает с новым запросом
- **THEN** orchestrator останавливается и предлагает resume либо `/usw-handoff finish`

#### Scenario: Legacy FLOW checkpoint
- **WHEN** `.usw/FLOW.json` существует
- **THEN** orchestrator не объединяет его автоматически с HANDOFF и требует явного завершения или ручного переноса

### Requirement: Реализация без Python runtime
Capability SHALL быть реализована изменениями Markdown-шаблонов, skills,
commands и документации. Она MUST NOT добавлять или изменять Python-скрипты.

#### Scenario: Проверка реализации
- **WHEN** change готов к завершению
- **THEN** diff не содержит изменений `*.py`, новых runtime dependencies или второго автоматически обновляемого state-файла
