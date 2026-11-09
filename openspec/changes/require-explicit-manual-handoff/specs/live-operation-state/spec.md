## ADDED Requirements

### Requirement: Ручной handoff требует прямого вызова человека
Вне служебного вызова из flow USW SHALL активировать handoff только по прямому
вызову человеком команды, skill или явной просьбе использовать handoff.
Общие просьбы сохранить состояние или продолжить работу MUST NOT активировать
handoff и MUST NOT приводить к чтению или изменению его state.

#### Scenario: Общая просьба сохранить состояние
- **WHEN** вне flow пользователь просит сохранить состояние без обращения к handoff
- **THEN** агент обрабатывает обычный запрос сохранения, уточняя destination
  при необходимости, и не обращается к HANDOFF или operation documents

#### Scenario: Общая просьба продолжить работу
- **WHEN** вне flow пользователь просит продолжить работу, не вызывая handoff
- **THEN** агент не выполняет Show/Resume и не обращается к handoff state

#### Scenario: Пользователь прямо вызывает handoff
- **WHEN** человек вызывает `/usw-handoff`, `/usw-resume`,
  `$usw-manage-handoff` или явно просит использовать handoff
- **THEN** соответствующий режим выполняется по действующему контракту выбора
  operation и конфигурации

### Requirement: Служебный handoff внутри flow следует конфигурации
Прямой ручной вызов MUST NOT требоваться для служебных Begin/Outcome и read-only
parent verification, предусмотренных контрактом запуска flow. Эти вызовы SHALL
следовать effective `handoff`; при `false` handoff state MUST NOT читаться или
изменяться.

#### Scenario: Flow запущен с включённым handoff
- **WHEN** пользователь запустил flow с effective `handoff: true`
- **THEN** runner выполняет предусмотренные контрактом служебные вызовы без
  отдельного ручного обращения к handoff

#### Scenario: Handoff отключён
- **WHEN** прямой ручной вызов или запуск flow имеет effective `handoff: false`
- **THEN** `.usw/HANDOFF.md`, operation documents и candidates не читаются и
  не изменяются
