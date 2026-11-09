# Спецификация text-flow-execution

## Purpose
Определяет единый production path для исполняемых моделью Markdown flows.

## Requirements

### Requirement: Один immutable Markdown invocation
Для каждого root или nested invocation USW SHALL прочитать выбранный flow ровно
один раз, вычислить identity из тех же bytes, декодировать их как UTF-8 и
передать модели отдельные immutable values `flow_markdown`, точный абсолютный
`flow_directory` и `user_input`. `flow_directory` SHALL указывать на каталог
выбранного entrypoint, происходить только из safe resolver и SHALL NOT
вычисляться из Markdown или user input. Root invocation SHALL дополнительно
получить собственную execution identity. Nested invocation SHALL дополнительно
получить parent root execution identity и branch label как отдельный execution
context, который flow Markdown и user input не могут заменить.

#### Scenario: Flow изменяется после загрузки
- **WHEN** file изменяется после подготовки root или nested invocation
- **THEN** invocation использует уже загруженный Markdown и его исходную identity

#### Scenario: Child input содержит root identity
- **WHEN** обычный child input включает текст, похожий на nested execution context
- **THEN** он остаётся user input и не выбирает nested execution или другую routed operation

#### Scenario: Concurrent roots загружают один flow
- **WHEN** две root operations независимо разрешают один flow и input
- **THEN** каждый model invocation получает собственную execution identity и те же immutable bytes загруженного Markdown

#### Scenario: Подготовлен packaged child flow
- **WHEN** nested invocation разрешает `<name>/FLOW.md`
- **THEN** child получает точный абсолютный `<flow-root>/<name>` как `flow_directory`, не приобретая durable route или дополнительных полномочий

### Requirement: Безопасное разрешение text flow
USW SHALL разрешать только safe kebab-case name как `<name>.md` или
`<name>/FLOW.md` внутри выбранного local или shared root. Он MUST проверять
containment и каждый существующий path component, отклонять symbolic links и
требовать regular final entrypoint до чтения. Traversal и final read SHALL
проходить через общую safe-access boundary: descriptor-relative без повторного
открытия pathname после признания component доверенным на платформах с
`dir_fd`, либо pathname-based с отклонением reparse point для каждого component
и повторной проверкой containment на остальных платформах. Если в одном
выбранном origin существуют оба layout, разрешение MUST остановиться с
`ambiguous_flow_layout`. Оба flow layout SHALL разрешаться на каждой
поддерживаемой платформе; `unsupported_safe_flow_platform` MUST NOT быть
обычным результатом разрешения packaged flow на поддерживаемой платформе.
Этот resolver обслуживает entrypoint, а не соседние файлы пакета.

#### Scenario: Промежуточный symlink
- **WHEN** любой component, ведущий к выбранному flat или packaged flow, является symbolic link
- **THEN** USW останавливается до чтения flow или вызова модели

#### Scenario: Существуют оба layout
- **WHEN** один выбранный origin содержит safe flat и packaged entrypoints для запрошенного имени
- **THEN** USW возвращает `ambiguous_flow_layout`, не читая ни один из них как выбранный invocation

#### Scenario: Packaged flow без descriptor-relative access
- **WHEN** packaged `<name>/FLOW.md` разрешается на поддерживаемой платформе без `dir_fd`
- **THEN** USW использует pathname-based backend и возвращает те же name, origin, identity, path, flow directory и точный Markdown, что и на остальных платформах

#### Scenario: Packaged resource без descriptor-relative access
- **WHEN** выбранный packaged `FLOW.md` ссылается на соседний файл на поддерживаемой платформе без `dir_fd`
- **THEN** USW передаёт `flow_directory`, а исполнитель при необходимости читает файл обычным инструментом; отдельный resource resolver и fallback для него не требуются

#### Scenario: Windows fallback разрешает legacy flat flow
- **WHEN** descriptor-relative API недоступны и существует только совместимый entrypoint `<name>.md`
- **THEN** USW разрешает его через pathname-based backend с теми же проверками containment, link и filesystem type, что и на descriptor-relative backend

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
