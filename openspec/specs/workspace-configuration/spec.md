# workspace-configuration Specification

## Purpose
TBD - created by archiving change establish-standalone-usw-workflow. Update Purpose after archive.
## Requirements
### Requirement: Версионированная общая конфигурация
USW SHALL выбирать shared artifact behavior из project-root `usw.yaml`, где
`schema_version`, artifact provider, shared artifact root, flow root и
provider-neutral review root имеют детерминированный смысл. Defaults v1 SHALL
быть provider `standalone`, shared root `usw`, flow root `usw/flows` и review
root `usw/reviews`.

`refinement.root` MUST NOT быть активным v1 configuration field.

#### Scenario: Инициализация проекта без configuration
- **WHEN** пользователь инициализирует USW в проекте без `usw.yaml`
- **THEN** USW создаёт v1 configuration со standalone provider и безопасными
  default roots

#### Scenario: Неподдерживаемая версия configuration
- **WHEN** USW читает `usw.yaml` с неподдерживаемым `schema_version`
- **THEN** он сообщает версию и не записывает managed artifacts

#### Scenario: Legacy refinement root присутствует
- **WHEN** v1 configuration содержит `refinement.root`
- **THEN** field не управляет новыми sessions и никакая automatic migration
  shared refinement data не выполняется

### Requirement: Configured roots безопасны
USW MUST принимать только project-relative artifact, flow и review roots,
которые остаются внутри проекта через реальные directories и не проходят через
symbolic links. Он MUST отклонять absolute paths, parent traversal, symlinked
managed paths и конфликтующие writable roots до записи.

При provider `standalone` flow и review roots MAY находиться внутри
`artifacts.root`, если они различны и не пересекаются друг с другом. Любое
другое равенство или ancestor/descendant overlap между writable roots, а также
совпадение или overlap с project root, `.git` либо `.usw`, MUST считаться
конфликтом.

#### Scenario: Configuration выходит за пределы проекта
- **WHEN** configured root является absolute или содержит parent traversal за
  пределы проекта
- **THEN** initialization завершается ошибкой без создания или изменения
  managed files

#### Scenario: Managed root является symbolic link
- **WHEN** configured artifact, flow, review или local managed path проходит через
  symbolic link
- **THEN** initialization отклоняет path без записи через link

#### Scenario: Standalone namespace содержит flow и review roots
- **WHEN** standalone configuration использует `artifacts.root: usw` и default
  flow/review roots под `usw/`
- **THEN** ожидаемое containment принимается, потому что flow и review roots
  различны и не пересекаются друг с другом

#### Scenario: Writable roots пересекаются
- **WHEN** review root совпадает с flow root либо один writable root содержит
  другой недопустимым образом
- **THEN** configuration отклоняется как конфликтующая до любой managed write

#### Scenario: OpenSpec использует provider-specific planning default
- **WHEN** configuration явно выбирает provider `openspec` и не задаёт
  `artifacts.root`
- **THEN** planning root разрешается как `openspec`, а flow и review roots
  остаются `usw/flows` и `usw/reviews`

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
Если standalone initialization находит real `openspec/` directory, она SHALL
сообщить directory hint и explicit opt-in path, но MUST NOT считать directory
валидированным workspace, выбрать OpenSpec provider или начать writes только
из-за detection.

Explicit standalone artifact, flow или review root под `openspec/**` SHALL
оставаться авторитетным user-selected writable root и MUST NOT отклоняться
только из-за имени namespace.

#### Scenario: Инициализация рядом с OpenSpec directory
- **WHEN** `/usw-init` запускается со standalone provider, default roots и real
  `openspec/` directory
- **THEN** он создаёт standalone USW state, сообщает directory hint и оставляет
  все OpenSpec files неизменными

#### Scenario: Пользователь явно выбрал standalone root под `openspec`
- **WHEN** standalone configuration явно задаёт managed root под `openspec/**`
- **THEN** initialization создаёт там только отсутствующие standalone artifacts
  и сохраняет все существующие files

### Requirement: Developer-local state остаётся приватным
USW SHALL хранить `.usw/HANDOFF.md` и clarification notes под `.usw/`, а shared
state — под configured artifact и review roots. Initialization SHALL создавать
`.usw/.gitignore` как локальный default, но Git tracking policy SHALL
принадлежать пользователю и MUST NOT блокировать initialization.

#### Scenario: Local state уже tracked
- **WHEN** initialization обнаруживает существующий tracked `.usw/**` entry
  либо custom ignore rules
- **THEN** он сохраняет state и продолжает initialization без изменения
  repository tracking policy
