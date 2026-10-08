## MODIFIED Requirements

### Requirement: Неподдерживаемое содержимое HANDOFF отклоняется
При включённом handoff runtime SHALL проверять `.usw/HANDOFF.md` только как
router. Иной формат, включая прежний generic single-state HANDOFF, SHALL
отклоняться ошибкой валидации без изменения bytes `.usw/HANDOFF.md`, operation
documents и candidates и без автоматического преобразования состояния.

#### Scenario: Файл другого формата
- **WHEN** handoff-команда читает файл, который не является валидным router
- **THEN** команда возвращает ошибку валидации, а bytes HANDOFF, operation
  documents и candidates остаются неизменными

#### Scenario: Старый single-state HANDOFF
- **WHEN** команда получает прежний single-state HANDOFF со status `idle`
  или non-idle status
- **THEN** файл отклоняется без преобразования в router и без создания
  operation document

## ADDED Requirements

### Requirement: Устаревшая форма operation document отклоняется
Runtime SHALL принимать только operation documents с обязательными `Summary`,
`Started` и `Workspace`. Старые документы без этих полей SHALL отклоняться
ошибкой валидации до изменения router, documents и candidates. Runtime MUST NOT
выводить недостающие поля из input или преобразовывать старый document при записи.

#### Scenario: Старый документ читается
- **WHEN** Show, Resume или parent verification получает зарегистрированный
  operation document без одного из обязательных recovery fields
- **THEN** операция возвращает ошибку валидации без изменения состояния

#### Scenario: Старый документ изменяется
- **WHEN** Begin, Outcome, Save, Finish или Cleanup затрагивает старый
  operation document без обязательных recovery fields
- **THEN** команда возвращает ошибку валидации, сохраняет router, documents
  и candidates и не записывает восстановленные исторические поля

#### Scenario: Старый candidate сохраняется
- **WHEN** Save получает candidate без обязательных recovery fields для
  актуального operation document
- **THEN** candidate отклоняется, а router, document и candidate остаются неизменными

## REMOVED Requirements

### Requirement: Generic single-state handoff мигрирует безопасно
**Reason**: Владелец отказался от поддержки старых установок и поручил удалить
миграцию сейчас.
**Migration**: Автоматическое преобразование удаляется. Старые пользовательские
файлы сохраняются без изменения; для дальнейшей работы нужен актуальный routed
формат. Новая команда конвертации не вводится.

### Requirement: Enriched recovery context остаётся backwards-compatible
**Reason**: Поддержка старых operation documents и их автоматическое дополнение
recovery fields больше не требуется.
**Migration**: Документы без обязательных recovery fields сохраняются на диске,
но отклоняются. Актуальные документы, включая уже сохранённые явные `unknown`,
продолжают использоваться без изменения исторических фактов.
