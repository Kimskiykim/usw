# Спецификация markdown-flow-composition

## Purpose
Определяет обычный и structured text-first authoring в Markdown.

## Requirements

### Requirement: Обычный Markdown является форматом по умолчанию
`usw-create-flow` SHALL создавать обычный Markdown без version или DSL, если
пользователь явно не выбрал `-s` или `--structured`. Оба selectors SHALL выбирать
один и тот же authoring style `version-2`.

#### Scenario: Structured selector отсутствует
- **WHEN** пользователь создаёт flow без `-s` или `--structured`
- **THEN** сохранённый file является обычным Markdown

#### Scenario: Structured selector передан
- **WHEN** пользователь создаёт flow с любым structured selector
- **THEN** сохранённый file использует ту же readable convention `version-2`

### Requirement: Составление завершается без исполнения
`usw-create-flow` SHALL записывать только выбранный safe Markdown file и MUST NOT
исполнять flow или любое описанное им действие.

#### Scenario: Flow создан
- **WHEN** запрошенный Markdown успешно сохранён
- **THEN** skill сообщает его name, origin и обычную command `$usw-run-flow`

### Requirement: Version-2 является authoring convention
Structured authoring SHALL использовать `version-2` и только применимые markers
`CALL`, `GATE`, `LOOP` и `PARALLEL`, чтобы intent было легко читать человеку и
модели. Convention MUST NOT обещать parser validation, deterministic
transitions, atomic parallelism, durable cursor, write authority или machine
guarantees.

#### Scenario: Control marker не нужен
- **WHEN** описанный процесс не содержит decision, loop или parallel work
- **THEN** authoring не добавляет соответствующий marker ради единообразия

#### Scenario: Существующий version-2 изменяется
- **WHEN** structured flow обновляется
- **THEN** его markers остаются readable guidance, а flow не передаётся validator

### Requirement: Очевидная структура может быть выведена из описания
Author MAY явно отразить в Markdown однозначные order, check, branch, bounded
return или independent work. Если существенно разные interpretation меняют
behavior, actor или external effect, author MUST запросить недостающее решение,
а не выдумывать его.

#### Scenario: Описание имеет два существенных смысла
- **WHEN** запрошенный процесс не определяет, какое consequential action выполнить
- **THEN** authoring задаёт один необходимый вопрос до сохранения этого behavior

### Requirement: Flow text не предоставляет полномочия
Authoring SHALL сохранять запрошенный пользователем процесс и явно показывать,
что Markdown не может разрешать external, destructive или иные permission-bound
действия.

#### Scenario: Flow упоминает deployment
- **WHEN** flow указывает выполнить deploy результата
- **THEN** последующее execution всё равно требует обычную user и platform
  permission boundary
