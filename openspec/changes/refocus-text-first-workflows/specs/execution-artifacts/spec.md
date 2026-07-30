## REMOVED Requirements

### Requirement: Локальный handoff описывает только текущую сессию
**Reason**: Формат требует typed subject, role, attempt и operation journal.
**Migration**: Использовать generic text-flow summary.

### Requirement: Локальный checkpoint и shared history не дублируют друг друга
**Reason**: Требование связывает handoff с typed role artifacts и evidence.
**Migration**: Generic handoff хранит только текущее local recovery state.

## ADDED Requirements

### Requirement: Generic handoff не требует artifact roles
`.usw/HANDOFF.md` MUST оставаться developer-local текущим состоянием и MUST NOT
требовать role, write authority, shared evidence или review receipts.

#### Scenario: Flow не использует OpenSpec artifacts
- **WHEN** text flow приостанавливается
- **THEN** handoff сохраняет достаточный recovery context без создания shared artifacts
