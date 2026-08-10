# flow-examples Specification

## Purpose
Define the exact non-normative text-first examples installed with USW.

## Requirements

### Requirement: Initialization installs exactly four flow examples
USW SHALL package and initialize exactly `chat-review.md`, `dev-test.md`,
`plan-small-steps.md` and `refine-intent.md` under `<flows.root>/examples/`.
The directory MUST NOT provide a hidden runtime fallback.

#### Scenario: Fresh project receives examples
- **WHEN** initialization finds either example absent
- **THEN** it creates the missing file under `<flows.root>/examples/`

### Requirement: Every installed example is explicitly non-normative
Each example SHALL state that it is guidance, MUST NOT be executed in place and
SHALL instruct the user to copy it to `<flows.root>/<name>.md` before execution.

#### Scenario: User reads an example
- **WHEN** a user opens an installed example
- **THEN** its example status and copy-before-use path are clear

### Requirement: Examples не обещают machine execution
Each example SHALL be ordinary readable Markdown and MUST NOT claim strict
validation, a machine cursor, deterministic control flow or a mandatory role
lifecycle.

#### Scenario: Example content is inspected
- **WHEN** package tests inspect both assets
- **THEN** they describe a model-executed process and an ordinary run command

### Requirement: Packaged examples объявляют внешние CALL dependencies
Каждый обязательный `CALL SKILL` в packaged example SHALL быть объявлен как
`external`. Декларация external dependency SHALL означать намеренную интеграцию
и MUST NOT приводить к её автоматической установке. Процесс, который можно
выразить самим Markdown-flow, MUST NOT требовать отдельного bundled skill.

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
Dependency test SHALL извлекать только external dependency declarations и
буквальные `CALL SKILL` references из packaged examples. Он MUST NOT валидировать порядок
действий, ветвления, voting semantics или исполнять flow.

#### Scenario: Human-readable control text меняется
- **WHEN** prose или порядок действий example меняется без изменения
  dependency declarations и `CALL SKILL` references
- **THEN** dependency test не требует normalized plan или runtime schema
