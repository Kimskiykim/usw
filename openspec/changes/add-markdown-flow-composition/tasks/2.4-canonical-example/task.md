# Task 2.4: Добавить канонический structured-пример

## Artifact model

- `v1`

## Result

Короткий пример показывает решение человека, bounded loop и две независимые проверки.

## Scope

- Добавить один self-contained Markdown example в skill.

## Non-scope

- Отдельная библиотека примеров.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Tasks 2.1–2.3.

## Definition of done

- Пример содержит все требуемые markers без повторения полной инструкции.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
