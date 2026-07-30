## REMOVED Requirements

### Requirement: Local flows cannot replace standard role scenarios
**Reason**: Text-first USW больше не имеет зарезервированных standard role flows.
**Migration**: Local и shared flow используют одинаковые правила выбора origin.

### Requirement: Resume preserves custom-flow origin
**Reason**: Machine checkpoint resume удалён.
**Migration**: Generic handoff хранит origin и flow identity как human-readable
recovery context.

## ADDED Requirements

### Requirement: Local и shared используют единый text path
После выбора origin USW SHALL создать одинаковый immutable Markdown invocation;
metadata и origin MUST NOT переключать executor mode.

#### Scenario: Одинаковое содержимое в разных origins
- **WHEN** local и shared flows имеют одинаковое имя и Markdown
- **THEN** local-first lookup сохраняется, а identity включает выбранный origin
