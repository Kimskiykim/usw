# Task 4.1: Провести end-to-end и регрессионную проверку

## Artifact model

- `v1`

## Result

Канонический explorer → groups → `FOR EACH` сценарий проходит полный ручной
lifecycle, а прежние контракты остаются совместимыми.

## Scope

- Проверить составление без исполнения действий.
- Проверить snapshot до первого элемента, по одному элементу за вызов и resume.
- Проверить пустой список и `outcome_unknown`.
- Запустить целевые и полные тесты проекта.
- Подтвердить отсутствие нового parser, dependency и параллельного обхода.

## Non-scope

- Оптимизация больших списков.
- Автоматическая миграция существующих flow.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/result-list-iteration/spec.md`

## Dependencies

- Task 3.2.

## Definition of done

- End-to-end сценарий обрабатывает все группы ровно один раз и в исходном порядке.
- Версия `1` и `experimental-1` без `FOR EACH` проходят без миграции.
- Полный набор тестов успешен, новые runtime dependencies отсутствуют.

## Verification

- Run: `python3 -m unittest discover -s tests -v`
- Expect: full suite passes with canonical iteration scenario covered.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
