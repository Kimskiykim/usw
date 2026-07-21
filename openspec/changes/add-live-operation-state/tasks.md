## 1. HANDOFF contract

- [x] 1.1 Обновить HANDOFF template: current `op-NNN`, actor, role, executor, scope, flow cursor, intent, writes, result, actual areas, verification, compact journal, next action и references.
- [x] 1.2 Обновить `usw-manage-handoff` для summary-first show/resume, conservative `in_progress` recovery и явного finish без выдуманных legacy fields.

## 2. Flow protocol

- [x] 2.1 Обновить `usw-run-flow`: preflight → HANDOFF begin → read-back → один executor → authority check → HANDOFF outcome.
- [x] 2.2 Зафиксировать блокировку другого flow/scope, отсутствие automatic retry и ручную обработку `.usw/FLOW.json`.

## 3. Commands and documentation

- [x] 3.1 Обновить `/usw-handoff`, `/usw-resume` и README для нового operation summary и lifecycle.
- [x] 3.2 Добавить Markdown-сценарий interruption/resume/completed/finish без отдельного runtime state.

## 4. Verification

- [x] 4.1 Проверить согласованность шаблона, skills и commands статическим поиском и существующими package checks.
- [x] 4.2 Запустить строгую OpenSpec validation и подтвердить отсутствие изменений `*.py`, новых runtime dependencies и автоматического второго state-файла.
