# Спецификация nested-flow-execution

## Purpose
Определяет исполнение вложенного именованного flow под управлением root executor
с immutable child invocations, общей root identity и без durable runtime,
принадлежащего child.

## Requirements

### Requirement: Root executor создаёт nested execution context
После подготовки root invocation USW SHALL позволять root executor передать
именованный flow как nested work вместе с root execution identity и branch
label. При включённом handoff root identity MUST быть точной зарегистрированной
operation identity, возвращённой Begin. При отключённом handoff она MUST быть
уникальной ephemeral identity, которая не сохраняется и не проверяется по local
handoff artifacts.

Nested context MUST исходить от root executor, MUST NOT выводиться из child flow
Markdown или обычного user input и MUST NOT предоставляться как общий selector
для обхода handoff.

#### Scenario: Root передаёт child flow
- **WHEN** активный root executor назначает именованный child flow субагенту
- **THEN** он передаёт nested context с точной root execution identity и branch
  label

#### Scenario: Handoff отключён
- **WHEN** root invocation работает с effective `handoff: false`
- **THEN** его nested context использует уникальную ephemeral root identity без
  чтения или изменения local handoff artifacts

#### Scenario: Пользователь запрашивает standalone nested mode
- **WHEN** активный root executor не предоставил nested context
- **THEN** USW считает запрос независимым root invocation и применяет обычную
  boundary Begin

### Requirement: Nested flow разрешается как immutable invocation
USW SHALL применять обычный safe flow resolver к каждому nested invocation и
SHALL передавать child model точные разрешённые Markdown, origin, identity и
исходный child input без повторного чтения path. При включённом handoff он MUST
непосредственно перед model execution подтвердить, что router всё ещё содержит
точную parent operation, а её operation document остаётся recoverable. При
отключённом handoff он MUST NOT проверять handoff artifacts.

#### Scenario: Nested flow разрешается безопасно
- **WHEN** child flow выбран внутри активной root operation
- **THEN** USW разрешает его по тем же правилам origin, containment, symlink и
  exact bytes, что и root flow

#### Scenario: Parent route устарел
- **WHEN** parent route отсутствует либо его operation identity или status больше
  не соответствует nested context
- **THEN** nested model execution останавливается без изменения handoff artifact

#### Scenario: Recoverable root явно продолжается
- **WHEN** root executor явно продолжает свою точную текущую operation со status
  `paused`, `blocked` или `decision_required` и передаёт child
- **THEN** read-only parent verification принимает неизменённую routed identity

#### Scenario: При отключённом handoff существует routed state
- **WHEN** nested execution запускается с effective `handoff: false`
- **THEN** execution продолжается без проверки или изменения существующих router
  и operation files

### Requirement: Nested execution не владеет durable state
Nested invocation MUST NOT вызывать Begin, Outcome, Save или Finish и MUST NOT
создавать или изменять router либо operation document. Поэтому несколько nested
invocations, связанных с одной root operation, MAY исполняться concurrently без
конкуренции за владение durable state.

#### Scenario: Независимые nested branches исполняются concurrently
- **WHEN** root flow передаёт два независимых именованных flow с одинаковым root
  execution context
- **THEN** оба MAY исполняться concurrently, пока зарегистрированной остаётся
  только их root operation

#### Scenario: Разные roots передают nested branches
- **WHEN** два concurrent registered roots передают по независимому nested flow
- **THEN** каждый child проверяет собственную parent identity, и ни один child не
  изменяет durable state обоих roots

#### Scenario: Nested branch достигает natural stop
- **WHEN** nested flow завершается, падает, приостанавливается, блокируется или
  требует решения
- **THEN** он возвращает root executor свой status и фактический результат без
  записи Outcome

### Requirement: Root executor агрегирует nested results
Root executor SHALL собирать identity, status и фактический результат каждого
запущенного nested invocation и SHALL оставаться единственным writer Outcome
своей зарегистрированной operation. При интерпретации child statuses он SHALL
следовать root Markdown; если необходимое aggregate action существенно
неоднозначно, он MUST использовать `decision_required`. Child permission
boundary MUST оставаться `decision_required` и MUST NOT получать authority из
текста root или child flow.

#### Scenario: Все parallel branches завершены
- **WHEN** каждая запущенная nested branch возвращает `completed`
- **THEN** root executor использует их results в оставшейся части root flow и
  записывает один Outcome в точный operation document

#### Scenario: Child требует permission
- **WHEN** nested child достигает permission boundary внешнего действия
- **THEN** он возвращает `decision_required`, а root записывает нерешённое
  решение в собственный Outcome

#### Scenario: Для child status нет объявленного handling
- **WHEN** child возвращает status, отличный от completed, а root Markdown не
  определяет aggregate action
- **THEN** root записывает `decision_required`, а не угадывает и не повторяет
  execution

### Requirement: Nested branches не добавляют durable branch runtime
USW MUST NOT создавать per-child handoff files, child router entries,
persistent branch registry, machine cursor или automatic child retry.
`PARALLEL` остаётся readable guidance, а concurrent execution MUST быть
ограничено работой, которую root flow определяет как независимую.

#### Scenario: Child execution прервано
- **WHEN** nested child завершается без надёжного результата
- **THEN** root не повторяет child автоматически и отражает нерешённую работу в
  своей operation

#### Scenario: Parallel branches имеют зависимые действия
- **WHEN** child work упорядочена, зависима или имеет пересекающиеся writes
- **THEN** USW не выводит safe parallel execution из одного nested context
