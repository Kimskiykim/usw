# Refinement outcome: Workflow review open questions

- Refinement: `workflow-review-open-questions`
- Status: ready
- Updated: 2026-07-21T13:21:56+03:00
- Target: OpenSpec change `establish-standalone-usw-workflow`

## Goal

Закрыть три продуктовые развилки из независимого review перед продолжением
реализации standalone USW workflow.

## Agreed model

- Execution-artifact model v1 применяется только к tasks, созданным после
  завершения задачи 2.1.
- Существующие task contracts получают явную метку `legacy`; новые templates
  создают tasks с `artifact model: v1`. Legacy tasks не мигрируют evidence.
- Source identity v1 является canonical digest base commit и всего текущего
  product candidate: tracked changes и untracked product files включаются, а
  `.git`, `.usw` и configured workflow artifact roots исключаются.
- Canonical source manifest сортирует project-relative paths и учитывает file
  kind, deletion и content hash.
- Один receipt schema использует общие обязательные gate, owner role, reviewer,
  scope, identities, evidence IDs, verdict и timestamp.
- `sender` и `receiver` обязательны только для transition review; internal
  review не моделируется как передача ответственности.

## Constraints

- Validators применяют v1 completion invariants только к tasks с
  `artifact model: v1`.
- Legacy classification должна быть явной, а не выводиться из отсутствующих
  файлов или Git history.
- Workflow artifacts не должны самоинвалидировать product source identity.
- Любое изменение включённого product candidate инвалидирует всё Development и
  Testing evidence задачи.
- Receipt validator обязан проверять conditional fields по gate.

## Remaining unknowns

- None within the scoped review questions.

## Decision references

- `D-001`
- `D-002`
- `D-003`

## Recommended next flow

Use `usw:openspec-update-change` to apply these decisions coherently to the
existing planning artifacts, remove the resolved open questions, and run strict
OpenSpec validation. Do not modify product code in that flow.
