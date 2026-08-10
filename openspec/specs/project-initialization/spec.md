# project-initialization Specification

## Purpose
Define the create-only contract for initializing USW project artifacts while
preserving user-owned files and repository policy.

## Requirements

### Requirement: Initialization учитывает handoff capability
`/usw-init` SHALL создавать только отсутствующие USW-owned artifacts для
выбранной v1 configuration и MUST сохранять каждый существующий regular file
byte-for-byte.

Немедленный inventory SHALL включать:

- `usw.yaml`;
- `<flows.root>/examples/{chat-review.md,dev-test.md,plan-small-steps.md,refine-intent.md}`;
- `.usw/.gitignore`;
- empty routed `.usw/HANDOFF.md` только при effective `handoff: true`.

При `handoff: false` initialization MUST NOT читать, создавать или изменять
`.usw/HANDOFF.md`, `.usw/handoffs/` или operation-scoped candidates.

Initialization MUST NOT создавать, удалять, перемещать или перезаписывать legacy
`flow-scenario-analysis.md`, `flow-scenario-development.md` или
`flow-scenario-testing.md`.

#### Scenario: Default workspace инициализируется
- **WHEN** пользователь запускает `/usw-init` без существующей configuration
- **THEN** отсутствующий default standalone inventory с empty HANDOFF router создаётся, а существующие files сохраняются

#### Scenario: Новый workspace без handoff
- **WHEN** project configuration содержит `handoff: false`
- **THEN** flow roots и остальной workspace создаются без router и operation directory

#### Scenario: Capability снова включена
- **WHEN** `handoff` меняется с `false` на `true`, а HANDOFF отсутствует
- **THEN** повторный init создаёт empty HANDOFF router без изменения других files

#### Scenario: Legacy role scenario уже существует
- **WHEN** configured flow root содержит один или несколько legacy `flow-scenario-*` files
- **THEN** initialization сохраняет их byte-for-byte и независимо создаёт только отсутствующие example files

### Requirement: Lazy artifacts не материализуются initialization
`/usw-init` MUST NOT создавать `.usw/flows/`, `.usw/refinements/`,
`.usw/handoffs/`, `<artifacts.root>/changes/`, `<artifacts.root>/templates/` или
`<reviews.root>/`. Эти directories SHALL создаваться только capability, которой
пользователь явно поручил первое соответствующее действие.

#### Scenario: Initialization завершена без lazy artifacts
- **WHEN** `/usw-init` успешно завершает новый workspace
- **THEN** local flow, refinement, routed operation, change, template и review directories отсутствуют до первого соответствующего действия

### Requirement: Git tracking policy принадлежит пользователю
Initialization SHALL создавать отсутствующий `.usw/.gitignore` с локальным ignore default, но MUST NOT проверять Git tracked state, отклонять workspace из-за ignore rules либо изменять root `.gitignore` или `.git/info/exclude`.

#### Scenario: `.usw` уже содержит tracked file
- **WHEN** initialization запускается в Git worktree с tracked entry под `.usw/`
- **THEN** tracked state не блокирует initialization, а существующий entry остаётся неизменным

### Requirement: Python и LLM initialization функционально эквивалентны
Python и явно подтверждённый LLM execution path MUST поддерживать одинаковый
закрытый набор v1 configurations и project-relative roots. Для одинакового
initial state оба path SHALL создавать и сохранять одинаковые artifacts и
возвращать эквивалентный created/preserved report.

#### Scenario: Python недоступен для custom v1 configuration
- **WHEN** Python 3.10+ отсутствует, пользователь подтверждает LLM initialization и configuration использует безопасные custom roots
- **THEN** LLM path валидирует configuration и материализует тот же USW-owned inventory, что Python path

### Requirement: Повторный запуск безопасно восстанавливает partial workspace
Initialization SHALL выполнять create-only additive writes. При неожиданной ошибке после части writes она MUST сообщить о возможном partial workspace и безопасном повторном запуске. Повторный запуск MUST сохранять существующие bytes и создавать только отсутствующие artifacts.

Если запись нового individual file завершается ошибкой, initialization MUST удалить только этот файл, созданный текущей попыткой. Уже существовавшие files и другие успешно созданные artifacts MUST оставаться неизменными.

#### Scenario: Поздняя I/O-ошибка прерывает initialization
- **WHEN** initialization завершается ошибкой после создания части inventory
- **THEN** пользователь получает retry guidance, а следующий успешный запуск достраивает workspace без перезаписи созданных files

#### Scenario: Ошибка оставляет partial bytes нового файла
- **WHEN** write или close завершается ошибкой после записи части bytes в файл, отсутствовавший до текущей попытки
- **THEN** только этот incomplete file удаляется, а повторный create-only запуск создаёт его полностью
