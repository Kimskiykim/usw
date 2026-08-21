# Спецификация flow-examples

## Purpose
Определяет точные non-normative text-first examples, устанавливаемые с USW.

## Requirements

### Requirement: Initialization устанавливает ровно четыре flow examples
USW SHALL поставлять и инициализировать ровно `chat-review.md`, `dev-test.md`,
`plan-small-steps.md` и `refine-intent.md` под `<flows.root>/examples/`.
Directory MUST NOT предоставлять скрытый runtime fallback.

#### Scenario: Новый project получает examples
- **WHEN** initialization обнаруживает отсутствие любого example
- **THEN** она создаёт недостающий file под `<flows.root>/examples/`

### Requirement: Каждый установленный example явно является non-normative
Каждый example SHALL указывать, что он является guidance, MUST NOT исполняться
на месте и SHALL предлагать пользователю скопировать его в
`<flows.root>/<name>.md` до execution.

#### Scenario: Пользователь читает example
- **WHEN** пользователь открывает установленный example
- **THEN** его status example и path для copy-before-use понятны

### Requirement: Examples не обещают machine execution
Каждый example SHALL быть обычным читаемым Markdown и MUST NOT заявлять strict
validation, machine cursor, deterministic control flow или mandatory role
lifecycle.

#### Scenario: Content example проверяется
- **WHEN** package tests проверяют оба assets
- **THEN** они описывают исполняемый моделью процесс и обычную run command

### Requirement: Packaged examples объявляют внешние CALL dependencies
Каждый обязательный `CALL SKILL` в packaged example SHALL быть объявлен как
`external`. Декларация external dependency SHALL означать намеренную интеграцию
и MUST NOT приводить к её автоматической установке. Процесс, который можно
выразить самим Markdown flow, MUST NOT требовать отдельного bundled skill.

#### Scenario: Внешняя dependency
- **WHEN** example объявляет `CALL SKILL ponytail-review` как external
- **THEN** package tests принимают декларацию без требования включить
  `ponytail-review` в USW package

#### Scenario: Dependency не объявлена
- **WHEN** обязательный `CALL SKILL` в packaged example отсутствует в dependency
  block
- **THEN** статическая package-проверка завершается ошибкой

### Requirement: Example chat-review демонстрирует adaptive quorum
Packaged `chat-review.md` SHALL показывать profile-based reviewers,
`--reviewers auto|2|3`, bounded escalation от двух reviewers к третьему, explicit
per-finding voting и отдельные human decisions.

#### Scenario: Пользователь копирует example chat-review
- **WHEN** пользователь адаптирует example в runnable flow
- **THEN** текст содержит полный adaptive review contract без обещаний parser,
  deterministic scheduler или machine cursor

### Requirement: Dependency test не становится runtime parser
Dependency test SHALL извлекать только external dependency declarations и
буквальные references `CALL SKILL` из packaged examples. Он MUST NOT валидировать
порядок действий, ветвления, voting semantics или исполнять flow.

#### Scenario: Human-readable control text изменяется
- **WHEN** prose или порядок действий example изменяется без изменения dependency
  declarations и references `CALL SKILL`
- **THEN** dependency test не требует normalized plan или runtime schema
