## Why

Role-based `HANDOFF.md` принадлежит снятому формату и сохраняет отдельные ветки чтения, запрета записи и Finish в routed runtime. Удаление поддержки оставит один контракт для активного handoff и явную ошибку для неподдерживаемого файла.

## Scope

- Удалить распознавание и обработку role-based HANDOFF из runtime, CLI, тестов и актуальной документации.
- Считать такой файл невалидным и не изменять его при обращении к handoff-командам.

## Non-goals

- Не менять generic single-state migration, routed state, `.usw/FLOW.json` и другие legacy-механизмы USW.
- Не применять пока черновик общего сокращения `usw-manage-handoff/SKILL.md`.

## What Changes

- **BREAKING**: Show, Resume и Finish больше не принимают role-based HANDOFF; его чтение даёт `invalid_handoff` без изменения state files.
- Удаляются role-based parser, специальные ветки команд и поле `legacy` из CLI-ответов handoff.
- Нормативная спека, product skills, reference и тесты приводятся к одному поведению.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `live-operation-state`: role-based HANDOFF перестаёт поддерживаться; существующий файл отклоняется без изменения.

## Impact

`skills/usw-manage-handoff/scripts/handoff_state.py`, `skills/usw-manage-handoff/`, `skills/usw-run-flow/SKILL.md`, тесты handoff и `openspec/specs/live-operation-state/spec.md`. Публичные JSON-ответы Show/Resume теряют поле `legacy`.
