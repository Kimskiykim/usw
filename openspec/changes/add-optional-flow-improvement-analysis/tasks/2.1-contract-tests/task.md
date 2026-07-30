# Task 2.1: Закрепить optional analysis контракт тестами

## Artifact model

- `v1`

## Result

Package tests обнаруживают потерю neutral opt-in, read-only analysis boundary,
отдельного revision consent или существующего no-execution поведения.

## Scope

- Добавить целевые assertions в `tests/test_package_layout.py`.
- Проверить OpenSpec change и packaged skill.
- Выполнить целевую и полную регрессию.

## Non-scope

- Доказательство соблюдения инструкций любой моделью или coding harness.
- E2E-вызов внешнего агента.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/flow-authoring-assistance/spec.md`

## Dependencies

- Task 1.1.

## Definition of done

- Тесты проверяют порядок create/report/offer/analyze/revise.
- Тесты проверяют формулировку будущего анализа и запрет готовых «идей».
- Тесты сохраняют прежние default/structured и no-execution assertions.
- OpenSpec strict validation и полная test suite проходят.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`
- Run: `python3 -m unittest discover -s tests -v`
- Run: `openspec validate add-optional-flow-improvement-analysis --strict`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:f39d2e4e16948c71d5215ebceae0c812448c4c6c9369801626d70a9a8b954693` | verified | `development-evidence.md` |
| 2 | source refresh | `cr-001` | `usw-source-v1:b48ccd5ab5fab5ac5cb9c3ea7b5b9e1da07911944f383f664ed75d690edf9231` | verified | `development-evidence.md` |
| 3 | source refresh | `cr-001` | `usw-source-v1:d3c54bb69a2ef3e05f9b6b71a4244cbfdc037b4c93949fe2cf5ffd8fb8a94a18` | verified | `development-evidence.md` |
