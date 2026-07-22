## MODIFIED Requirements

### Requirement: Initialization создаёт точный provider-specific workspace
`/usw-init` SHALL создавать только отсутствующие USW-owned artifacts для выбранной v1 configuration и MUST сохранять каждый существующий regular file byte-for-byte.

Для standalone provider немедленный inventory SHALL включать:

- `usw.yaml`;
- `<artifacts.root>/changes/`;
- `<artifacts.root>/templates/change/{proposal.md,design.md,spec.md,tasks.md}`;
- `<artifacts.root>/templates/task/{task.md,development-evidence.md,testing-evidence.md}`;
- `<artifacts.root>/templates/review/receipt.md`;
- `<flows.root>/examples/{analysis.md,development.md,testing.md,chat-review.md,dev-test.md}`;
- `<reviews.root>/`;
- `.usw/.gitignore` и `.usw/HANDOFF.md`.

Для OpenSpec provider initialization SHALL создавать только configured USW flow/review roots, пять перечисленных flow examples и два local `.usw` files и MUST NOT создавать или изменять provider-owned `openspec/**`.

Initialization MUST NOT создавать, удалять, перемещать или перезаписывать legacy `flow-scenario-analysis.md`, `flow-scenario-development.md` или `flow-scenario-testing.md`.

#### Scenario: Default standalone workspace инициализируется
- **WHEN** пользователь запускает `/usw-init` без существующей configuration
- **THEN** отсутствующий default standalone inventory создаётся, а существующие files сохраняются

#### Scenario: OpenSpec provider выбран явно
- **WHEN** поддерживаемая v1 configuration выбирает provider `openspec`
- **THEN** initialization создаёт только USW-owned flow, review и local artifacts и не изменяет `openspec/**`

#### Scenario: Standalone явно использует custom root под `openspec`
- **WHEN** поддерживаемая v1 configuration выбирает provider `standalone` и явно задаёт artifact, flow или review root под `openspec/**`
- **THEN** initialization уважает user-selected root и применяет к нему обычный create-only standalone contract

#### Scenario: Legacy role scenario уже существует
- **WHEN** configured flow root содержит один или несколько legacy `flow-scenario-*` files
- **THEN** initialization сохраняет их byte-for-byte и независимо создаёт только отсутствующие example files
