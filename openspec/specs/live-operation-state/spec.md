# Спецификация live-operation-state

## Purpose
Определяет optional routed recovery state для concurrent root operations
текстовых flows и read-only проверку parent для nested execution.

## Requirements

### Requirement: Generic handoff маршрутизирует text operations
Когда effective `handoff` равен `true`, `.usw/HANDOFF.md` SHALL быть
валидированным Markdown router от каждой зарегистрированной exact operation
identity к одному сгенерированному relative state path под `.usw/handoffs/`.
Членство в router SHALL определять регистрацию operation, а указанный operation
document SHALL быть authoritative для mutable status и recovery content этой
operation. Router SHALL также отображать человекочитаемую таблицу с task
summary, flow, latest status, update time, exact operation identity и state path
каждой operation, а также явные команды Finish одной operation и Cleanup
terminal operations. Таблица SHALL быть единственным представлением routes;
второй скрытый route list MUST NOT требоваться.

Каждый operation document SHALL содержать root flow, origin, flow identity,
input digest, operation identity, status, completed work, narrative position,
next action, blocker, checks и references. Допустимые operation statuses SHALL
быть `in_progress`, `paused`, `blocked`, `decision_required`, `failed` и
`completed`. Empty router SHALL означать отсутствие зарегистрированной работы.
Permission boundary в root или nested child SHALL использовать
`decision_required`.

#### Scenario: Новая root operation
- **WHEN** root flow безопасно загружен и Begin создаёт уникальную operation
  identity
- **THEN** его operation document со status `in_progress` и router entry
  записываются атомарно и проверяются по exact bytes до model execution

#### Scenario: Естественная pause
- **WHEN** одна root model явно останавливается до завершения
- **THEN** Outcome записывает `paused`, текущую position и одно next action в
  operation document этого root и обновляет его человекочитаемое представление
  в router

#### Scenario: Nested branches участвуют в root outcome
- **WHEN** nested flows возвращают results до natural stop своего root
- **THEN** только этот root executor записывает Outcome своей operation и
  включает фактический nested progress, необходимый для recovery

### Requirement: Recoverable state требует explicit finish
Generic states `in_progress`, `paused`, `blocked` и `decision_required` SHALL
оставаться зарегистрированными до Finish с их exact operation identity. Они
MUST NOT блокировать Begin независимой root operation. Recoverable root state
MAY допускать nested executions, переданные его root executor с его exact
current identity, но MUST отклонять nested execution для любой другой identity
или terminal state.

Generic states `failed` и `completed` SHALL оставаться доступными для inspection
до Finish с их exact identity. Новый Begin SHALL создавать другую operation и
MUST NOT заменять несвязанное terminal state. Неожиданное прерывание после
регистрации SHALL оставлять status `in_progress` и MUST NOT вызывать automatic
retry. Cleanup SHALL явно удалять все зарегистрированные operations со status
`failed` и `completed`, сохраняя каждую recoverable operation.

#### Scenario: Тот же flow получает новый input
- **WHEN** существует recoverable operation и тот же flow начинается с новым input
- **THEN** Begin регистрирует отдельную operation identity, не изменяя первую
  operation

#### Scenario: Nested flow использует свой active root
- **WHEN** nested context называет точную зарегистрированную recoverable root
  operation
- **THEN** read-only parent check проходит без создания или изменения durable
  state

#### Scenario: Nested flow указывает terminal root
- **WHEN** nested context называет root operation со status `failed` или
  `completed`
- **THEN** child execution останавливается без изменения router или operation
  documents

#### Scenario: Новый flow следует после terminal outcome
- **WHEN** одна зарегистрированная operation имеет status `failed` или
  `completed`, а другой root flow начинается
- **THEN** регистрируется новая operation со status `in_progress`, а terminal
  outcome остаётся доступным для inspection

#### Scenario: Terminal operations очищаются вместе
- **WHEN** Cleanup запрошен при зарегистрированных terminal и recoverable
  operations
- **THEN** удаляются только terminal routes и их exact files, а recoverable
  operations остаются зарегистрированными

#### Scenario: Прерванный invocation возобновляется
- **WHEN** Resume выбирает operation со status `in_progress` без terminal Outcome
- **THEN** он возвращает recovery context этой operation без автоматического
  повтора root или nested mutations

### Requirement: Operation identity связывает flow, input и route
Operation identity SHALL выводиться из flow origin, flow identity и exact input
digest вместе с уникальным invocation token, созданным Begin. Её валидированный
hex suffix SHALL определять сгенерированное имя operation file, а router entry,
запрошенная identity и embedded document identity MUST совпадать при каждом
доступе к state.

Begin MUST сохранять exact input в представлении, которое не может случайно
создать handoff headings. Outcome, Save и Finish MUST называть ожидаемую
operation identity и SHALL отклоняться, если её route отсутствует, указывает на
другую identity или больше не разрешает запрошенный transition. Каждое generic
operation read MUST проверять, что decoded exact input соответствует digest.

#### Scenario: Input изменяется
- **WHEN** тот же flow запрашивается с другим input
- **THEN** его proposed operation identity и route отличаются

#### Scenario: Одинаковый invocation повторяется
- **WHEN** тот же flow и input запускаются снова
- **THEN** новый invocation token, operation identity и route отличаются от
  предыдущего запуска

#### Scenario: Приходит stale Outcome
- **WHEN** Outcome называет завершённую через Finish operation либо operation,
  отсутствующую в router
- **THEN** router и все зарегистрированные operations остаются неизменными, а
  stale writer отклоняется

#### Scenario: Сохранённый input изменён без изменения identity
- **WHEN** candidate Save изменяет decoded input, сохраняя прежние digest и
  operation identity
- **THEN** зарегистрированная operation остаётся неизменной, а candidate
  отклоняется

#### Scenario: Identity router и document расходятся
- **WHEN** router entry разрешается в operation document с другой embedded
  identity
- **THEN** доступ завершается ошибкой до mutation и ни один file не изменяется

### Requirement: Handoff transitions сериализованы
Begin, Outcome, Save, Finish и Cleanup SHALL сериализовать полный transition
read-check-write под project-local handoff lock. Begin SHALL записать и
проверить operation document до его регистрации и MUST NOT начинать model
execution до подтверждения обеих записей. Outcome SHALL обновлять только
выбранный authoritative operation document, а затем обновлять
человекочитаемый status snapshot в router.

Save MUST использовать operation-scoped candidate и MUST NOT заменять legacy
state, переписывать terminal operation, изменять operation identity или
immutable context либо указывать на незарегистрированную operation. Finish
SHALL отменять регистрацию только выбранной identity до удаления только её
exact operation document и candidate. Cleanup SHALL сначала отменить регистрацию
всех terminal identities, а затем удалить только их exact operation documents
и candidates.

#### Scenario: Два вызова Begin пересекаются
- **WHEN** два process concurrently создают разные operation identities
- **THEN** обе operations MAY быть зарегистрированы в сериализованных transitions
  без потери любой router entry

#### Scenario: Concurrent operations записывают Outcome
- **WHEN** два зарегистрированных roots concurrently достигают natural stops
- **THEN** каждый Outcome изменяет только свой exact operation document, а обе
  routes остаются зарегистрированными

#### Scenario: Begin останавливается до регистрации
- **WHEN** Begin не может подтвердить свою router entry после создания candidate
  operation document
- **THEN** model execution не начинается, а candidate удаляется при обработанной
  ошибке либо остаётся non-routable orphan после process crash

#### Scenario: Finish выбирает одну из двух operations
- **WHEN** Finish называет одну из двух зарегистрированных operation identities
- **THEN** удаляются только эта route и её exact files, а другая operation
  остаётся неизменной

#### Scenario: Save из очереди приходит после Finish
- **WHEN** candidate прежней operation сохраняется после удаления её route
- **THEN** все зарегистрированные operations остаются неизменными, а candidate
  отклоняется

### Requirement: Legacy handoff доступен только для recovery
Role-based HANDOFF SHALL оставаться доступным для чтения через Show и Resume без
automatic migration. Resume MUST NOT исполнять работу или записывать generic
Outcome поверх legacy content. Legacy state SHALL блокировать Begin, а явный
Finish SHALL заменять его empty router.

#### Scenario: Активное legacy state
- **WHEN** Resume читает role-based handoff
- **THEN** он показывает доступный recovery context и требует Finish до начала
  routed operation

### Requirement: Отключённая capability не касается HANDOFF
Когда effective `handoff` равен `false`, initialization, root и nested execution,
Show, Resume, Save, Finish и Cleanup MUST NOT требовать, читать, создавать или
изменять `.usw/HANDOFF.md`, `.usw/handoffs/` либо operation-scoped candidate и
SHALL объяснять, что capability отключена.

#### Scenario: При отключении существует routed state
- **WHEN** существуют router или operation files, а configuration устанавливает
  `handoff: false`
- **THEN** каждый local handoff artifact остаётся byte-for-byte неизменным

### Requirement: Router поддерживает deterministic discovery
Show, Resume и Finish SHALL принимать exact operation identity. Без identity они
SHALL выбирать единственную зарегистрированную operation, сообщать об отсутствии
работы при empty router либо возвращать краткий валидированный список operations
и требовать выбор, когда routes несколько.

Читаемое представление router SHALL позволять сделать тот же выбор без открытия
сгенерированных state files. Show MAY обновлять это представление из
authoritative operation documents без изменения operation membership или
recovery state.

#### Scenario: Зарегистрирована одна operation
- **WHEN** Resume вызывается без identity и существует ровно одна route
- **THEN** он показывает recovery context этой operation

#### Scenario: Зарегистрировано несколько operations
- **WHEN** Resume вызывается без identity и существует несколько routes
- **THEN** он возвращает их identities, flows и statuses без возобновления любой
  operation

### Requirement: Generic single-state handoff мигрирует безопасно
Когда включённая handoff command встречает текущий generic single-state format,
USW SHALL мигрировать idle в empty router, а non-idle state — сначала записать
его exact bytes в path, выведенный из валидированной embedded operation identity,
и только затем заменить HANDOFF router-ом. Single-state file MUST оставаться
authoritative до успешной замены router.

#### Scenario: Recoverable generic state мигрирует
- **WHEN** valid generic HANDOFF со status `paused` впервые читается routed runtime
- **THEN** его exact operation content остаётся recoverable через
  зарегистрированную route

#### Scenario: Migration завершается ошибкой до замены router
- **WHEN** operation document не удаётся подтвердить во время migration
- **THEN** исходный single-state HANDOFF остаётся authoritative и неизменным

### Requirement: Проверка active parent остаётся read-only
USW SHALL предоставлять read-only handoff operation, которая подтверждает,
имеет ли exact identity зарегистрированный operation document со status
`in_progress`, `paused`, `blocked` или `decision_required`. Check MUST
использовать те же safe rules валидации router и operation, что и другие reads,
и MUST NOT изменять любой file при успехе или ошибке.

#### Scenario: Exact active parent проверен
- **WHEN** запрошенная identity соответствует зарегистрированной recoverable
  operation
- **THEN** verification проходит, а bytes router и operation остаются неизменными

#### Scenario: Stale parent проверен
- **WHEN** запрошенная identity отсутствует, не совпадает, является idle, legacy
  или terminal
- **THEN** verification завершается ошибкой, а каждый local handoff artifact
  остаётся неизменным

### Requirement: Operation document сохраняет bounded recovery context
Каждый новый operation document SHALL содержать непустой однострочный `Summary`,
immutable timezone-aware `Started`, latest `Updated` и section `Workspace`.
Workspace section SHALL записывать Git base revision, наблюдавшуюся при Begin,
либо явное state `unborn`, `not-git` или `unknown`, если revision наблюдать
нельзя; zero or more expected write hints, переданные до execution; и zero or
more changes, фактически указанные в latest Outcome.

Summary и workspace values MUST оставаться informational: они MUST NOT изменять
operation identity, предоставлять write authority или заявлять detection либо
ownership concurrent product writes.

#### Scenario: Начинается новая operation
- **WHEN** Begin регистрирует routed operation
- **THEN** её document содержит bounded summary, одинаковые initial timestamps
  Started и Updated, observed base revision, expected write hints и не содержит
  observed changes

#### Scenario: Operation достигает outcome
- **WHEN** Outcome записывает natural stop и reported changed areas
- **THEN** Started, base revision и expected writes остаются неизменными, а
  Updated и observed changes отражают подтверждённый Outcome

#### Scenario: Git inspection завершается ошибкой
- **WHEN** Git metadata существует, но base revision проверить нельзя и
  repository не определён положительно как unborn
- **THEN** Begin записывает base revision как `unknown`, не заявляя unborn
  repository

### Requirement: Enriched recovery context остаётся backwards-compatible
USW SHALL читать существующие generic operation documents без Summary, Started
и Workspace, не изменяя их bytes во время Show, Resume или parent verification.
Discovery SHALL выводить bounded display summary из exact input и SHALL сообщать
неизвестное start time для такого document.

Mutation Outcome существующего document SHALL записывать enriched shape,
используя явное `unknown` для недоступных historical start и base revision. Save
MUST NOT заменять enriched operation старой shape или выдумывать недоступные
historical facts.

#### Scenario: Существующая operation проверяется
- **WHEN** Show, Resume или parent verification читает старый routed operation
  document
- **THEN** document остаётся byte-for-byte неизменным, а его recovery content —
  пригодным к использованию

#### Scenario: Существующая operation получает Outcome
- **WHEN** Outcome обновляет старую recoverable operation
- **THEN** operation получает enriched shape с derived summary, неизвестными
  historical fields и новыми reported observed changes

#### Scenario: Save пытается выполнить downgrade
- **WHEN** candidate старой shape указывает на enriched operation
- **THEN** Save отклоняет candidate и оставляет зарегистрированную operation
  неизменной

### Requirement: Multi-operation discovery показывает human context
Когда зарегистрировано более одной operation, Show и Resume SHALL перечислять
summary, flow, status, start time, latest update time, exact operation identity
и state path каждой operation. Exact operation identity SHALL оставаться
единственным selector.

#### Scenario: Две operations используют один flow
- **WHEN** discovery находит несколько зарегистрированных operations с
  одинаковым flow name
- **THEN** их summaries и timestamps возвращаются вместе с разными exact
  operation identities без возобновления любой operation
