# Task 1.2: Запрашивать версию без structured-флага

## Artifact model

- `v1`

## Result

Без `-s` и `--structured` версия выбирается пользователем до записи flow.

## Scope

- Зафиксировать обязательный вопрос и запрет записи до ответа.

## Non-scope

- Автоматический выбор версии по описанию.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Task 1.1.

## Definition of done

- Skill не выбирает версию и не пишет файл без ответа пользователя.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
