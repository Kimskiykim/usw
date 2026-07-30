## MODIFIED Requirements

### Requirement: Initialization учитывает handoff capability
`/usw-init` SHALL создавать только отсутствующие USW-owned artifacts для
выбранной v1 configuration и MUST сохранять каждый существующий regular file
byte-for-byte.

Немедленный inventory SHALL включать:

- `usw.yaml`;
- `<flows.root>/examples/{chat-review.md,dev-test.md}`;
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
`.usw/handoffs/`, `<artifacts.root>/changes/`,
`<artifacts.root>/templates/` или `<reviews.root>/`. Эти directories SHALL
создаваться только capability, которой пользователь явно поручил первое
соответствующее действие.

#### Scenario: Initialization завершена без lazy artifacts
- **WHEN** `/usw-init` успешно завершает новый workspace
- **THEN** local flow, refinement, routed operation, change, template и review directories отсутствуют до первого соответствующего действия
