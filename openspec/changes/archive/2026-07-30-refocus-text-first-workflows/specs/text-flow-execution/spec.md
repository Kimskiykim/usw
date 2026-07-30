## ADDED Requirements

### Requirement: Один immutable Markdown invocation
USW SHALL прочитать выбранный flow ровно один раз, вычислить identity из тех же
bytes, декодировать их как UTF-8 и передать модели отдельные неизменяемые
`flow_markdown` и `user_input`.

#### Scenario: Flow изменился после загрузки
- **WHEN** файл изменён после создания invocation
- **THEN** текущий invocation использует уже загруженный Markdown и прежнюю identity

### Requirement: Безопасное разрешение text flow
USW SHALL разрешать безопасное kebab-case имя только внутри выбранного local или
shared root, проверяя containment, каждый существующий path component, запрет
symlink и regular конечный файл. Traversal и final read SHALL выполняться
descriptor-relative без повторного pathname open после проверки компонента.

#### Scenario: Intermediate symlink
- **WHEN** любой компонент пути к flow является symbolic link
- **THEN** USW останавливается до чтения flow и model invocation

### Requirement: Модель следует тексту без machine guarantees
USW SHALL интерпретировать весь Markdown как человекочитаемый процесс до
`completed`, `failed`, `blocked`, `decision_required`, permission boundary или
явной паузы. Flow text MUST NOT предоставлять дополнительные полномочия.

#### Scenario: Неоднозначный structured marker
- **WHEN** `CALL`, `GATE`, `LOOP`, `PARALLEL` или prose допускает существенно разные действия
- **THEN** USW возвращает `decision_required`, а не parse error и не угадывает

### Requirement: Снятый runtime имеет понятную миграцию
USW SHALL отклонять `--experimental-structured` и retired internal commands до
mutation с указанием обычной команды `$usw-run-flow`.

#### Scenario: Старый structured вызов
- **WHEN** пользователь передаёт `--experimental-structured`
- **THEN** USW предлагает убрать flag и выполнить тот же Markdown как текстовый

### Requirement: Legacy FLOW state не используется
USW MUST NOT читать, изменять или удалять `.usw/FLOW.json` и SHALL показывать не
более одного предупреждения о его наличии за invocation.

#### Scenario: Legacy state существует
- **WHEN** text flow запускается при существующем `.usw/FLOW.json`
- **THEN** flow продолжает text execution, а legacy path остаётся неизменным
