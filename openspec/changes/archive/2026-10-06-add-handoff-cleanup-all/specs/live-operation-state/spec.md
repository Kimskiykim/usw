## MODIFIED Requirements

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
MUST NOT заменять несвязанное terminal state. Неожиданное прерывание после
регистрации SHALL оставлять status `in_progress` и MUST NOT вызывать automatic
retry. Cleanup без `--all` SHALL удалять только зарегистрированные operations
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
