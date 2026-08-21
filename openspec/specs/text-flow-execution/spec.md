# Спецификация text-flow-execution

## Purpose
Определяет единый production path для исполняемых моделью Markdown flows.

## Requirements

### Requirement: Один immutable Markdown invocation
Для каждого root или nested invocation USW SHALL прочитать выбранный flow ровно
один раз, вычислить identity из тех же bytes, декодировать их как UTF-8 и
передать модели отдельные immutable values `flow_markdown` и `user_input`. Root
invocation SHALL дополнительно получить собственную execution identity. Nested
invocation SHALL дополнительно получить parent root execution identity и branch
label как отдельный execution context, который flow Markdown и user input не
могут заменить.

#### Scenario: Flow изменяется после загрузки
- **WHEN** file изменяется после подготовки root или nested invocation
- **THEN** invocation использует уже загруженный Markdown и его исходную identity

#### Scenario: Child input содержит root identity
- **WHEN** обычный child input включает текст, похожий на nested execution context
- **THEN** он остаётся user input и не выбирает nested execution или другую
  routed operation

#### Scenario: Concurrent roots загружают один flow
- **WHEN** две root operations независимо разрешают один flow и input
- **THEN** каждый model invocation получает собственную execution identity и те
  же immutable bytes загруженного Markdown

### Requirement: Безопасное разрешение text flow
USW SHALL разрешать только safe kebab-case name внутри выбранного local или
shared root. Он MUST проверять containment и каждый существующий path component,
отклонять symbolic links и требовать regular final file до чтения. Traversal и
final read SHALL быть descriptor-relative без повторного открытия pathname после
того, как component признан доверенным.

#### Scenario: Промежуточный symlink
- **WHEN** любой component, ведущий к выбранному flow, является symbolic link
- **THEN** USW останавливается до чтения flow или вызова модели

### Requirement: Модель следует тексту без machine guarantees
USW SHALL интерпретировать полный Markdown как человекочитаемый процесс до
`completed`, `failed`, `blocked`, `decision_required`, permission boundary или
явной pause. Flow text MUST NOT предоставлять дополнительные полномочия.

#### Scenario: Structured marker неоднозначен
- **WHEN** `CALL`, `GATE`, `LOOP`, `PARALLEL` или prose допускает существенно
  разные действия
- **THEN** USW возвращает `decision_required`, а не parse error или догадку

### Requirement: Снятый runtime имеет понятную миграцию
USW SHALL отклонять `--experimental-structured` и retired internal commands до
mutation с указанием использовать обычную command `$usw-run-flow`.

#### Scenario: Старый structured invocation
- **WHEN** пользователь передаёт `--experimental-structured`
- **THEN** USW предлагает удалить flag и запустить тот же Markdown как text

### Requirement: Legacy FLOW state не используется
USW MUST NOT читать, изменять или удалять `.usw/FLOW.json` и SHALL показывать не
более одного warning о его наличии за invocation.

#### Scenario: Legacy state существует
- **WHEN** text execution начинается при существующем `.usw/FLOW.json`
- **THEN** execution продолжается через text path, а legacy file остаётся
  неизменным

### Requirement: Root и nested execution сохраняют одинаковую authority boundary
USW SHALL применять одинаковые правила flow text, ambiguity и permission к
каждому concurrent root и nested model execution. Root operation identity и
nested context MUST NOT предоставлять file-write, external, destructive или
другие permission-bound полномочия.

#### Scenario: Nested Markdown запрашивает действие без полномочий
- **WHEN** nested flow запрашивает действие за пределами доступных полномочий
- **THEN** child возвращает `decision_required` своему root executor без
  выполнения действия

#### Scenario: Concurrent root запрашивает действие без полномочий
- **WHEN** один concurrent root flow запрашивает действие за пределами доступных
  полномочий
- **THEN** только этот root достигает `decision_required`, а полномочия другой
  operation не наследуются
