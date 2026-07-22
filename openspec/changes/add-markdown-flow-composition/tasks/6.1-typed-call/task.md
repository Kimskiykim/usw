# Task 6.1: Заменить USING на typed CALL и определить payload субагента

## Artifact model

- `v1`

## Result

`version-2` использует однозначные typed `CALL`, а вложенная работа субагента
имеет видимую ownership boundary.

## Scope

- Разрешить `CALL SKILL`, `CALL SCRIPT`, `CALL FLOW`, `CALL SUBAGENT` и
  `CALL HUMAN` с точной целью в backticks.
- Исключить `MODEL` и прежний маркер `USING`.
- Описать вложенные именованные действия `CALL SUBAGENT`.
- Обновить канонический пример и контрактные тесты.

## Non-scope

- Parser, runtime, execution, HANDOFF и поддержка version-2 в runner.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/markdown-flow-composition/spec.md`

## Dependencies

- Tasks 1.1–5.1.

## Definition of done

- Канонический reference не использует `USING`.
- Все пять разрешённых `CALL` types и запрет `MODEL` зафиксированы.
- Subagent payload является вложенным блоком глобально уникальных действий.
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
| 1 | typed CALL grammar | `cr-001` | `usw-source-v1:7094195c1e1b2341ffd8def57f3362b769cbc09e16e87a30d5df00bfaad3ce1e` | verified | `development-evidence.md` |
| 2 | MVP boundary | `cr-002` | `usw-source-v1:a8f57e82367218382f421f36170868dec2eb9462b9c4aace29803e8a7899e288` | verified | `development-evidence.md` |
