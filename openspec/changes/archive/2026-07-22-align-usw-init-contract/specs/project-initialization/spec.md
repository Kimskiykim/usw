## ADDED Requirements

### Requirement: Initialization создаёт точный provider-specific workspace
`/usw-init` SHALL создавать только отсутствующие USW-owned artifacts для выбранной v1 configuration и MUST сохранять каждый существующий regular file byte-for-byte.

Для standalone provider немедленный inventory SHALL включать:

- `usw.yaml`;
- `<artifacts.root>/changes/`;
- `<artifacts.root>/templates/change/{proposal.md,design.md,spec.md,tasks.md}`;
- `<artifacts.root>/templates/task/{task.md,development-evidence.md,testing-evidence.md}`;
- `<artifacts.root>/templates/review/receipt.md`;
- `<flows.root>/{flow-scenario-analysis.md,flow-scenario-development.md,flow-scenario-testing.md}`;
- `<reviews.root>/`;
- `.usw/.gitignore` и `.usw/HANDOFF.md`.

Для OpenSpec provider initialization SHALL создавать только configured USW flow/review roots, три перечисленных standard scenario files и два local `.usw` files и MUST NOT создавать или изменять provider-owned `openspec/**`.

#### Scenario: Default standalone workspace инициализируется
- **WHEN** пользователь запускает `/usw-init` без существующей configuration
- **THEN** отсутствующий default standalone inventory создаётся, а существующие files сохраняются

#### Scenario: OpenSpec provider выбран явно
- **WHEN** поддерживаемая v1 configuration выбирает provider `openspec`
- **THEN** initialization создаёт только USW-owned flow, review и local artifacts и не изменяет `openspec/**`

#### Scenario: Standalone явно использует custom root под `openspec`
- **WHEN** поддерживаемая v1 configuration выбирает provider `standalone` и явно задаёт artifact, flow или review root под `openspec/**`
- **THEN** initialization уважает user-selected root и применяет к нему обычный create-only standalone contract

### Requirement: Lazy local artifacts не материализуются initialization
`/usw-init` MUST NOT создавать `.usw/flows/` или `.usw/refinements/`. Эти directories SHALL создаваться только capability, которой пользователь явно поручил создать первый local custom flow или intent clarification session.

#### Scenario: Initialization завершена без local flow и refinement
- **WHEN** `/usw-init` успешно завершает новый workspace
- **THEN** `.usw/flows/` и `.usw/refinements/` отсутствуют до первого соответствующего действия

### Requirement: Git tracking policy принадлежит пользователю
Initialization SHALL создавать отсутствующий `.usw/.gitignore` с локальным ignore default, но MUST NOT проверять Git tracked state, отклонять workspace из-за ignore rules либо изменять root `.gitignore` или `.git/info/exclude`.

#### Scenario: `.usw` уже содержит tracked file
- **WHEN** initialization запускается в Git worktree с tracked entry под `.usw/`
- **THEN** tracked state не блокирует initialization, а существующий entry остаётся неизменным

### Requirement: Python и LLM initialization функционально эквивалентны
Python и явно подтверждённый LLM execution path MUST поддерживать одинаковый закрытый набор v1 configurations, provider choices и project-relative roots. Для одинакового initial state оба path SHALL создавать и сохранять одинаковые artifacts и возвращать эквивалентный created/preserved report.

LLM path MAY сообщать более слабую детерминированность, но MUST NOT отклонять supported custom roots или наличие `openspec/` только из-за отсутствия Python.

#### Scenario: Python недоступен для custom v1 configuration
- **WHEN** Python 3.10+ отсутствует, пользователь подтверждает LLM initialization и configuration использует безопасные custom roots
- **THEN** LLM path валидирует configuration и материализует тот же USW-owned inventory, что Python path

#### Scenario: OpenSpec directory существует без Python
- **WHEN** LLM path видит real `openspec/` directory, который configuration не выбрала как standalone writable root
- **THEN** он оставляет directory byte-for-byte неизменным и продолжает provider-appropriate USW initialization

### Requirement: OpenSpec detection является provider-aware hint
Initialization SHALL считать real `openspec/` directory только hint и MUST NOT утверждать, что provider workspace валиден, инспектировать его содержимое или менять provider selection.

Само обнаружение directory MUST NOT разрешать writes под `openspec/**`, но explicit standalone custom root SHALL оставаться авторитетным пользовательским выбором.

#### Scenario: Standalone рядом с OpenSpec directory
- **WHEN** provider равен `standalone` и real `openspec/` directory существует
- **THEN** initialization сообщает directory hint и explicit opt-in path

#### Scenario: OpenSpec provider уже выбран
- **WHEN** provider равен `openspec` и real `openspec/` directory существует
- **THEN** initialization сообщает активный provider без повторного opt-in предложения

### Requirement: Повторный запуск безопасно восстанавливает partial workspace
Initialization SHALL выполнять create-only additive writes. При неожиданной ошибке после части writes она MUST сообщить о возможном partial workspace и безопасном повторном запуске. Повторный запуск MUST сохранять существующие bytes и создавать только отсутствующие artifacts.

Если запись нового individual file завершается ошибкой, initialization MUST удалить только этот файл, созданный текущей попыткой. Уже существовавшие files и другие успешно созданные artifacts MUST оставаться неизменными.

#### Scenario: Поздняя I/O-ошибка прерывает initialization
- **WHEN** initialization завершается ошибкой после создания части inventory
- **THEN** пользователь получает retry guidance, а следующий успешный запуск достраивает workspace без перезаписи созданных files

#### Scenario: Ошибка оставляет partial bytes нового файла
- **WHEN** write или close завершается ошибкой после записи части bytes в файл, отсутствовавший до текущей попытки
- **THEN** только этот incomplete file удаляется, а повторный create-only запуск создаёт его полностью
