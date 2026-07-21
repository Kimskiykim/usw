## ADDED Requirements

### Requirement: Один владелец для каждого вида состояния исполнения
USW SHALL хранить завершение change-задач только в `tasks.md`, устойчивый
контракт и краткую историю попыток задачи — в `task.md`, факты локальной
проверки Development — в `development-evidence.md`, независимые проверки и
findings Testing — в `testing-evidence.md`, а решения human review и общие
переходы между ответственностями — в неизменяемых review receipts.

`.usw/HANDOFF.md` SHALL быть только developer-local текущей контрольной точкой
и ограниченным журналом активной сессии. Task-level `plan.md` и `handoff.md`
MUST NOT быть обязательными или каноническими артефактами workflow.

#### Scenario: Development выполняет проверку
- **WHEN** обязательная local verification действительно выполнена
- **THEN** её contract revision, source identity, command, result и timestamp
  записываются в `development-evidence.md`, а не выводятся из намерения агента

#### Scenario: Работа приостанавливается
- **WHEN** Development прерывает активную задачу до её завершения
- **THEN** текущая операция и одно следующее действие записываются в
  `.usw/HANDOFF.md`, но shared task artifacts не получают выдуманный результат

### Requirement: Granular tasks имеют устойчивые контракты и краткую историю
Каждая исполнимая change-задача MUST иметь уникальный внутри change стабильный
ID и явное поле `Artifact model: legacy|v1`. Task, созданная после завершения
задачи внедрения templates 2.1, MUST использовать `v1`; значение MUST NOT
выводиться из отсутствующих files или Git history. Completion checkboxes MUST
находиться только в change `tasks.md`.

`V1` task MUST иметь `task.md` с sections Result, Scope, Non-scope, References,
Dependencies, Definition of done, Verification, Contract revision и Milestone
log. Grandfathered `legacy` task MAY сохранять прежний contract и MUST NOT
получать backfilled evidence, которого фактически не существовало.

Contract revision или digest SHALL идентифицировать только стабильную часть
контракта и MUST NOT включать изменяемый Milestone log. Milestone log SHALL быть
таблицей `Attempt | Trigger | Contract | Source | Outcome | References` и
фиксировать границы попыток и значимые переходы, а не каждую команду или tool
call.

#### Scenario: Создание исполнимой задачи после 2.1
- **WHEN** planning добавляет новую leaf task после завершения задачи 2.1
- **THEN** запись ссылается на task directory, чей `task.md` содержит все
  обязательные поля v1 contract, явно объявляет `Artifact model: v1` и не
  дублирует completion status

#### Scenario: Существующая задача сохраняет legacy model
- **WHEN** задача существовала до завершения 2.1
- **THEN** её `task.md` явно объявляет `Artifact model: legacy`, а validator не
  требует от неё созданных задним числом v1 evidence files

#### Scenario: Новая попытка repair
- **WHEN** blocking review открывает ранее завершённую coding task
- **THEN** в Milestone log добавляется новая попытка со ссылками на предыдущий
  receipt и новый source, не изменяя identity исходной версии контракта

### Requirement: Локальный handoff описывает только текущую сессию
`.usw/HANDOFF.md` MUST содержать metadata table
`Subject | Role | Attempt | Current operation | Status | Updated`, ограниченный Session
journal `Event | Operation | Status | Fact | Changed areas`, Verification table,
одно Next action, References и trusted source snapshot с freshness.

`Subject` MUST быть typed reference на refinement, change или task. `Role` MUST
называть текущий Analysis, Development или Testing flow, чтобы resume восстановил
его write authority и completion criteria. Analysis checkpoint MAY ссылаться на
refinement или change до появления granular task.

Operation IDs MUST обозначать смысловые единицы работы, а events — изменения их
состояния, включая как минимум started, completed, blocked, interrupted и
superseded. Журнал MUST NOT перечислять каждую shell command или tool call.
Файл SHALL перезаписываться как текущая локальная контрольная точка и MUST NOT
считаться общей или долговечной историей задачи.

#### Scenario: Нормальная пауза
- **WHEN** исполнитель останавливается между операциями
- **THEN** он обновляет snapshot, завершённые факты, Current operation и ровно
  одно Next action перед окончанием сессии

#### Scenario: Неожиданное прерывание
- **WHEN** агент не успел записать завершение текущей операции
- **THEN** следующий запуск сверяет trusted source snapshot и Git diff, считает
  незавершённую операцию неподтверждённой и продолжает только после reconciliation

### Requirement: Development и Testing ведут раздельное evidence
Development MUST быть единственным writer файла `development-evidence.md`, а
Testing — единственным writer файла `testing-evidence.md` конкретной задачи.
Каждая evidence entry MUST иметь стабильный ID, contract revision, source
identity, выполненный check, result и timestamp. Testing entries также MUST
иметь finding либо явное отсутствие finding.

Одна роль MUST NOT изменять evidence другой роли. В v1 изменение contract
revision или task source identity MUST считать всё Development и Testing
evidence этой задачи stale. Currentness MUST вычисляться сравнением contract
revision и source identity каждой неизменяемой entry с текущими identities
задачи; stale не требует и не разрешает переписывать role-owned entry другой
ролью. V1 MUST NOT сохранять отдельную entry current на основании частичного
dependency analysis.

#### Scenario: Testing проверяет новый source
- **WHEN** Testing выполняет независимый check после изменения implementation
- **THEN** оно добавляет новую entry в `testing-evidence.md` и не изменяет
  прежнее Development evidence

#### Scenario: Source изменился после успешной проверки
- **WHEN** новая source identity инвалидирует ранее успешную verification
- **THEN** всё Development и Testing evidence задачи сохраняется как stale, а
  task не может быть завершена повторно до всех обязательных checks для текущего
  source

### Requirement: Source identity описывает полный конечный product tree
V1 source identity MUST быть SHA-256 digest canonical manifest полного конечного
product tree в worktree и MUST NOT включать commit OID. Candidate MUST включать
текущее состояние всех tracked product files после staged и unstaged changes и
все Git-visible untracked product files; deleted files MUST отсутствовать.

Manifest bytes MUST начинаться с ASCII `USW-SOURCE-V1\0`. Каждый path MUST быть
project-relative UTF-8 NFC с separator `/`, без absolute, empty, `.` или `..`
segments. Entries MUST сортироваться по unsigned path bytes; collision после
normalization MUST отклоняться. Entry MUST кодироваться как
`uint32be(path_byte_length) + path_bytes + kind_byte +
uint64be(payload_byte_length) + sha256(payload)_raw_32_bytes`, где kind равен
`f` для regular non-executable file, `x` для executable file и `l` для symlink.
Regular payload MUST быть raw file bytes без line-ending normalization; symlink
payload MUST быть raw link-target bytes без чтения target. Source ID MUST иметь
форму `usw-source-v1:<lowercase-hex-sha256(manifest-bytes)>`.

`.git`, `.usw` и configured artifact, refinement, flow и review roots MUST быть
исключены. Git-ignored untracked files MUST NOT входить в candidate. Один и тот
же manifest MUST использоваться evidence, receipts, resume snapshot и Delivery.

#### Scenario: Product file изменён до commit
- **WHEN** tracked product file изменён либо добавлен Git-visible untracked file
- **THEN** canonical source digest меняется и всё evidence v1 task против
  прежнего digest считается stale

#### Scenario: Workflow record изменён
- **WHEN** изменяется evidence, receipt, `.usw/HANDOFF.md` или другой file под
  configured workflow root
- **THEN** product source digest остаётся прежним и не самоинвалидируется

#### Scenario: Workflow-only commit изменяет HEAD
- **WHEN** commit изменяет только исключённые workflow artifacts
- **THEN** полный product manifest и source ID остаются прежними, несмотря на
  новый commit OID

### Requirement: Завершение coding task ограничено ответственностью Development
Development MUST отмечать v1 change-задачу выполненной только после выполнения её
definition of done, завершения применимых операций и наличия актуального
успешного Development evidence для всех обязательных local checks. Checkbox MUST
NOT означать принятие human reviewer, Testing или Delivery.

Grandfathered legacy task SHALL завершаться по явно сохранённому legacy contract
и фактически выполненной verification, но MUST NOT получать выдуманное v1
evidence либо считаться принятой human reviewer, Testing или Delivery.

#### Scenario: Проверка запланирована, но не выполнена
- **WHEN** implementation выглядит завершённой, но обязательная local
  verification не имеет выполненного результата
- **THEN** coding task остаётся незавершённой, а Development evidence не
  содержит выдуманного успешного факта

#### Scenario: Development завершён до Testing
- **WHEN** coding task удовлетворяет своему контракту и обязательным local checks
- **THEN** Development отмечает её выполненной, но работа всё ещё требует
  применимых human review, Testing и Delivery gates

### Requirement: Blocking finding повторно открывает исходную coding task
Если human review или Testing показывает, что отмеченная coding task не
удовлетворяет исходным scope, result или definition of done, Development MUST
изменить её checkbox с `[x]` на `[ ]`, начать новую attempt, выполнить repair и
verification и только затем отметить задачу снова. Старые evidence entries и
receipts MUST сохраняться. Независимый новый scope MUST стать новой задачей
только после подтверждения пользователя.

#### Scenario: Finding входит в исходный контракт
- **WHEN** reviewer фиксирует blocking finding против исходного `task.md`
- **THEN** та же coding task повторно открывается и получает новую attempt без
  создания искусственной новой задачи

#### Scenario: Finding предлагает независимое улучшение
- **WHEN** предложение не требуется исходным контрактом задачи
- **THEN** текущая task не открывается повторно, а новый scope сначала
  предлагается пользователю

### Requirement: Replanning сохраняет факты без отдельного plan artifact
Replanning MAY заменять неподтверждённые или pending операции текущей сессии в
`.usw/HANDOFF.md`, но MUST сохранять подтверждённые факты, Milestone log,
evidence и receipts. Изменение stable task contract MUST создавать новую
contract revision и инвалидировать всё Development и Testing evidence задачи.
Изменение только порядка локальных операций MUST NOT менять contract revision
или freshness evidence.

#### Scenario: Оставшаяся работа изменилась после частичного выполнения
- **WHEN** после завершения части работы нужен другой порядок дальнейших действий
- **THEN** текущие локальные операции обновляются, подтверждённые факты
  сохраняются, а в task Milestone log добавляется запись только при новой
  попытке или значимом переходе

#### Scenario: Definition of done изменился
- **WHEN** согласованное изменение затрагивает стабильный контракт задачи
- **THEN** `task.md` получает новую contract revision, а относящееся к прежней
  revision evidence сохраняется, но не доказывает новую revision

### Requirement: Review receipt является общей записью перехода
USW MUST создавать новый reviewer-owned receipt для каждой попытки internal или
transition review под настроенным provider-neutral review root, по умолчанию
`usw/reviews/<subject-type>/<subject-path>/<review-id>.md`. Receipt MUST содержать
gate, owner role, subject identity, reviewed scope, previous attempt или receipt,
reviewer, verdict, timestamp, ссылки на findings и sorted reviewed artifact
identities. Каждая artifact identity MUST содержать canonical project-relative
path и SHA-256 raw bytes artifact content. Receipt MUST ссылаться на
канонические artifacts без копирования их содержимого.

Для `Artifact model: v1` task receipt MUST дополнительно содержать contract
revision, product source identity и evidence IDs. Для `Artifact model: legacy`
task receipt MUST содержать digest `task.md` как contract identity и ссылки на
фактически наблюдавшуюся verification; v1 Contract revision и evidence IDs MUST
NOT требоваться или backfill-иться. Для non-task review эти task-specific fields
MUST быть conditional по reviewed scope.

Receipt с `gate: transition` MUST дополнительно содержать sender и receiver.
Receipt с `gate: internal` MUST NOT требовать или моделировать sender/receiver;
owner role остаётся текущей ответственностью. Validator MUST применять эти
conditional fields по gate.

Subject namespace MUST использовать `refinement/<refinement-id>` для refinement,
`change/<change-id>` для change и `task/<change-id>/<task-id>` для task. Validator
MUST отклонять invalid path segments и доказывать отсутствие collisions между
типами subject.

Receipt SHALL быть единственной общей записью принятого или отклонённого
перехода после удаления task-level `handoff.md`. Каждая повторная попытка MUST
создавать новый receipt; прежний receipt MUST NOT изменяться или удаляться.

#### Scenario: Reviewer принимает переход
- **WHEN** receiver принимает кандидата для следующей ответственности
- **THEN** создаётся новый accepted receipt с точным contract, source и evidence
  identity, после чего ответственность переходит receiver

#### Scenario: Internal review фиксирует решение без перехода
- **WHEN** reviewer завершает internal review результата текущей роли
- **THEN** receipt содержит `gate: internal` и owner role без sender/receiver, а
  ответственность не меняется

#### Scenario: Planning artifact изменился после review
- **WHEN** proposal, spec, design, task или evidence content отличается от
  reviewed artifact identity в accepted receipt
- **THEN** receipt остаётся immutable, но не разрешает следующий переход даже
  при неизменном product source ID

#### Scenario: Legacy task проходит human review
- **WHEN** reviewer проверяет legacy task без v1 Contract revision и evidence IDs
- **THEN** receipt фиксирует `Artifact model: legacy`, digest `task.md` и ссылки
  на фактически наблюдавшуюся verification без создания v1 evidence задним числом

#### Scenario: Кандидат изменился после review
- **WHEN** source или reviewed artifact identity изменились после accepted receipt
- **THEN** прежний receipt остаётся неизменным, но не разрешает новый переход, и
  применимый gate выполняется новой попыткой

### Requirement: Локальный checkpoint и shared history не дублируют друг друга
`.usw/HANDOFF.md` SHALL указывать на typed subject, role, attempt, operation и
канонические shared artifacts, но MUST NOT быть единственным источником
долговечной истории.
Durable milestone history SHALL находиться в `task.md`, выполненные проверки —
в role-owned evidence, а human decisions и переходы — в receipts. Git MAY
служить технической историей файлов, но MUST NOT заменять эти workflow records.

#### Scenario: Новая сессия возобновляет задачу
- **WHEN** доступен актуальный `.usw/HANDOFF.md`
- **THEN** исполнитель восстанавливает role и текущую operation по её ID и
  проверяет ссылки на shared artifacts, не копируя их содержимое в local checkpoint

#### Scenario: Локальный checkpoint отсутствует или устарел
- **WHEN** `.usw/HANDOFF.md` отсутствует либо его source snapshot не совпадает
  с текущим source
- **THEN** shared task, evidence и receipt artifacts сохраняют историю, а
  текущая операция восстанавливается заново и явно

### Requirement: Первое включение модели не мигрирует legacy evidence
При первом включении execution-artifact templates USW SHALL явно пометить все
существующие leaf tasks active change как `Artifact model: legacy` и MUST NOT
создавать для них v1 evidence, Contract revision или Milestone log задним
числом. `tasks.md` MUST содержать activation task ID `2.1` и исчерпывающий legacy
allowlist. После завершения 2.1 allowlist MUST быть immutable; task ID вне списка
MUST использовать `Artifact model: v1`, а новая legacy entry MUST отклоняться.

#### Scenario: Ранняя задача уже существует
- **WHEN** 2.1 обнаруживает task, созданную до появления v1 templates
- **THEN** она получает явную legacy classification без backfilled evidence и
  продолжает использовать сохранённый legacy completion contract

#### Scenario: Новая задача создаётся после 2.1
- **WHEN** planning создаёт следующую granular task после завершения 2.1
- **THEN** template маркирует её `Artifact model: v1`, а validator применяет все
  v1 contract, evidence и completion invariants

#### Scenario: Новая задача пытается объявить legacy model
- **WHEN** task ID отсутствует в frozen legacy allowlist, но `task.md` объявляет
  `Artifact model: legacy`
- **THEN** validator отклоняет task и не позволяет обойти v1 evidence invariants
