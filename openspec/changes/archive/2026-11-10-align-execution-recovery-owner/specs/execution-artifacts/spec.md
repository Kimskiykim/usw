# Spec Delta

## MODIFIED Requirements

### Requirement: Один владелец для каждого вида состояния исполнения
USW SHALL хранить завершение change-задач только в `tasks.md`, устойчивый
контракт и краткую историю попыток задачи — в `task.md`, факты локальной
проверки Development — в `development-evidence.md`, независимые проверки и
findings Testing — в `testing-evidence.md`, а решения human review и общие
переходы между ответственностями — в неизменяемых review receipts.

Состояние восстановления текстовой операции SHALL следовать `live-operation-state`:
`.usw/HANDOFF.md` служит developer-local router, а текущий контекст операции
хранится в её exact operation document `.usw/handoffs/<operation-hex>.md`.
Task-level `plan.md` и `handoff.md` MUST NOT быть обязательными или
каноническими артефактами workflow.

#### Scenario: Development выполняет проверку
- **WHEN** обязательная local verification действительно выполнена
- **THEN** её contract revision, source identity, command, result и timestamp
  записываются в `development-evidence.md`, а не выводятся из намерения агента

#### Scenario: Работа приостанавливается
- **WHEN** Development прерывает активную задачу до её завершения
- **THEN** текущая position и одно следующее действие записываются в exact
  operation document по `live-operation-state`, HANDOFF остаётся router,
  а shared task artifacts не получают выдуманный результат

### Requirement: Generic handoff не требует artifact roles
Generic handoff — router и operation documents по `live-operation-state` —
MUST оставаться developer-local и MUST NOT требовать typed subject, role,
write authority, shared evidence или review receipts. Он MUST NOT считаться
durable shared task history.

#### Scenario: Flow не использует OpenSpec artifacts
- **WHEN** text flow приостанавливается
- **THEN** operation document сохраняет достаточный narrative recovery context
  по `live-operation-state` без создания shared artifacts

### Requirement: Replanning сохраняет факты без отдельного plan artifact
Replanning MAY заменять неподтверждённые или pending действия в exact operation
document по `live-operation-state`, но MUST сохранять подтверждённые факты, Milestone log,
evidence и receipts. Изменение stable task contract MUST создавать новую
contract revision и инвалидировать всё Development и Testing evidence задачи.
Изменение только порядка локальных операций MUST NOT менять contract revision
или freshness evidence.

#### Scenario: Оставшаяся работа изменилась после частичного выполнения
- **WHEN** после завершения части работы нужен другой порядок дальнейших действий
- **THEN** оставшиеся локальные действия обновляются в exact operation document,
  HANDOFF остаётся router, подтверждённые факты сохраняются, а в task Milestone
  log добавляется запись только при новой попытке или значимом переходе

#### Scenario: Definition of done изменился
- **WHEN** согласованное изменение затрагивает стабильный контракт задачи
- **THEN** `task.md` получает новую contract revision, а относящееся к прежней
  revision evidence сохраняется, но не доказывает новую revision
