# Task 2.1: Добавить prose-first structured-контракт

## Artifact model

- `v1`

## Result

`version-2` фиксирует цель, действия, executors и управляющие связи в читаемом Markdown.

## Scope

- Описать постоянные имена и маркеры `CALL`, `GATE`, `IF`, `ELIF`, `ELSE`, `LOOP`, `PARALLEL`.

## Non-scope

- Machine-only manifest или parser.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Task 1.1.

## Definition of done

- Маркеры используются только для реально присутствующих конструкций.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`

## Contract revision

- `cr-002`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | implementation | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
| 2 | MVP boundary | `cr-002` | `usw-source-v1:a8f57e82367218382f421f36170868dec2eb9462b9c4aace29803e8a7899e288` | verified | `development-evidence.md` |
