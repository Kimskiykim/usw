## ADDED Requirements

### Requirement: Packaged examples объявляют CALL dependencies
Каждый packaged flow example SHALL иметь человекочитаемый dependency block.
Каждый обязательный `CALL SKILL` SHALL быть объявлен как `bundled` либо
`external`. Декларация external dependency SHALL означать намеренную
интеграцию и MUST NOT приводить к её автоматической установке.

#### Scenario: Bundled dependency
- **WHEN** example объявляет `CALL SKILL usw-structured-review` как bundled
- **THEN** package tests подтверждают наличие `skills/usw-structured-review`
  и его включение в standalone installer

#### Scenario: External dependency
- **WHEN** example объявляет `CALL SKILL ponytail-review` как external
- **THEN** package tests принимают декларацию без требования включить
  `ponytail-review` в USW package

#### Scenario: Dependency не объявлена
- **WHEN** обязательный `CALL SKILL` в packaged example отсутствует в
  dependency block
- **THEN** статическая package-проверка завершается ошибкой

### Requirement: Chat-review example демонстрирует adaptive quorum
Packaged `chat-review.md` SHALL показывать profile-based reviewers,
`--reviewers auto|2|3`, bounded escalation от двух reviewer-ов к третьему,
explicit per-finding voting и отдельные human decisions.

#### Scenario: Пользователь копирует chat-review example
- **WHEN** пользователь адаптирует example в runnable flow
- **THEN** текст содержит полный adaptive review contract без обещаний parser,
  deterministic scheduler или machine cursor

### Requirement: Dependency test не становится runtime parser
Dependency test SHALL извлекать только dependency declarations и буквальные
`CALL SKILL` references из packaged examples. Он MUST NOT валидировать порядок
действий, ветвления, voting semantics или исполнять flow.

#### Scenario: Human-readable control text меняется
- **WHEN** prose или порядок действий example меняется без изменения
  dependency declarations и `CALL SKILL` references
- **THEN** dependency test не требует normalized plan или runtime schema
