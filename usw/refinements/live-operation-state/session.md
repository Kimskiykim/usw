# Refinement session: Live operation state

- ID: `live-operation-state`
- Status: ready
- Updated: 2026-07-21T16:55:48+03:00
- Target: будущий OpenSpec change для live operation state
- Current case: None — all scoped decision cases are closed.

## Goal

Согласовать минимальную модель, которая до изменения рабочих файлов фиксирует,
кто начинает атомарное действие, в рамках какой задачи и с какими полномочиями,
а после действия сохраняет его фактический результат и позволяет восстановиться
после прерывания.

## Scope

- Запись начала и завершения атомарного действия.
- Связь исполнителя, flow, шага, task/change scope и write authority.
- Восстановление после прерывания и отношение к `.usw/FLOW.json`.
- Жизненный цикл и очистка developer-local operational state.

## Non-scope

- Логирование каждого tool-call, чтения файла или промежуточного рассуждения.
- Командный audit log и долговременная история действий.
- Реализация до завершения refinement.

## Confirmed context

- `.usw/HANDOFF.md` сейчас обновляется только через явный `/usw-handoff`.
- Custom flow хранит машинный курсор отдельно в `.usw/FLOW.json`.
- `usw-run-flow` не вызывает `usw-manage-handoff` на границах шага.
- Пользователь хочет запись до mutation с исполнителем, task scope и областью
  предполагаемых изменений.
- При восстановлении агент должен сначала читать только компактное текущее
  состояние и переходить к подробным артефактам по ссылкам лишь при необходимости.

## Assumptions

- Полезная гранулярность — один атомарный skill/script step, а не каждый tool-call.
- Состояние остаётся developer-local в `.usw/`.

## Decision cases

- [x] `C-001` — Выбрать форму operational state: снимок, task-scoped journal или durable audit log.
- [x] `C-002` — Определить точные границы begin/complete/fail и порядок записей.
- [x] `C-003` — Определить обязательные поля исполнителя, scope и write intent.
- [x] `C-004` — Разделить ответственность между Markdown state и `FLOW.json`.
- [x] `C-005` — Определить очистку, удержание и поведение resume.

## Current case

None. All scoped decision cases are closed.

## Next action

Create an OpenSpec change from `outcome.md`; do not modify product code in the
proposal flow.

## References

- `.usw/HANDOFF.md`
- `.usw/FLOW.json`
- `skills/usw-manage-handoff/SKILL.md`
- `skills/usw-run-flow/SKILL.md`
