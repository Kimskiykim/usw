# Refinement decisions: Workflow review open questions

## `D-001` — Применять v1 execution artifacts только к новым задачам

- Case: `C-001`
- Status: accepted
- Decided: 2026-07-21T13:18:14+03:00
- Decision: задачи, существующие до завершения 2.1, сохраняют legacy execution
  model; canonical v1 layout и completion invariants обязательны только для
  задач, созданных после 2.1.
- Basis: пользователь выбрал non-retroactive adoption вместо migration текущих
  задач или отдельной bootstrap-задачи.
- Consequences: 2.1 явно маркирует существующие task contracts как `legacy`, а
  новый template создаёт tasks с `artifact model: v1`; validators применяют v1
  invariants только к последним. Исторические tasks не получают выдуманное или
  backfilled evidence, а active change временно содержит две явные модели.
- Supersedes: None.
- Follow-up cases: None.

## `D-002` — Идентифицировать весь product candidate

- Case: `C-002`
- Status: accepted
- Decided: 2026-07-21T13:20:31+03:00
- Decision: source identity v1 является canonical digest base commit и полного
  текущего product candidate, включая tracked changes и untracked product files,
  но исключая `.git`, `.usw` и configured workflow artifact roots.
- Basis: пользователь выбрал консервативную worktree identity, которая не
  зависит от ручного определения task-owned paths и доступна до commit.
- Consequences: evidence, receipts, resume snapshot и Delivery используют один
  digest; любое изменение включённого product state инвалидирует всё evidence
  задачи, даже если изменение логически не связано с ней. Canonicalization должна
  сортировать project-relative paths и учитывать file kind, deletion и content
  hash, чтобы результат был воспроизводимым.
- Supersedes: None.
- Follow-up cases: None.

## `D-003` — Использовать conditional fields в едином receipt schema

- Case: `C-003`
- Status: accepted
- Decided: 2026-07-21T13:21:56+03:00
- Decision: один receipt schema имеет общие обязательные fields `gate`, owner
  role, reviewer, reviewed scope, contract/source identities, evidence IDs,
  verdict и timestamp; `sender` и `receiver` обязательны только для transition
  review и запрещены либо отсутствуют для internal review.
- Basis: пользователь выбрал единый формат без ложного self-transition.
- Consequences: validator ветвится по `gate`; internal receipt не означает
  передачу ответственности, transition receipt остаётся единственной общей
  записью такой передачи.
- Supersedes: None.
- Follow-up cases: None.
