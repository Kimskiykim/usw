# Refinement outcome: Live operation state

- Refinement: `live-operation-state`
- Status: ready
- Updated: 2026-07-21T16:55:48+03:00
- Target: будущий OpenSpec change для live operation state

## Goal

Сделать developer-local состояние наблюдаемым до mutation: фиксировать, кто,
каким executor и в рамках какой задачи начинает атомарное действие, сохранять
результат и обеспечивать безопасное восстановление после прерывания.

## Agreed model

- `.usw/HANDOFF.md` является единственным атомарно обновляемым operational state;
  отдельный `.usw/FLOW.json` удаляется.
- State использует summary-first модель: одна текущая операция и компактный
  task-scoped список завершённых операций; подробности остаются в существующих
  артефактах и читаются по references только при необходимости.
- Гранулярность равна одному atomic skill/script step; tool-call, чтения и
  рассуждения не журналируются.
- Orchestrator сначала полностью проверяет flow, scope, capability и write
  authority, затем сохраняет `in_progress` и только после успешной записи
  вызывает executor.
- Обязательные поля: operation ID, actor/role, exact executor, task/change scope,
  flow step, однострочный intent, declared write roles/areas, status, started
  timestamp и references.
- Точные planned paths необязательны; actual changed paths и verification
  references записываются в outcome после выполнения.
- `in_progress` без outcome обозначает возможное прерывание внутри executor;
  resume сначала проверяет фактические изменения и не выполняет автоматический
  повторный запуск.
- Любое non-idle состояние сохраняется до явного `/usw-handoff finish`.
- Продолжить можно только тот же flow и scope; новая работа строго блокируется,
  пока человек не выполнит resume либо finish.

## Constraints

- Operational state остаётся developer-local под `.usw/` и не является shared
  audit history.
- Новый flow не может молча очистить, архивировать или перезаписать journal.
- Завершённая операция переносится в journal одной компактной строкой, а не
  записывается отдельными begin/end events.
- Markdown обязан иметь детерминированный parser/validator и атомарную запись.
- Восстановление не объявляет прерванную mutation завершённой без проверки
  фактического состояния и evidence.
- Постоянный audit-log, отдельные журналы скиллов и configurable retention в MVP
  не вводятся.

## Remaining unknowns

- Точные имена Markdown fields и совместимая миграция текущего idle/v1 handoff.
- Детерминированный формат operation ID.

## Decision references

- `D-001`
- `D-002`
- `D-003`
- `D-004`
- `D-005`

## Recommended next flow

Use `usw:openspec-propose` to create one change from this outcome, including
specification of begin/outcome ordering, resume behavior, migration away from
`.usw/FLOW.json`, tests for interruption boundaries, and strict OpenSpec
validation. Do not implement product code in the proposal flow.
