# Task 3.1: Добавить статический checklist

## Artifact model

- `v1`

## Result

Structured-flow проверяется на обязательные разделы, имена, ссылки, решения, loops и executors.

## Scope

- Добавить явный ручной checklist в skill.

## Non-scope

- Детерминированный parser.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Tasks 2.1–2.3.

## Definition of done

- Очевидная структурная ошибка не считается успешным созданием.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`

## Contract revision

- `cr-002`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
| 2 | MVP boundary | `cr-002` | `usw-source-v1:a8f57e82367218382f421f36170868dec2eb9462b9c4aace29803e8a7899e288` | verified | `development-evidence.md` |
