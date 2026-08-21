# Спецификация intent-clarification

## Purpose
Определяет clarification намерения как обычный адаптируемый Markdown flow, а не
как установленный backend skill.

## Requirements

### Requirement: Clarification намерения является packaged example flow
USW SHALL поставлять `refine-intent.md` под `<flows.root>/examples/`. Он SHALL
уточнять не более одного существенного решения за один ход пользователя и MUST
NOT начинать planning или implementation.

#### Scenario: Пользователь копирует example
- **WHEN** пользователь копирует `refine-intent.md` в runnable flow path
- **THEN** flow можно адаптировать и исполнить через обычный path `usw-run-flow`
  без skill или command `usw-refine-intent`

### Requirement: Clarification state является local и minimal
Example SHALL использовать один developer-local Markdown file под
`.usw/refinements/` для подтверждённых фактов, предположений, открытых вопросов,
решений и текущей формулировки. Он MUST NOT считать этот file backlog,
specification, planning state или evidence завершённой implementation.

#### Scenario: Одно решение подтверждено
- **WHEN** пользователь однозначно отвечает на текущий вопрос
- **THEN** flow записывает решение до выбора не более одного следующего
  существенного вопроса

#### Scenario: Решение пересмотрено
- **WHEN** пользователь заменяет ранее принятое решение
- **THEN** прежнее решение остаётся видимым как `superseded`

### Requirement: Clarification может завершиться независимо
Flow SHALL допускать завершённую формулировку, запрос human decision или
нерешённую остановку без требования другого flow.

#### Scenario: Формулировка достаточна
- **WHEN** существенных вопросов больше нет
- **THEN** flow записывает текущую формулировку, возвращает local reference и
  завершается без выбора последующей работы

### Requirement: State удалённого skill сохраняется
Установка с `--force` SHALL удалить устаревшие skill и command
`usw-refine-intent`, но MUST NOT удалять существующие artifacts
`.usw/refinements/`.

#### Scenario: Существующие refinement notes присутствуют
- **WHEN** USW обновляется после удаления skill
- **THEN** metadata установленного skill очищаются, а project-local notes
  остаются неизменными
