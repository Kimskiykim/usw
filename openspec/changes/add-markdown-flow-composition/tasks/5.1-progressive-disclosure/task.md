# Task 5.1: Разделить контракты версий на references

## Artifact model

- `v1`

## Result

`usw-create-flow` загружает инструкции только выбранной версии, называет
structured-контракт `version-2` и сохраняет общие safety-инварианты в основном
skill.

## Scope

- Оставить выбор версии и общую безопасность в `SKILL.md`.
- Вынести форму, version-specific проверку и отчёт в два прямых reference.
- Использовать имя и reference `version-2`.
- Проверить маршрутизацию и сохранение обоих контрактов.

## Non-scope

- Parser, runtime, scripts, зависимости и исполнение `version-2`.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Tasks 1.1–4.4.

## Definition of done

- До выбора версии не требуется ни один version-specific reference.
- После выбора требуется ровно один reference выбранной версии.
- Structured-флаг и документ используют точное имя `version-2`.
- Targeted tests, full suite и strict OpenSpec validation проходят.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`
- Run: `python3 -m unittest discover -s tests -v`
- Run: `openspec validate add-markdown-flow-composition --type change --strict`

## Contract revision

- `cr-002`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | progressive disclosure | `cr-001` | `usw-source-v1:fb5625aa4a283dacceb888b575eb77c5a338113c62d4dc2d8ce080fc41e640d1` | verified | `development-evidence.md` |
| 2 | version rename | `cr-002` | `usw-source-v1:e725ad0db4f0626d8f528345501119d13a76f701db9bd0c080d58b5dba1bdc66` | verified | `development-evidence.md` |
