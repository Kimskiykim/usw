# markdown-flow-composition Specification

## Purpose
Define ordinary and structured text-first Markdown authoring.

## Requirements

### Requirement: Ordinary Markdown является форматом по умолчанию
`usw-create-flow` SHALL create ordinary Markdown without a version or DSL unless
the user explicitly selects `-s` or `--structured`. Both selectors SHALL choose
the same `version-2` authoring style.

#### Scenario: Structured selector отсутствует
- **WHEN** a user creates a flow without `-s` or `--structured`
- **THEN** the saved file is ordinary Markdown

#### Scenario: Structured selector передан
- **WHEN** a user creates a flow with either structured selector
- **THEN** the saved file uses the same readable `version-2` convention

### Requirement: Составление завершается без исполнения
`usw-create-flow` SHALL write only the selected safe Markdown file and MUST NOT
execute the flow or any action described by it.

#### Scenario: Flow создан
- **WHEN** the requested Markdown has been saved successfully
- **THEN** the skill reports its name, origin and ordinary `$usw-run-flow` command

### Requirement: Version-2 является authoring convention
Structured authoring SHALL use `version-2` and only applicable `CALL`, `GATE`,
`LOOP` and `PARALLEL` markers to make intent easy for a human and model to read.
The convention MUST NOT promise parser validation, deterministic transitions,
atomic parallelism, durable cursor, write authority or machine guarantees.

#### Scenario: Control marker не нужен
- **WHEN** the described process has no decision, loop or parallel work
- **THEN** authoring does not add the corresponding marker for uniformity

#### Scenario: Existing version-2 is revised
- **WHEN** a structured flow is updated
- **THEN** its markers remain readable guidance and the flow is not passed to a validator

### Requirement: Очевидная структура может быть выведена из описания
The author MAY make an unambiguous order, check, branch, bounded return or
independent work explicit in Markdown. If materially different interpretations
change behavior, actor or external effect, the author MUST request the missing
decision rather than invent it.

#### Scenario: Description has two material meanings
- **WHEN** the requested process does not determine which consequential action to take
- **THEN** authoring asks one necessary question before saving that behavior

### Requirement: Flow text не предоставляет полномочия
Authoring SHALL preserve the user's requested process while making clear that
Markdown cannot authorize external, destructive or otherwise permission-bound
actions.

#### Scenario: Flow mentions deployment
- **WHEN** a flow says to deploy a result
- **THEN** later execution still requires the normal user and platform permission boundary
