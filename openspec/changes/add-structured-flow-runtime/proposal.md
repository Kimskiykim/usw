## Why

`usw-create-flow` уже создаёт структурированные Markdown-flow `version-2`, но
`usw-run-flow` умеет валидировать и исполнять только линейную версию `1`.
Созданные structured-flow должны стать исполнимыми без неявного толкования
prose во время запуска.

## What Changes

- Добавить детерминированный parser канонического executable-поднабора
  `version-2` с постоянными именами действий.
- Исполнять typed calls `CALL SKILL`, `CALL SCRIPT`, `CALL FLOW`,
  `CALL SUBAGENT` и `CALL HUMAN` через точные executors.
- Передавать вложенные действия `CALL SUBAGENT` как явный payload ближайшему
  enclosing subagent.
- Поддержать `GATE` с полными `IF`/`ELIF`/`ELSE` переходами, ограниченный
  `LOOP` и `PARALLEL` как одну observable orchestration boundary.
- Сохранять one-boundary-per-invocation, conservative resume, безопасное
  разрешение scripts и обратную совместимость flow версии `1`.
- Уточнить каноническую форму `version-2` и документацию раннера; неоднозначный
  Markdown отклонять до вызова executor.

## Capabilities

### New Capabilities

- `structured-flow-runtime`: валидация, разрешение executors, пошаговое
  исполнение и возобновление Markdown-flow `version-2`.

### Modified Capabilities

Нет.

## Impact

Изменение затрагивает `usw-run-flow`, reference `usw-create-flow` для
`version-2`, runtime parser/orchestrator, CLI validation report, README и
контрактные/регрессионные тесты. Новые зависимости и новый state-файл не
добавляются; версия `1` сохраняет прежнее поведение.
