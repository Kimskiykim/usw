# Task 3.2: Проверить ошибки, остановки и возобновление

## Artifact model

- `v1`

## Result

Проверки runner подтверждают последовательность элементов и консервативные
остановки на ошибках и неизвестном результате.

## Scope

- Проверить explorer result с несколькими группами и один элемент за invocation.
- Проверить пустой список и полное завершение обхода.
- Проверить отсутствующий список, duplicate names и missing item reference.
- Проверить failed, blocked, decision_required и permission violation.
- Проверить `outcome_unknown` без retry и перехода к следующему элементу.

## Non-scope

- Нагрузочные проверки и параллельное выполнение.
- Новый test framework или fixture subsystem.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/result-list-iteration/spec.md`

## Dependencies

- Task 2.2.
- Task 3.1.

## Definition of done

- Проверки падают при повторе завершённого или неизвестного элемента.
- Resume использует сохранённый snapshot, а не актуальное содержимое источника.
- Существующие сценарии одного действия остаются успешными.

## Verification

- Run: `python3 -m unittest tests.test_flow_orchestrator tests.test_handoff_state -v`
- Expect: iteration error, stop and resume cases pass.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
