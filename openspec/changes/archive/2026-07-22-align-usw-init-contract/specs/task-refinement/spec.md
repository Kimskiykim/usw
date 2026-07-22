## REMOVED Requirements

### Requirement: Refinement сохраняет общее состояние
**Reason**: Shared refinement sessions заменены local non-normative `intent-clarification`; две активные модели конфликтуют.

**Migration**: Новые sessions создаются в `.usw/refinements/`. Исторические shared sessions сохраняются byte-for-byte и используются только после отдельного user-directed migration.

### Requirement: Один decision case за пользовательский ход
**Reason**: Поведение принадлежит capability `intent-clarification`, а legacy `task-refinement` удаляется.

**Migration**: Использовать `usw-refine-intent`, который обсуждает один bounded decision case за ход.

### Requirement: Решения требуют подтверждения и сохраняют superseded history
**Reason**: Decision tracking теперь определяется local `intent-clarification` contract.

**Migration**: Новые decisions сохраняются в local clarification session; shared history автоматически не переписывается.

### Requirement: Ready outcome актуален и переиспользуем
**Reason**: Local clarification outcome является ненормативным и не обязан рекомендовать downstream flow.

**Migration**: Явно продвигать принятый local outcome в отдельную planning capability, если пользователь запросил downstream work.

### Requirement: Refinement не реализует target work
**Reason**: Граница уже нормативно задана `intent-clarification`; отдельная legacy capability не нужна.

**Migration**: После clarification запускать отдельную явно разрешённую planning или implementation operation.
