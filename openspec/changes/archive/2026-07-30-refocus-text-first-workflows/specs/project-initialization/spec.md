## REMOVED Requirements

### Requirement: Initialization создаёт точный workspace
**Reason**: Требование всегда создаёт role-based `HANDOFF.md` и не учитывает
опциональную capability.
**Migration**: Использовать условную инициализацию text-first workspace.

## ADDED Requirements

### Requirement: Initialization учитывает handoff capability
Initialization SHALL создавать generic idle `.usw/HANDOFF.md` только когда
effective `handoff` равен `true`. При `false` существующий файл MUST оставаться
непрочитанным и неизменным.

#### Scenario: Новый workspace без handoff
- **WHEN** проект инициализируется с `handoff: false`
- **THEN** flow roots и остальной workspace создаются без `HANDOFF.md`

#### Scenario: Capability снова включена
- **WHEN** `handoff` меняется с `false` на `true`, а HANDOFF отсутствует
- **THEN** повторный init создаёт generic idle HANDOFF без изменения других файлов
