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

Outcome SHALL различать статус операции и предметный исход flow. При неполном
охвате он SHALL сохранять исходный результат, проверенную часть, остаток и
причины: обозначенный как результат flow исход и проверенную часть в `Done`,
остаток и причины в `Current position`, препятствие в `Blocker` (или `none`),
следующий шаг в `Next action`. Статус
операции SHALL определяться фактической причиной остановки и
условиями завершения задачи, а не автоматически выводиться из `partial`.
`completed` допустим только при выполнении запроса и условий завершения flow,
в том числе если согласованный результат — отчёт с ограниченным охватом.
Если выполнение завершилось невосстановимой ошибкой и продолжение этой
операции не предусмотрено, Outcome SHALL записывать `failed`. Устранимое
внешнее препятствие SHALL оставаться `blocked`.

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

#### Scenario: Контекст незавершённой проверки
- **WHEN** проверка останавливается до завершения
- **THEN** Outcome сохраняет в Done проверенные элементы и существенные
  результаты, в Checks и References — проверки и их источники либо ссылку на
  уже сохранённый подробный отчёт, а в Current position — остаток работы
- **AND** исполнитель сверяет перечитанный Outcome с результатами, которые
  сообщает человеку, и сообщает о несохранённых существенных сведениях
- **AND** при разрешённом продолжении исполнитель учитывает этот контекст,
  проверяет актуальность используемых источников, не утверждает неизменность
  без сопоставимой версии и указывает причину повтора при изменении,
  недоступности источника или недостаточности сохранённых доказательств

#### Scenario: Незавершённый частичный анализ
- **WHEN** flow вернул `partial`, обязательный анализ не закончен и исполнитель
  ставит работу на паузу для продолжения
- **THEN** Outcome записывает `paused`, исходный `partial`, проверенную часть,
  непроверенный остаток и следующий шаг

#### Scenario: Частичный результат из-за внешнего препятствия
- **WHEN** обязательная часть работы недоступна из-за внешнего препятствия,
  которое ответ человека в текущем диалоге не устраняет
- **THEN** Outcome записывает `blocked`, исходный результат, остаток и причину

#### Scenario: Завершённый отчёт с ограниченным охватом
- **WHEN** запрос и условия flow выполнены отчётом об имеющихся данных, а его
  предметный результат указывает ограниченный охват
- **THEN** Outcome записывает `completed` и сохраняет ограничения и исходный
  предметный результат, не утверждая, что непроверенная область проверена

#### Scenario: Nested branches участвуют в root outcome
- **WHEN** nested flows возвращают results до natural stop своего root
- **THEN** только этот root executor записывает Outcome своей operation и
  включает фактический nested progress, необходимый для recovery

### Requirement: Неподдерживаемое содержимое HANDOFF отклоняется
При включённом handoff runtime SHALL проверять `.usw/HANDOFF.md` только как
router. Иной формат, включая прежний generic single-state HANDOFF, SHALL
отклоняться ошибкой валидации без изменения bytes `.usw/HANDOFF.md`, operation
documents и candidates и без автоматического преобразования состояния.

#### Scenario: Файл другого формата
- **WHEN** handoff-команда читает файл, который не является валидным router
- **THEN** команда возвращает ошибку валидации, а bytes HANDOFF, operation
  documents и candidates остаются неизменными

#### Scenario: Старый single-state HANDOFF
- **WHEN** команда получает прежний single-state HANDOFF со status `idle`
  или non-idle status
- **THEN** файл отклоняется без преобразования в router и без создания
  operation document

### Requirement: Recoverable state требует explicit finish
Generic states `in_progress`, `paused`, `blocked` и `decision_required` SHALL
оставаться зарегистрированными до Finish с их exact operation identity или
явно запрошенного `cleanup --all`. Они
MUST NOT блокировать Begin независимой root operation. Recoverable root state
MAY допускать nested executions, переданные его root executor с его exact
current identity, но MUST отклонять nested execution для любой другой identity
или terminal state.

Generic states `failed` и `completed` SHALL оставаться доступными для inspection
до явного Finish или Cleanup. Новый Begin SHALL создавать другую operation и
MUST NOT заменять несвязанное terminal state. Неожиданное прерывание или ошибка Outcome MUST NOT вызывать automatic
retry. Сохранённый status SHALL определяться authoritative operation document,
а не фактом ошибки. Cleanup без `--all` SHALL удалять только зарегистрированные operations
со status `failed` и `completed`, сохраняя recoverable operations. Явный
`cleanup --all` SHALL удалять все зарегистрированные operations независимо от
status; файлы продукта и незарегистрированные документы MUST NOT удаляться.

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
- **WHEN** Cleanup без `--all` запрошен при зарегистрированных terminal и recoverable
  operations
- **THEN** удаляются только terminal routes и их exact files, а recoverable
  operations остаются зарегистрированными

#### Scenario: Прерванный invocation возобновляется
- **WHEN** Resume выбирает operation со status `in_progress` без terminal Outcome
- **THEN** он возвращает recovery context этой operation без автоматического
  повтора root или nested mutations

#### Scenario: Все операции очищаются явно
- **WHEN** пользователь вызывает `cleanup --all` при операциях в любых статусах
- **THEN** router становится пустым, документы и кандидаты всех зарегистрированных
  операций удаляются, а остальные файлы остаются неизменными

#### Scenario: Пустой журнал очищается повторно
- **WHEN** пользователь вызывает `cleanup --all` при пустом router
- **THEN** возвращается пустой список удалённых операций

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
read-check-write под project-local handoff lock на каждой поддерживаемой
платформе и без зависимости от locking primitive, отсутствующего на одной из
них. Begin SHALL записать и проверить operation document до его регистрации и
MUST NOT начинать model execution до подтверждения обеих записей. Outcome SHALL
обновлять только выбранный authoritative operation document, а затем обновлять
человекочитаемый status snapshot в router.

Save MUST использовать operation-scoped candidate и MUST NOT переписывать
terminal operation, изменять operation identity или immutable context либо
указывать на незарегистрированную operation. Finish SHALL отменять регистрацию
только выбранной identity до удаления только её exact operation document и
candidate. Cleanup SHALL сначала отменить регистрацию выбранных identities
(terminal без `--all`, всех зарегистрированных с `--all`), а затем удалить
только их exact operation documents и candidates.

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

#### Scenario: Handoff transition на платформе без POSIX locking
- **WHEN** любой handoff transition выполняется на поддерживаемой платформе,
  где нет `fcntl`
- **THEN** transition сериализуется locking primitive этой платформы, а его
  state files читаются и записываются через общую safe-access boundary

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
сгенерированных state files. Show без identity MAY обновлять это представление из
authoritative operation documents без изменения operation membership или
recovery state. Show с exact operation identity SHALL проверять route и читать
authoritative operation document без обновления router snapshot или recovery
state; недоступный или невалидный router MUST NOT обходиться.

#### Scenario: Зарегистрирована одна operation
- **WHEN** Resume вызывается без identity и существует ровно одна route
- **THEN** он показывает recovery context этой operation

#### Scenario: Зарегистрировано несколько operations
- **WHEN** Resume вызывается без identity и существует несколько routes
- **THEN** он возвращает их identities, flows и statuses без возобновления любой
  operation

#### Scenario: Exact Show после неполного обновления snapshot
- **WHEN** operation document уже содержит новый status, router snapshot
  устарел, а ошибка записи snapshot сохраняется
- **THEN** Show с exact identity возвращает status и content из валидированного
  operation document без попытки обновить router и без изменения state

#### Scenario: Exact Show не может проверить route
- **WHEN** router недоступен, невалиден или не подтверждает exact operation
- **THEN** Show возвращает ошибку, не читает document в обход route validation
  и не исправляет state

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
- **WHEN** запрошенная identity отсутствует, не совпадает, является idle или
  terminal
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

### Requirement: Устаревшая форма operation document отклоняется
Runtime SHALL принимать только operation documents с обязательными `Summary`,
`Started` и `Workspace`. Старые документы без этих полей SHALL отклоняться
ошибкой валидации до изменения router, documents и candidates. Runtime MUST NOT
выводить недостающие поля из input или преобразовывать старый document при записи.

#### Scenario: Старый документ читается
- **WHEN** Show, Resume или parent verification получает зарегистрированный
  operation document без одного из обязательных recovery fields
- **THEN** операция возвращает ошибку валидации без изменения состояния

#### Scenario: Старый документ изменяется
- **WHEN** Begin, Outcome, Save, Finish или Cleanup затрагивает старый
  operation document без обязательных recovery fields
- **THEN** команда возвращает ошибку валидации, сохраняет router, documents
  и candidates и не записывает восстановленные исторические поля

#### Scenario: Старый candidate сохраняется
- **WHEN** Save получает candidate без обязательных recovery fields для
  актуального operation document
- **THEN** candidate отклоняется, а router, document и candidate остаются неизменными

### Requirement: Ручной handoff требует прямого вызова человека
Вне служебного вызова из flow USW SHALL активировать handoff только по прямому
вызову человеком команды, skill или явной просьбе использовать handoff.
Общие просьбы сохранить состояние или продолжить работу MUST NOT активировать
handoff и MUST NOT приводить к чтению или изменению его state.

#### Scenario: Общая просьба сохранить состояние
- **WHEN** вне flow пользователь просит сохранить состояние без обращения к handoff
- **THEN** агент обрабатывает обычный запрос сохранения, уточняя destination
  при необходимости, и не обращается к HANDOFF или operation documents

#### Scenario: Общая просьба продолжить работу
- **WHEN** вне flow пользователь просит продолжить работу, не вызывая handoff
- **THEN** агент не выполняет Show/Resume и не обращается к handoff state

#### Scenario: Пользователь прямо вызывает handoff
- **WHEN** человек вызывает `/usw-handoff`, `/usw-resume`,
  `$usw-manage-handoff` или явно просит использовать handoff
- **THEN** соответствующий режим выполняется по действующему контракту выбора
  operation и конфигурации

### Requirement: Служебный handoff внутри flow следует конфигурации
Прямой ручной вызов MUST NOT требоваться для служебных Begin/Outcome, read-only
parent verification и exact Show после ошибки Outcome, предусмотренных
контрактом запуска flow. Эти вызовы SHALL
следовать effective `handoff`; при `false` handoff state MUST NOT читаться или
изменяться.

#### Scenario: Flow запущен с включённым handoff
- **WHEN** пользователь запустил flow с effective `handoff: true`
- **THEN** runner выполняет предусмотренные контрактом служебные вызовы без
  отдельного ручного обращения к handoff

#### Scenario: Handoff отключён
- **WHEN** прямой ручной вызов или запуск flow имеет effective `handoff: false`
- **THEN** `.usw/HANDOFF.md`, operation documents и candidates не читаются и
  не изменяются

#### Scenario: Служебная проверка после ошибки Outcome
- **WHEN** root flow с effective `handoff: true` получил ошибку Outcome своей
  exact operation
- **THEN** runner выполняет read-only exact Show без отдельного ручного вызова,
  не активируя произвольные handoff-команды

### Requirement: Ошибка Outcome требует проверки сохранённого состояния
При ошибке Outcome root executor с effective `handoff: true` SHALL прочитать
exact operation через read-only Show. Он SHALL сообщить проверенные status и сохранённые сведения отдельно от
ошибки записи, сохраняя предметный результат в ответе. Если чтение не удалось,
он MUST явно сообщить невозможность подтвердить текущий status и сохранность
новых сведений. Он MUST NOT повторять Outcome, root или nested mutations
автоматически.

#### Scenario: Ошибка до обновления operation document
- **WHEN** operation имела `paused`, Outcome с новым результатом завершился
  ошибкой до изменения document и exact Show прочитал прежнее состояние
- **THEN** ответ сообщает проверенный `paused`, ошибку записи и какие новые
  результаты не найдены в сохранённом контексте, сохраняя их в ответе человеку
- **AND** исполнитель не объявляет `in_progress` по факту ошибки и не повторяет
  исполненные действия или Outcome автоматически

#### Scenario: Ошибка после обновления operation document
- **WHEN** Outcome записал `completed` и новый результат в document, затем
  обновление router snapshot завершилось ошибкой, а exact Show прочитал document
- **THEN** ответ сообщает проверенный `completed` и найденные сохранённые
  сведения, отдельно отмечая ошибку обновления router
- **AND** предметный результат не теряется и исполненные действия не повторяются

#### Scenario: Текущее сохранённое состояние проверить нельзя
- **WHEN** после ошибки Outcome exact Show также завершился ошибкой
- **THEN** ответ содержит предметный результат, обе ошибки и явно отделяет
  прежние подтверждённые факты от текущего неподтверждённого status и сохранности
  новых сведений
- **AND** исполнитель не объявляет сведения сохранёнными или утраченными без
  доказательств, не обходит validation и не повторяет изменения автоматически
