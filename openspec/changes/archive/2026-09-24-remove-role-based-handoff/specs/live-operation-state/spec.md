## ADDED Requirements

### Requirement: Неподдерживаемое содержимое HANDOFF отклоняется
При включённом handoff runtime SHALL проверять `.usw/HANDOFF.md` как router или
поддерживаемый generic single-state документ. Содержимое, не прошедшее эти
проверки, SHALL отклоняться ошибкой валидации без изменения bytes
`.usw/HANDOFF.md`, operation documents и candidates.

#### Scenario: Файл другого формата
- **WHEN** handoff-команда читает файл, который не является ни валидным router,
  ни валидным generic single-state документом
- **THEN** команда возвращает ошибку валидации, а bytes HANDOFF, operation
  documents и candidates остаются неизменными

## MODIFIED Requirements

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
candidate. Cleanup SHALL сначала отменить регистрацию всех terminal identities,
а затем удалить только их exact operation documents и candidates.

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

## REMOVED Requirements

### Requirement: Legacy handoff доступен только для recovery
**Reason**: Role-based HANDOFF больше не поддерживается routed handoff.
**Migration**: Сохранить нужный контекст вручную и инициализировать новый empty
router через `/usw-init` после переноса старого файла. Автоматического
преобразования нет.
