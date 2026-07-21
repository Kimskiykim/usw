## ADDED Requirements

### Requirement: OpenSpec provider выбирается явно
USW SHALL использовать OpenSpec-owned planning artifacts только когда общая
конфигурация явно выбирает OpenSpec provider. Наличие `openspec/` MUST NOT менять
provider selection.

#### Scenario: OpenSpec существует при standalone configuration
- **WHEN** проект содержит `openspec/`, но `usw.yaml` выбирает `standalone`
- **THEN** USW использует standalone shared artifacts и не выполняет OpenSpec write

#### Scenario: Configuration выбирает OpenSpec
- **WHEN** валидная общая configuration явно выбирает OpenSpec provider
- **THEN** USW разрешает поддерживаемые planning roles из OpenSpec workspace
  вместо создания standalone-дубликатов

### Requirement: Отсутствующая provider capability видима
Compatibility layer MUST различать отсутствующий required artifact,
отсутствующий optional artifact и неподдерживаемую provider capability. Он MUST
NOT имитировать недоступное поведение созданием standalone planning artifacts.

#### Scenario: Required OpenSpec artifact отсутствует
- **WHEN** flow запрашивает required role, которую выбранный OpenSpec workspace
  не предоставляет
- **THEN** flow останавливается с provider contract error и не создаёт fallback
  artifact

#### Scenario: OpenSpec adapter ещё не подключён
- **WHEN** configuration выбирает provider `openspec`, но общий artifact
  capability не имеет установленного OpenSpec adapter
- **THEN** capability возвращает structured `unsupported_provider_operation`
  до записи и не выполняет standalone fallback

### Requirement: Standalone runtime не требует OpenSpec
Packaging и standalone commands MUST работать без установленного OpenSpec
executable или library. OpenSpec MAY устанавливаться только в development и CI
compatibility environments.

#### Scenario: Standalone-инициализация без OpenSpec
- **WHEN** пользователь устанавливает USW без OpenSpec и инициализирует
  standalone project
- **THEN** initialization и standalone artifact workflows остаются доступными

### Requirement: OpenSpec artifact frontier соблюдает role ownership
При `spec-driven` provider Analysis SHALL завершать `proposal` и capability
`specs`, а Development SHALL завершать technical `design` и `tasks` через
нативный artifact graph.

#### Scenario: Analysis передаёт незавершённый aggregate change
- **WHEN** Analysis завершил `proposal` и `specs`, status `design` равен `ready`,
  файл `design.md` отсутствует, а status `tasks` равен `blocked`
- **THEN** USW разрешает Analysis handoff без вызова bundled `openspec-propose`

#### Scenario: Development принимает Analysis handoff
- **WHEN** Development принимает handoff при status `design: ready` и
  отсутствующем `design.md`
- **THEN** оно отдельно запрашивает instructions и создаёт `design.md`, повторно
  читает status, а после перехода `tasks` в `ready` отдельно создаёт `tasks.md`

### Requirement: Review receipts не изменяют OpenSpec workspace
При OpenSpec provider USW SHALL хранить reviewer receipts в настроенной
provider-neutral USW review collection и SHALL только ссылаться на OpenSpec
subjects.

OpenSpec adapter MUST использовать общий provider-neutral receipt writer, а не
реализовывать отдельное OpenSpec-backed review storage.

#### Scenario: Review относится к OpenSpec change
- **WHEN** reviewer создаёт receipt для OpenSpec-backed subject
- **THEN** receipt записывается под USW review root, а OpenSpec artifacts остаются
  неизменными

### Requirement: Совместимость проверяется на реальной pinned версии OpenSpec
CI MUST выполнять release-blocking compatibility scenarios с точной версией
реальной установки OpenSpec `1.6.0`, записанной в одном version-controlled
source of truth.

#### Scenario: Pinned compatibility не проходит
- **WHEN** required compatibility scenario завершается ошибкой на OpenSpec `1.6.0`
- **THEN** release-blocking job завершается ошибкой и USW не считается готовым к
  release

### Requirement: V1 имеет закрытый набор provider adapters
V1 SHALL поддерживать только встроенные `standalone` и `openspec` adapters.
Общий adapter interface MUST быть внутренней implementation boundary и MUST NOT
объявляться declarative path mapping, executable plugin API или произвольным
сторонним provider contract.

#### Scenario: Выбран неизвестный provider
- **WHEN** configuration запрашивает provider вне `standalone` и `openspec`
- **THEN** config validation возвращает `unsupported_provider` до runtime
  dispatch и не использует standalone fallback

#### Scenario: Встроенный provider не реализует operation
- **WHEN** валидно выбран `standalone` или `openspec`, но adapter либо required
  operation недоступны
- **THEN** runtime capability возвращает `unsupported_provider_operation` до
  записи и не использует fallback другого provider

### Requirement: Latest compatibility probe видим и не блокирует release
CI SHALL выполнять применимые compatibility scenarios с latest OpenSpec в
отдельной job, ошибка которой видима, но не блокирует USW release.

#### Scenario: Latest OpenSpec нарушает совместимость
- **WHEN** pinned compatibility проходит, а latest probe завершается ошибкой
- **THEN** release gate остаётся удовлетворённым, а ошибка и tested version
  остаются видимыми для triage

### Requirement: Pinned version изменяется намеренно
Pinned OpenSpec version SHALL иметь один version-controlled source of truth и
MUST обновляться явно вместе с успешным compatibility evidence.

#### Scenario: Обновление pinned compatibility target
- **WHEN** maintainers меняют pinned OpenSpec version
- **THEN** change называет новую версию, а release-blocking scenarios проходят
  до принятия изменения
