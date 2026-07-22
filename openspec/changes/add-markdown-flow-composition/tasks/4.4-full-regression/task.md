# Task 4.4: Провести полную регрессионную проверку

## Artifact model

- `v1`

## Result

Targeted and full project suites pass with unchanged v1 execution behavior.

## Scope

- Run create-flow checks, full tests and strict OpenSpec validation.

## Non-scope

- Исправление unrelated failures.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Tasks 4.1–4.3.

## Definition of done

- Все доступные project tests и strict change validation проходят.

## Verification

- Run: `python3 -m unittest discover -s tests -v`
- Run: `openspec validate add-markdown-flow-composition --type change --strict`

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | full regression | `cr-001` | `usw-source-v1:5d6fc91f4dd496181c9440b9c257fbe247b3a0ff9c825ea19ad3143fa472f9ce` | verified | `development-evidence.md` |
