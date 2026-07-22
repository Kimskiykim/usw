## ADDED Requirements

### Requirement: Default run-flow принимает любой Markdown
`usw-run-flow` SHALL принимать текст задачи и безопасное имя flow, находить
обычный `.md` и запускать его без обязательной версии, DSL, action names,
bindings или normalized plan. Наличие metadata версии MUST NOT автоматически
включать строгий runtime.

#### Scenario: Запуск plain Markdown
- **WHEN** найденный flow является обычным Markdown без поля версии
- **THEN** фасад передаёт исходную задачу и документ default Markdown executor

#### Scenario: Structured Markdown без opt-in
- **WHEN** найденный flow содержит metadata версии `1` или `version-2`, но experimental selector не передан
- **THEN** фасад запускает его как обычный Markdown и не требует strict validation

### Requirement: Фасад разрешает именованный flow в существующих roots
Без явного origin selector фасад MUST искать безопасное имя сначала в
`<project>/.usw/flows`, затем в настроенном shared root. Явный selector SHALL
ограничивать поиск выбранным root. Фасад MUST отклонять path traversal,
symlinks и non-regular files до исполнения и SHALL сообщать resolved origin.

#### Scenario: Local flow переопределяет shared
- **WHEN** flow с одинаковым именем существует в local и shared roots без явного selector
- **THEN** фасад выбирает local flow и сообщает его origin

#### Scenario: Flow отсутствует
- **WHEN** безопасное имя не найдено ни в одном разрешённом root
- **THEN** фасад останавливается до executor и сообщает missing flow

### Requirement: Default executor следует описанному процессу
Default Markdown executor SHALL прочитать flow целиком, использовать задачу как
рабочий вход и выполнить описанные действия через доступные capabilities.
Неоднозначность, которая требует существенного выбора пользователя, MUST
вернуть `decision_required`. Внешние или разрушительные действия MUST сохранять
существующие permission boundaries.

#### Scenario: Однозначный prose flow
- **WHEN** Markdown однозначно описывает последовательность доступных действий
- **THEN** executor выполняет её без преобразования документа в пользовательский DSL

#### Scenario: Неоднозначный prose flow
- **WHEN** из Markdown нельзя безопасно выбрать одно из существенно разных действий
- **THEN** executor не угадывает и возвращает `decision_required`

### Requirement: Default execution имеет одну operation boundary
Обычный запуск SHALL фиксировать flow origin, identity, задачу, Begin и Outcome
через существующий HANDOFF mechanism. Он MUST NOT требовать per-action cursor,
loop counters, action bindings или отдельный runtime state-файл.

#### Scenario: Успешный default-запуск
- **WHEN** Markdown executor завершил описанный flow
- **THEN** HANDOFF содержит завершённый outcome одной operation boundary

#### Scenario: Прерывание внутри default executor
- **WHEN** Begin записан, но terminal outcome отсутствует
- **THEN** повторный вызов не запускает mutations автоматически и сообщает незавершённую operation

### Requirement: Structured runtime является явным experiment
Строгий parser/orchestrator SHALL включаться только через явный selector
`--experimental-structured`. В этом режиме он MUST принимать только
поддерживаемые v1/v2 контракты, валидировать их до первого executor и исполнять
не более одной top-level boundary за invocation.

#### Scenario: Явный запуск version-2 experiment
- **WHEN** пользователь передал experimental selector для валидного `version-2` flow
- **THEN** runner строит `CustomFlow`, выполняет preflight и запускает одну boundary

#### Scenario: Невалидный strict contract
- **WHEN** experimental selector передан для Markdown, который не соответствует v1 или v2
- **THEN** strict parser отклоняет документ до первого executor

### Requirement: Experimental runtime сохраняет typed control flow
В experimental structured mode runner SHALL поддерживать exact `CALL SKILL`,
`CALL SCRIPT`, `CALL FLOW`, `CALL SUBAGENT` и `CALL HUMAN`, nested subagent
payload, complete gates, bounded loops и preflighted parallel blocks. Он MUST
сохранять cursor/control state через существующий checkpoint/HANDOFF boundary.

#### Scenario: Experimental control transition
- **WHEN** completed gate возвращает объявленный outcome
- **THEN** experimental runner сохраняет outcome и переводит cursor к точному target

#### Scenario: Experimental parallel boundary
- **WHEN** все заранее разрешённые parallel children завершаются успешно
- **THEN** runner агрегирует outcomes и открывает следующую top-level boundary

### Requirement: Experimental binding необязателен
Experimental runtime MAY принимать action-specific inputs и передавать
именованные completed results. Если binding передан, неизвестные action names
MUST быть отклонены до первого executor, а child outcomes `PARALLEL` SHALL
сохраняться по постоянным именам. Отсутствие binding MUST NOT препятствовать
запуску flow.

#### Scenario: Запуск без action map
- **WHEN** валидный experimental flow запущен только с общей задачей
- **THEN** runner начинает flow без требования action-specific input map

#### Scenario: Именованные parallel results
- **WHEN** experimental binding включён и `review-a` и `review-b` завершились внутри parallel block
- **THEN** зависимый consumer получает оба результата под постоянными именами

### Requirement: Структурированную форму создаёт create-flow
`usw-create-flow` SHALL создавать или обновлять v1/v2 executable contract только
после явного structured/experimental выбора. `usw-run-flow` MUST NOT изменять
исходный Markdown или требовать такого преобразования для default execution.

#### Scenario: Создание structured flow
- **WHEN** пользователь явно выбирает structured mode в `usw-create-flow`
- **THEN** create-flow формирует валидируемые actions, executors и transitions

#### Scenario: Default run не переписывает flow
- **WHEN** пользователь запускает plain Markdown обычным `usw-run-flow`
- **THEN** исходный flow остаётся неизменным
