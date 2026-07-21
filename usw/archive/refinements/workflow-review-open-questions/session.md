# Refinement session: Workflow review open questions

- ID: `workflow-review-open-questions`
- Status: ready
- Updated: 2026-07-21T13:21:56+03:00
- Target: OpenSpec change `establish-standalone-usw-workflow`
- Current case: None — all scoped decision cases are closed.

## Goal

Итеративно закрыть три продуктовые развилки из независимого review и подготовить
согласованный input для обновления change-артефактов.

## Scope

- Activation/bootstrap execution-artifact invariants.
- Каноническая граница и форма task source identity.
- Поля receipt для internal review.

## Non-scope

- Изменение target change-артефактов или product code во время refinement.
- Повторное обсуждение уже согласованных pin OpenSpec, evidence invalidation и
  provider extension boundaries.

## Confirmed context

- Task 2.1 создаёт canonical execution-artifact templates и мигрирует уже
  существующие leaf tasks.
- Общий completion invariant требует актуальное Development evidence.
- До выполнения 2.1 задачи 1.1 и сама 2.1 ещё не имеют нового canonical layout.
- Историческое evidence нельзя выдумывать; completed checks подтверждаются
  только фактическим повторным запуском.
- Независимое review обнаружило нормативный bootstrap cycle.

## Assumptions

- V1 может иметь явную одноразовую activation boundary, если она наблюдаема и
  безопасна после частично завершённой migration.

## Decision cases

- [x] `C-001` — Выбрать bootstrap execution-artifact model.
- [x] `C-002` — Выбрать task source identity.
- [x] `C-003` — Определить schema internal-review receipt.

## Current case

None. All scoped decision cases are closed.

## Next action

Update the existing OpenSpec change from `outcome.md` without modifying product
code.

## References

- `openspec/changes/establish-standalone-usw-workflow/design.md`
- `openspec/changes/establish-standalone-usw-workflow/specs/execution-artifacts/spec.md`
- `openspec/changes/establish-standalone-usw-workflow/tasks/2.1-artifact-templates/task.md`
