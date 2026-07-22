# Task 8.1: Убрать write-metadata из новых flow версии 1

## Artifact model

- `v1`

## Result

Новые flow версии `1` не содержат `Пишет` и раздел полномочий записи, а runner
по-прежнему исполняет существующую verbose-форму.

## Scope

- Упростить canonical version-1 reference.
- Разрешить concise и legacy verbose формы в parser.
- Для concise skill-step использовать write-contract executor.
- Сохранить отдельное разрешение на запуск project-local scripts.
- Добавить contract и runtime regression tests.

## Non-scope

- Исполнение `version-2`, наблюдение фактических filesystem writes и HANDOFF.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Task 7.1.

## Definition of done

- Новый version-1 reference не содержит write-metadata.
- Concise skill-flow получает write-contract из executor и выполняется.
- Существующая verbose-форма сохраняет прежнюю строгую проверку.
- Смешанная форма отклоняется до исполнения.
- Targeted tests, full suite и strict OpenSpec validation проходят.

## Verification

- Run: `python3 -m unittest tests.test_package_layout tests.test_flow_scenarios tests.test_flow_orchestrator -v`
- Run: `python3 -m unittest discover -s tests -v`
- Run: `openspec validate add-markdown-flow-composition --type change --strict`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | concise version-1 | `cr-001` | `usw-source-v1:fb982e192c3b67bf24ad3f61a46958df71379cb6440d13b653d03ea6bc91f17a` | verified | `development-evidence.md` |
