## Context

`/usw-init` имеет два execution path: детерминированный Python initializer и agent-driven fallback без подходящего Python. Сейчас fallback искусственно ограничен default standalone layout, а Python path дополнительно навязывает Git privacy policy. Одновременно main specs всё ещё описывают shared `refinement.root`, хотя актуальный intent clarification хранит только локальные ненормативные notes.

Изменение пересекает initialization code, skill instructions, documentation, packaged assets, specs и tests. Оно не должно менять provider-owned OpenSpec artifacts, перезаписывать project-owned files или расширять threat model до concurrent filesystem attacker.

## Goals / Non-Goals

**Goals:**

- задать один функциональный v1 initialization contract для Python и LLM execution;
- сделать точный provider-specific artifact inventory наблюдаемым и тестируемым;
- оставить Git tracking policy пользователю, сохранив `.usw/.gitignore` как удобство;
- удалить legacy shared refinement configuration и capability;
- сохранить OpenSpec no-write boundary и provider-operation validation;
- восстановить зелёный full test suite после добавления GATE в `chat-review`.

**Non-Goals:**

- transactional rollback или staging всего workspace;
- защита от процесса, одновременно заменяющего проверенные parents на symlinks;
- автоматическая миграция исторических shared refinements;
- валидация внутренней структуры OpenSpec workspace во время init;
- изменение provider adapters или OpenSpec artifact graph.

## Decisions

### 1. Git ignore является удобством, а не enforced policy

Initializer продолжает создавать отсутствующий `.usw/.gitignore` с `*`, но не вызывает Git для проверки tracked state или эффективности ignore rules. Root `.gitignore` и `.git/info/exclude` не изменяются.

Альтернатива — проверять весь tracked `.usw/**` namespace — отклонена: решение о tracking принадлежит пользователю и не должно блокировать workspace initialization.

### 2. Shared refinement model удаляется, historical data сохраняется

`refinement.root` удаляется из активной v1 configuration, а main capability `task-refinement` удаляется. Единственная новая clarification model — `.usw/refinements/<id>/` из `intent-clarification`. Существующие shared sessions не читаются, не перемещаются и не удаляются автоматически.

Альтернатива — переписать `task-refinement` под local storage — отклонена как дублирование `intent-clarification`.

### 3. Python и LLM paths разделяют один функциональный контракт

Оба path принимают все поддерживаемые v1 configurations, создают одинаковые отсутствующие artifacts, сохраняют существующие files и одинаково соблюдают provider/no-write boundaries. LLM path остаётся opt-in после отсутствия Python 3.10+ и сообщает более слабую детерминированность, но не урезает функциональность из-за custom roots или наличия OpenSpec.

Agent instructions должны описывать те же preflight, classification, create-only и readback guarantees, не пытаясь вызвать или имитировать Python после выбора fallback.

### 4. `openspec/` является только directory hint во время init

Initializer проверяет лишь наличие real directory без symlink traversal. Для standalone provider он показывает opt-in hint; для уже выбранного OpenSpec provider — нейтральное подтверждение. Содержимое каталога и required artifacts проверяет конкретная provider operation.

Directory detection само по себе не разрешает writes, но explicit standalone custom root под `openspec/**` остаётся авторитетным пользовательским выбором. No-write boundary относится к OpenSpec provider-owned artifacts и к неявному detection, а не запрещает user-configured standalone namespace.

Альтернатива — считать `openspec/config.yaml` маркером валидности — отклонена, чтобы не связывать initialization с layout конкретной версии provider-а.

### 5. Additive retry заменяет transactionality

Все writes остаются create-only. При поздней I/O-ошибке сообщение предупреждает о возможном partial workspace и предлагает устранить причину и повторить init. Повторный запуск сохраняет существующие bytes и достраивает отсутствующее.

Если write или close нового файла падает, initializer удаляет только incomplete file, который отсутствовал до текущей попытки. Остальные созданные artifacts не откатываются; это per-file cleanup, а не transactional workspace initialization.

### 6. OpenSpec instructions имеют одного владельца

Repo-local `openspec/AGENTS.md` обновляется как обычный project artifact. Недостижимый `skills/usw-initialize-project/templates/openspec/AGENTS.md` удаляется; initializer не получает разрешение писать или обновлять AGENTS в чужом OpenSpec workspace.

### 7. Flow regression проверяет новый control contract

`chat-review` test ожидает `handle-follow-up` и три routes GATE, а не только увеличивает число actions. Это защищает выбранную семантику follow-up mode.

## Risks / Trade-offs

- [LLM execution менее детерминировано, чем Python] → сохранять явное согласие пользователя, полный preflight, create-only writes и readback verification.
- [Пользователь может намеренно или случайно track `.usw/**`] → документировать user-owned policy; не заявлять enforced privacy guarantee.
- [Partial workspace остаётся после I/O failure] → возвращать non-zero/error outcome с retry guidance; idempotency делает восстановление безопасным.
- [Простой directory hint может быть false positive] → сообщение не называет каталог валидным workspace и не меняет provider selection.
- [Удаление `refinement.root` ломает старую configuration surface] → диагностировать legacy key как неподдерживаемый либо игнорируемый согласно implementation task, не мигрировать данные и описать breaking change.

## Migration Plan

1. Сначала обновить delta specs и tests для нового initialization/refinement contract.
2. Удалить Git enforcement и legacy refinement configuration из initializer и intent clarification implementation.
3. Переписать LLM fallback на функциональную v1 parity и provider-aware behavior.
4. Синхронизировать README, command/skill instructions и OpenSpec AGENTS ownership.
5. Обновить `chat-review` regression и выполнить полный unittest suite.

Rollback выполняется возвратом implementation/docs/tests вместе; исторические shared refinement files и OpenSpec artifacts не изменяются, поэтому data rollback не требуется.

## Open Questions

Нет. Все policy decisions приняты владельцем в `chat-review` follow-up.
