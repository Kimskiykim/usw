## ADDED Requirements

### Requirement: Handoff включается top-level boolean
`usw.yaml` SHALL принимать необязательное top-level поле `handoff` только как
boolean. Отсутствующее поле SHALL означать `true`; schema version остаётся `1`.

#### Scenario: Backwards-compatible configuration
- **WHEN** существующий `usw.yaml` не содержит `handoff`
- **THEN** USW включает handoff

#### Scenario: Handoff явно отключён
- **WHEN** `handoff: false`
- **THEN** run, init, handoff и resume не требуют, не читают и не изменяют `HANDOFF.md`

#### Scenario: Неверный тип
- **WHEN** `handoff` является строкой, числом или mapping
- **THEN** configuration validation завершается наблюдаемой ошибкой
