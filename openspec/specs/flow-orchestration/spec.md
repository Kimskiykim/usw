# flow-orchestration Specification

## Purpose
TBD - created by archiving change establish-standalone-usw-workflow. Update Purpose after archive.
## Requirements
### Requirement: Три role flows образуют один macro lifecycle
USW SHALL предоставлять Analysis, Development и Testing flows в общем macro
lifecycle `Analysis → Development → Testing → Delivery`. Review MUST быть gate
внутри и между flows, а не четвёртым end-to-end role flow. Delivery MUST быть
терминальным переходом, а не отдельной ролью исполнения.

#### Scenario: Один агент переключает ответственность
- **WHEN** один агент завершает flow и входит в другой role flow
- **THEN** USW меняет input contract, allowed writes, owned artifacts и completion
  criteria без требования другой agent identity

### Requirement: Каждый flow использует общий управляющий shell
Каждый role flow SHALL проверить inputs, восстановить context, подтвердить scope,
выполнить разрешённые role actions, провести internal review, предложить handoff
и пройти transition review принимающей стороны либо вернуть findings владельцу.

#### Scenario: Flow готов передать ответственность
- **WHEN** role actions и internal review завершены успешно
- **THEN** flow предлагает handoff принимающей ответственности и не считает
  передачу состоявшейся до её transition review

### Requirement: Analysis формирует ограниченные спецификации
Analysis SHALL владеть intent clarification, done criteria, project context,
approach selection, product proposal, capability specs и complexity assessment.
Analysis MUST NOT писать implementation code, technical design, executable tasks,
локальные Development operations, tests или evidence.

#### Scenario: Спецификация слишком широкая
- **WHEN** до executable planning обнаружены независимо поставляемые и
  проверяемые части
- **THEN** Analysis предлагает parent/child boundaries, dependencies и acceptance
  boundaries и ждёт подтверждения пользователя до создания split

#### Scenario: Capabilities имеют общую delivery boundary
- **WHEN** несколько capabilities должны поставляться и проверяться вместе
- **THEN** Analysis сохраняет их как capability specs одного change

### Requirement: OpenSpec frontier разделён между Analysis и Development
При OpenSpec `spec-driven` provider Analysis SHALL создавать `proposal` и
capability `specs`, а Development SHALL создавать technical `design` и `tasks`.
Role-oriented flows MUST запрашивать artifact instructions по отдельности и
MUST NOT вызывать bundled `openspec-propose` через эту границу.

#### Scenario: Analysis достигает своего OpenSpec frontier
- **WHEN** `proposal` и capability `specs` завершены, status `design` равен
  `ready`, `design.md` отсутствует, а status `tasks` равен `blocked`
- **THEN** Analysis может предложить handoff при `isComplete: false`, не создавая
  `design.md` или `tasks.md`

#### Scenario: Development продолжает OpenSpec graph
- **WHEN** Development принимает Analysis handoff с явным scope
- **THEN** Development запрашивает instructions и создаёт technical `design.md`,
  повторно читает status и затем создаёт `tasks.md`, когда его status становится
  `ready`

### Requirement: Development сохраняет authority спецификации
Development SHALL владеть technical design, executable tasks, implementation,
implementation-adjacent tests, local verification, repair, Development evidence
и coding-task checkboxes. Оно MUST NOT неявно менять product requirements или
объявлять Testing либо Delivery завершёнными.

#### Scenario: Implementation обнаруживает недостающее product decision
- **WHEN** Development не может продолжить без изменения принятого requirement
- **THEN** оно останавливается и возвращает решение в Analysis

#### Scenario: Development завершает coding task
- **WHEN** task definition of done, применимые операции и обязательные local checks выполнены
- **THEN** Development отмечает coding task выполненной и предлагает результат
  для internal review, не заявляя независимое принятие

### Requirement: Testing создаёт независимое evidence
Testing SHALL оценивать точный source identity против нормативного product
contract и владеть созданными им independent tests, findings и evidence. Testing
MUST NOT изменять inspected implementation, Development artifacts или product
requirements.

#### Scenario: Testing обнаруживает implementation defect
- **WHEN** наблюдаемое поведение нарушает acceptance criterion
- **THEN** Testing записывает finding и evidence и возвращает работу Development
  без скрытого исправления implementation

#### Scenario: Независимый check оказался ошибочным
- **WHEN** Testing доказывает ошибку собственного check
- **THEN** оно может исправить check и повторить его, не ослабляя requirement

### Requirement: Human review разделён на internal и transition gates
Каждый role flow MUST пройти human internal review своего результата. Handoff
между flows MUST пройти отдельный human transition review, принадлежащий
принимающей ответственности: Development принимает Analysis, Testing принимает
Development, а delivery owner принимает Testing.

Internal receipt MUST содержать owner role и MUST NOT моделировать
sender/receiver. Transition receipt MUST содержать owner role, sender и receiver.
Оба receipt MUST связываться с точными identities всех reviewed planning
artifacts. Legacy task review MUST передавать digest `task.md` и observed
verification references вместо отсутствующих v1 contract/evidence fields.

#### Scenario: Receiver отклоняет handoff
- **WHEN** transition reviewer находит blocking issue в sender-owned artifact
- **THEN** receiver создаёт review receipt с findings и возвращает работу
  владельцу, не исправляя sender artifact

#### Scenario: Receiver принимает handoff
- **WHEN** supplied contract, artifacts и evidence достаточны для принятия
  следующей ответственности
- **THEN** reviewer создаёт accepted receipt и ответственность переходит receiver

#### Scenario: Internal review завершён
- **WHEN** human reviewer проверяет результат внутри текущей ответственности
- **THEN** receipt фиксирует owner role и verdict без sender/receiver, а
  ответственность остаётся у той же роли

#### Scenario: Legacy task передаётся на review
- **WHEN** reviewed task явно объявляет `Artifact model: legacy`
- **THEN** review использует task artifact digest и observed verification
  references, не создавая Contract revision или evidence IDs задним числом

### Requirement: Возвраты направляются владельцу и повторяют затронутые gates
Finding MUST возвращаться flow, владеющему затронутым каноническим артефактом.
После repair USW SHALL возобновлять lifecycle с самого раннего gate, чей contract,
source identity или evidence стали неактуальны.

#### Scenario: Code изменён после Testing finding
- **WHEN** Development исправляет implementation defect
- **THEN** новая task source identity делает всё Development и Testing evidence
  задачи stale, все обязательные checks и Testing повторяются, а затем
  выполняется новая попытка применимого transition review

#### Scenario: Product contract изменён после finding
- **WHEN** Analysis изменяет нормативную specification
- **THEN** работа проходит через затронутые Development, Testing и review gates

### Requirement: Явный контракт flow scenario
Каждый исполнимый USW flow SHALL быть описан artifact
`flow-scenario-<name>.md` с sections Purpose, Inputs, Ordered actions, Branches,
Write authority, Stop conditions и Outputs.

Исполнимые scenarios MUST разрешаться из configured project `flows.root`.
Package SHALL предоставлять initial templates, а initialization SHALL создавать
только отсутствующие Analysis, Development и Testing scenario files без
перезаписи существующих. Package assets MUST NOT использоваться как скрытый
runtime fallback для отсутствующего project scenario.

#### Scenario: Валидация полного scenario
- **WHEN** scenario содержит все обязательные sections и ссылается на доступные
  actions
- **THEN** USW принимает его как исполнимый orchestration contract

#### Scenario: Отклонение неполного scenario
- **WHEN** scenario не содержит Write authority или Stop conditions
- **THEN** USW отклоняет его до запуска любого action

#### Scenario: Инициализация добавляет отсутствующие standard scenarios
- **WHEN** configured flow root не содержит один или несколько initial scenario
  files
- **THEN** initialization создаёт только отсутствующие files из packaged
  templates и сохраняет существующие scenarios byte-for-byte

#### Scenario: Project scenario отсутствует во время запуска
- **WHEN** orchestrator не находит выбранный scenario в configured flow root
- **THEN** flow останавливается как invalid artifact state и не выполняет
  packaged scenario неявно

### Requirement: Scenario владеет оркестрацией
`usw-run-flow` SHALL следовать ordered actions и branches выбранного scenario.
Atomic skills MUST выполнять только заявленную capability и MUST NOT выбирать
или вызывать последующий skill самостоятельно.

Orchestrator SHALL вызывать capability через action-executor contract, который
возвращает status, фактически затронутые artifact roles, output references и
применимый blocker, decision либо permission boundary. После одного action
управление MUST возвращаться orchestrator.

#### Scenario: Atomic action завершён
- **WHEN** atomic skill завершает одно scenario action
- **THEN** управление возвращается `usw-run-flow`, который оценивает следующую
  branch или stop condition

#### Scenario: Capability ещё не подключена
- **WHEN** выбранный scenario ссылается на action, для которого нет доступного
  executor
- **THEN** orchestrator останавливается до mutation и сообщает отсутствующую
  capability как следующее необходимое действие

#### Scenario: Orchestrator проверяется до реализации capabilities
- **WHEN** sequencing и branching проверяются на stub action executors
- **THEN** stub возвращает тот же structured outcome contract, но не считается
  установленной lifecycle capability

### Requirement: Минимальный набор skills ориентирован на capabilities
Начальный workflow SHALL использовать три role scenarios и один
`usw-run-flow`, переиспользовать существующие brainstorming, refinement,
small-step task decomposition и local checkpoint skills и добавлять только provider-aware artifact
management, bounded task execution и independent verification/evidence.

#### Scenario: Human review требуется сценарию
- **WHEN** scenario достигает internal или transition review gate
- **THEN** он выполняет human gate action и создаёт receipt, не вызывая отдельный
  Review flow или review-orchestrator skill

### Requirement: Scope исполнения выбирается явно
Если request разрешает execution, но не называет единственный допустимый step,
task или change scope, orchestrator MUST показать текущие допустимые варианты и
ждать выбора пользователя.

#### Scenario: Неуточнённое продолжение имеет несколько scopes
- **WHEN** пользователь говорит только «продолжай», а допустимы current step и
  current task
- **THEN** orchestrator показывает оба scope и не выполняет action до выбора

#### Scenario: Пользователь назвал scope
- **WHEN** пользователь явно выбирает допустимый step, task или change
- **THEN** orchestrator работает только внутри выбранного scope и stop conditions

### Requirement: Write authority проверяется до записи
Перед записью shared или local state orchestrator SHALL проверить, что scenario
разрешает action изменять соответствующую artifact role.

#### Scenario: У action нет authority на artifact
- **WHEN** action пытается изменить artifact role вне своей Write authority
- **THEN** flow останавливается без записи и сообщает об authority mismatch

### Requirement: Delivery использует per-run terminal contract
Перед Delivery USW MUST определить delivery scope, точную tested source identity,
current evidence, unresolved non-blocking observations и delivery owner. User
SHALL быть owner по умолчанию, если явно не делегировал ответственность.

#### Scenario: Delivery owner принимает Testing handoff
- **WHEN** owner принимает названный tested candidate
- **THEN** lifecycle достигает Delivery только для указанного scope и identity

#### Scenario: Требуется внешнее действие
- **WHEN** Delivery принят, но commit, push, pull request, deployment или release
  не были явно разрешены
- **THEN** USW не выполняет внешнее действие и сообщает, какое разрешение нужно

### Requirement: Причина остановки flow наблюдаема
Flow SHALL останавливаться на completion condition, blocker, обязательном user
decision или permission, invalid artifact state либо исчерпании выбранного scope
и SHALL сообщать причину и следующее безопасное действие.

#### Scenario: Требуется решение пользователя
- **WHEN** branch требует отсутствующего выбора
- **THEN** flow останавливается до зависимых writes и задаёт только необходимый
  вопрос
