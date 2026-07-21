# Refinement session: Execution evidence open questions

- ID: `execution-evidence-open-questions`
- Status: ready
- Updated: 2026-07-21T12:43:49+03:00
- Target: OpenSpec change `establish-standalone-usw-workflow`
- Current case: None — all scoped decision cases are closed.

## Goal

Последовательно закрыть оставшиеся вопросы дизайна standalone USW workflow и
подготовить согласованный результат для обновления change-артефактов.

## Scope

- Правило устаревания Development и Testing evidence.
- Первая pinned-версия OpenSpec для compatibility tests.
- Граница будущего provider path mapping.

## Non-scope

- Изменение change-артефактов или product code во время refinement.
- Реализация templates, adapters или compatibility infrastructure.

## Confirmed context

- Development и Testing ведут раздельные evidence files.
- Evidence связано с contract revision и source identity; прежние факты не
  удаляются.
- Изменение только порядка локальных operations не меняет contract revision.
- Один pinned OpenSpec target блокирует release, а latest probe остаётся
  неблокирующим.
- В v1 реализуются standalone и OpenSpec providers; произвольный внешний
  provider API не входит в scope.

## Assumptions

- Для v1 важнее детерминированное безопасное правило, чем минимизация каждого
  повторного запуска verification.

## Decision cases

- [x] `C-001` — Определить гранулярность устаревания evidence.
- [x] `C-002` — Выбрать первую pinned-версию OpenSpec.
- [x] `C-003` — Подтвердить границу будущего provider path mapping.

## Current case

None. All scoped decision cases are closed.

## Next action

Update the existing OpenSpec change from `outcome.md` without modifying product
code.

## References

- `openspec/changes/establish-standalone-usw-workflow/design.md`
- `openspec/changes/establish-standalone-usw-workflow/specs/execution-artifacts/spec.md`
