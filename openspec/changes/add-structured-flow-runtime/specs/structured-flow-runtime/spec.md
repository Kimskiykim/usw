## ADDED Requirements

### Requirement: Детерминированный executable-контракт version-2
`usw-run-flow` SHALL распознавать точную версию `version-2` и валидировать
канонический executable-поднабор Markdown до вызова любого executor. Каждый
верхнеуровневый пункт MUST иметь последовательный номер и глобально уникальное
постоянное kebab-case имя; неизвестная или неоднозначная форма MUST быть
отклонена с наблюдаемой причиной и строкой.

#### Scenario: Валидный structured flow
- **WHEN** документ `version-2` использует канонические typed calls и управляющие маркеры
- **THEN** runner создаёт валидированное представление с постоянными именами и переходами

#### Scenario: Неоднозначный structured flow
- **WHEN** смысл executor, branch, loop либо nested ownership нельзя получить из канонической формы
- **THEN** runner останавливается до разрешения или вызова executor и сообщает точную ошибку

### Requirement: Все typed calls разрешаются точно
Runner SHALL поддерживать `CALL SKILL`, `CALL SCRIPT`, `CALL FLOW`,
`CALL SUBAGENT` и `CALL HUMAN`. `SKILL`, `FLOW`, `SUBAGENT` и `HUMAN` MUST
разрешаться по точным type и target; script MUST сохранять безопасный
project-relative argv contract без shell semantics. `MODEL` MUST быть
отклонён.

#### Scenario: Typed executor доступен
- **WHEN** action ссылается на доступный executor с теми же type и target
- **THEN** runner передаёт ему scope, literal arguments и применимый nested payload

#### Scenario: Тип либо target недоступен
- **WHEN** exact typed executor отсутствует или недоступен
- **THEN** runner останавливается до mutation и не заменяет его похожим executor

### Requirement: Nested actions принадлежат CALL SUBAGENT
Каждый `CALL SUBAGENT` MUST содержать непустой вложенный нумерованный payload с
глобально уникальными именами. Runner SHALL передавать этот payload ближайшему
enclosing subagent как часть одного typed invocation и MUST NOT исполнять его
как действия родительского flow.

#### Scenario: Subagent получает payload
- **WHEN** parent action вызывает subagent с двумя nested actions
- **THEN** subagent executor получает оба действия в документированном порядке, а parent cursor имеет одну boundary

#### Scenario: Payload отсутствует
- **WHEN** `CALL SUBAGENT` не содержит вложенных действий
- **THEN** validation отклоняет flow до запуска

### Requirement: Gate выбирает только объявленный переход
Action с `GATE` MUST объявлять конечные outcomes, полный `IF`/`ELIF` target для
каждого outcome и `ELSE`. После completed human outcome runner SHALL перейти к
точному target. Outcome вне набора SHALL вернуть `decision_required` и MUST NOT
продвигать cursor.

#### Scenario: Объявленный outcome
- **WHEN** gate executor возвращает один из объявленных outcomes
- **THEN** следующим доступным action становится соответствующий target

#### Scenario: Неизвестный outcome
- **WHEN** gate executor возвращает outcome вне объявленного набора
- **THEN** runner применяет `ELSE`, запрашивает объявленный вариант и не запускает зависимый action

### Requirement: Loop имеет положительный предел и наблюдаемое исчерпание
`LOOP` MUST ссылаться на существующий gate, expected outcome, положительный
предел попыток, ровно один typed call на попытку, возврат к gate и явный текст
исхода при исчерпании. Runner SHALL сохранять число completed attempts и MUST
остановиться как `loop_exhausted`, если gate снова направляет в loop после
достижения предела.

#### Scenario: Loop завершается раньше предела
- **WHEN** повторная проверка возвращает expected outcome до исчерпания попыток
- **THEN** runner следует gate target и больше не вызывает loop executor

#### Scenario: Loop исчерпан
- **WHEN** выполнено максимальное число попыток, а gate снова выбирает loop
- **THEN** runner останавливается до нового вызова и сообщает объявленный exhaustion outcome

### Requirement: Parallel block выполняется как одна boundary
`PARALLEL` MUST содержать не менее двух именованных child calls. Runner MUST
разрешить всех child executors до первого вызова, затем SHALL запустить их
concurrently и дождаться всех outcomes. Parent cursor SHALL продвинуться только
когда все children завершились `completed`; writes и references SHALL быть
агрегированы в порядке документа.

#### Scenario: Все parallel children успешны
- **WHEN** все заранее разрешённые children возвращают completed
- **THEN** block возвращает completed aggregate и открывает следующий top-level action

#### Scenario: Один parallel child неуспешен
- **WHEN** любой child возвращает failed, blocked, decision или permission boundary
- **THEN** block останавливает parent flow и не запускает следующий top-level action

### Requirement: Version-2 resume сохраняет управляющее состояние
Runner SHALL связывать resume с exact flow origin и identity, текущим action и
loop counters. Он MUST использовать существующую operation-state boundary без
нового runtime state-файла и SHALL продолжать принимать legacy checkpoint
schema версии `1` для flow версии `1`.

#### Scenario: Fresh structured resume
- **WHEN** identity и source context не изменились после остановки structured flow
- **THEN** runner восстанавливает текущий action и loop counters без повторения completed boundary

#### Scenario: Structured flow изменился
- **WHEN** Markdown identity отличается от сохранённой
- **THEN** runner отклоняет автоматическое resume как stale flow

### Requirement: Версия 1 сохраняет прежнее поведение
Добавление runtime `version-2` MUST сохранять parsing, executor resolution,
write-contract checks, sequencing, CLI validation и resume flow версии `1`.

#### Scenario: Запуск legacy либо concise version-1 flow
- **WHEN** runner получает ранее поддерживаемый документ версии `1`
- **THEN** он выполняет его с прежней линейной семантикой без миграции
