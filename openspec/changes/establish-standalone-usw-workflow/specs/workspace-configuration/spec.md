## ADDED Requirements

### Requirement: Версионированная общая конфигурация
USW SHALL выбирать shared artifact behavior из project-root `usw.yaml`, где
`schema_version`, artifact provider, shared root, refinement root, flow root и
provider-neutral review root имеют детерминированный смысл. Defaults v1 SHALL
быть provider `standalone`, shared root `usw` и review root `usw/reviews`.

#### Scenario: Инициализация проекта без configuration
- **WHEN** пользователь инициализирует USW в проекте без `usw.yaml`
- **THEN** USW создаёт v1 configuration со standalone provider и безопасными
  default roots

#### Scenario: Неподдерживаемая версия configuration
- **WHEN** USW читает `usw.yaml` с неподдерживаемым `schema_version`
- **THEN** он сообщает версию и не записывает managed artifacts

### Requirement: Configured roots безопасны
USW MUST принимать только project-relative managed roots, которые остаются
внутри проекта через реальные directories и не проходят через symbolic links.
Он MUST отклонять absolute paths, parent traversal, symlinked managed paths и
конфликтующие writable roots до записи.

#### Scenario: Configuration выходит за пределы проекта
- **WHEN** configured root является absolute или содержит parent traversal за
  пределы проекта
- **THEN** initialization завершается ошибкой без создания или изменения
  managed files

#### Scenario: Managed root является symbolic link
- **WHEN** configured shared, review или local managed path проходит через
  symbolic link
- **THEN** initialization отклоняет path без записи через link

### Requirement: Review collection не зависит от planning provider
USW SHALL хранить receipts под настроенным USW review root независимо от
выбранного planning provider. Receipt MUST ссылаться на reviewed subject и MUST
NOT копировать или изменять provider artifacts.

#### Scenario: OpenSpec provider использует USW review root
- **WHEN** `artifacts.provider` равен `openspec` и создаётся review receipt
- **THEN** receipt записывается под configured review root, а `openspec/`
  остаётся неизменным

### Requirement: Standalone-инициализация не разрушает существующее состояние
Initialization SHALL создавать только отсутствующие standalone USW artifacts и
MUST NOT перезаписывать существующие configuration, shared artifacts, review
receipts или developer-local state.

#### Scenario: Повторная инициализация standalone workspace
- **WHEN** initialization снова запускается в валидном workspace
- **THEN** все существующие managed files остаются неизменными, а операция
  сообщает, что workspace уже существует

### Requirement: Существующий OpenSpec workspace только обнаруживается
Если standalone initialization находит `openspec/`, она SHALL сообщить о нём и
явном opt-in path, но MUST NOT выбрать OpenSpec provider или изменить OpenSpec
artifacts.

#### Scenario: Инициализация рядом с OpenSpec workspace
- **WHEN** `/usw-init` запускается без `usw.yaml` в проекте с валидным
  `openspec/` workspace
- **THEN** он создаёт standalone USW state, сообщает о найденном workspace и
  оставляет все OpenSpec files неизменными

### Requirement: Developer-local state остаётся приватным
USW SHALL хранить `.usw/HANDOFF.md` локально и под ignore rules, а shared state
под configured artifact и review roots SHALL оставаться пригодным для version
control.

#### Scenario: Local handoff может попасть в version control
- **WHEN** initialization обнаруживает tracked `.usw/HANDOFF.md` или
  недостаточные ignore rules
- **THEN** она завершается privacy error до записи state
