# Спецификация workspace-configuration

## Purpose
Определяет безопасные версионированные project roots, используемые USW.
## Requirements
### Requirement: Версионированная общая конфигурация
USW SHALL выбирать shared artifact behavior из project-root `usw.yaml`, где
`schema_version`, shared artifact root, flow root и review root имеют
детерминированный смысл. Defaults v1 SHALL быть shared root `usw`, flow root
`usw/flows` и review root `usw/reviews`.

`artifacts.provider` и `refinement.root` MUST NOT быть активными v1
configuration fields.

#### Scenario: Инициализация проекта без configuration
- **WHEN** пользователь инициализирует USW в проекте без `usw.yaml`
- **THEN** USW создаёт v1 configuration с безопасными default roots

#### Scenario: Неподдерживаемая версия configuration
- **WHEN** USW читает `usw.yaml` с неподдерживаемым `schema_version`
- **THEN** он сообщает версию и не записывает managed artifacts

#### Scenario: Legacy refinement root присутствует
- **WHEN** v1 configuration содержит `refinement.root`
- **THEN** field не управляет новыми sessions и никакая automatic migration
  shared refinement data не выполняется

#### Scenario: Legacy provider field присутствует
- **WHEN** v1 configuration содержит `artifacts.provider`
- **THEN** configuration отклоняется до managed writes с указанием удалить field

### Requirement: Корень проекта задаётся явно
USW SHALL использовать переданный корень открытого проекта буквально и MUST
NOT выбирать другой workspace по наличию `.git` в родительском каталоге.

#### Scenario: Проект вложен в другой Git repository
- **WHEN** USW получает вложенную открытую папку как project root
- **THEN** configuration и managed paths разрешаются внутри неё без ancestor
  discovery

### Requirement: Configured roots безопасны
USW MUST принимать только project-relative artifact, flow и review roots,
которые остаются внутри проекта через реальные directories и не проходят через
symbolic links. Он MUST отклонять absolute paths, parent traversal, symlinked
managed paths и конфликтующие writable roots до записи.

Flow и review roots MAY находиться внутри `artifacts.root`, если они различны и
не пересекаются друг с другом. Любое другое равенство или ancestor/descendant
overlap между writable roots, а также совпадение или overlap с project root,
`.git` либо `.usw`, MUST считаться конфликтом.

#### Scenario: Configuration выходит за пределы проекта
- **WHEN** configured root является absolute или содержит parent traversal за
  пределы проекта
- **THEN** initialization завершается ошибкой без создания или изменения
  managed files

#### Scenario: Managed root является symbolic link
- **WHEN** configured artifact, flow, review или local managed path проходит через
  symbolic link
- **THEN** initialization отклоняет path без записи через link

#### Scenario: Artifact namespace содержит flow и review roots
- **WHEN** configuration использует `artifacts.root: usw` и default
  flow/review roots под `usw/`
- **THEN** ожидаемое containment принимается, потому что flow и review roots
  различны и не пересекаются друг с другом

#### Scenario: Writable roots пересекаются
- **WHEN** review root совпадает с flow root либо один writable root содержит
  другой недопустимым образом
- **THEN** configuration отклоняется как конфликтующая до любой managed write

### Requirement: Review collection использует настроенный root
USW SHALL хранить receipts под настроенным review root. Receipt MUST ссылаться
на reviewed subject и MUST NOT копировать reviewed artifacts.

#### Scenario: Создаётся review receipt
- **WHEN** review action создаёт receipt для проверенного subject
- **THEN** receipt записывается под configured review root

### Requirement: Инициализация не разрушает существующее состояние
Initialization SHALL создавать только отсутствующие USW artifacts и
MUST NOT перезаписывать существующие configuration, shared artifacts, review
receipts или developer-local state.

#### Scenario: Повторная инициализация workspace
- **WHEN** initialization снова запускается в валидном workspace
- **THEN** все существующие managed files остаются неизменными, а операция
  сообщает, что workspace уже существует

### Requirement: Developer-local state остаётся приватным
USW SHALL хранить enabled `.usw/HANDOFF.md` и clarification notes под `.usw/`,
а shared state — под configured artifact и review roots. Initialization SHALL
создавать `.usw/.gitignore` как локальный default, но Git tracking policy SHALL
принадлежать пользователю и MUST NOT блокировать initialization.

#### Scenario: Local state уже tracked
- **WHEN** initialization обнаруживает существующий tracked `.usw/**` entry
  либо custom ignore rules
- **THEN** он сохраняет state и продолжает initialization без изменения
  repository tracking policy

### Requirement: Handoff включается top-level boolean
`usw.yaml` SHALL принимать необязательное top-level поле `handoff` только как
boolean. Отсутствующее поле SHALL означать `true`; schema version остаётся `1`.

#### Scenario: Обратно совместимая configuration
- **WHEN** существующий `usw.yaml` не содержит `handoff`
- **THEN** USW включает handoff

#### Scenario: Handoff явно отключён
- **WHEN** `handoff: false`
- **THEN** run, init, handoff и resume не требуют, не читают и не изменяют `HANDOFF.md`

#### Scenario: Неверный тип
- **WHEN** `handoff` является строкой, числом или mapping
- **THEN** configuration validation завершается наблюдаемой ошибкой
