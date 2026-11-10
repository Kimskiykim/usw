# Spec Delta

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

## ADDED Requirements

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
