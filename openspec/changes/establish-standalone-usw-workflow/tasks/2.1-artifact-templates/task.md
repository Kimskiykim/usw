# Задача 2.1: Добавить канонические templates и review receipts

## Artifact model

- `legacy`

## Результат

Package содержит полный standalone layout для change, task и reviewer receipts,
а каждый вид состояния имеет одного документированного и проверяемого владельца.

## Область

- Добавить templates для proposal, design, capability spec, task index,
  granular task contract с Contract revision и Milestone log, раздельных
  `development-evidence.md` и `testing-evidence.md`.
- Добавить template неизменяемого reviewer receipt с gate, subject/source
  identity, owner role, sorted reviewed artifact identities, previous attempt,
  reviewer, verdict, timestamp и ссылками на findings. Для v1 task требовать
  contract revision, source и evidence IDs; для legacy task — digest `task.md` и
  observed verification references. Sender/receiver требовать только для
  transition gate.
- Кодировать стабильные task IDs и ссылки из `tasks.md` в `task.md`.
- Валидировать, что completion checkboxes существуют только в `tasks.md`.
- Сделать receipt единственной shared transition record без task-level
  `plan.md` или `handoff.md`.
- Добавить для `.usw/HANDOFF.md` строгие metadata, Session journal и
  Verification tables, typed Subject, текущую Role, одно Next action и trusted
  source snapshot.
- Кодировать receipt subjects через typed namespace
  `refinement/<id>`, `change/<id>` и `task/<change-id>/<task-id>` и валидировать
  path safety и отсутствие cross-type collisions.
- Явно пометить все существующие leaf tasks active change как
  `Artifact model: legacy` без создания v1 evidence или Milestone log.
- Записать в `tasks.md` activation task `2.1` и исчерпывающий legacy allowlist;
  запрещать его расширение после завершения 2.1.
- Маркировать новые tasks из template как `Artifact model: v1` и применять к ним
  полный v1 contract после завершения 2.1.

## Вне области

- Выполнение других product tasks, их verification или human review; собственная
  verification задачи 2.1 остаётся обязательной по её legacy contract.
- Порядок flow scenarios.
- OpenSpec planning-artifact mapping.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/execution-artifacts/spec.md`

## Зависимости

- Задача 1.1.

## Критерии готовности

- Каждый artifact из standalone layout имеет packaged template.
- Receipt template не копирует requirements или evidence content.
- Ownership и checkbox invariants проверяются автоматически.
- Generated leaf task содержит scope, non-scope, dependencies, definition of
  done, verification, `Artifact model: v1`, Contract revision и Milestone log;
  contract identity не включает изменяемый log.
- Development и Testing evidence имеют раздельные writer authority и stable IDs.
- Freshness evidence вычисляется из сохранённых и текущих contract/source
  identities без переписывания entries другой роли.
- Typed receipt subjects не конфликтуют между refinement, change и task, а
  unsafe path segments отклоняются до записи.
- Internal receipt требует owner role без sender/receiver; transition receipt
  требует owner role, sender и receiver.
- Изменение любого reviewed planning artifact инвалидирует применимость receipt
  независимо от product source identity.
- Legacy task review не требует отсутствующих v1 contract/evidence fields и не
  создаёт их задним числом.
- Локальный handoff остаётся bounded current checkpoint, а не shared history.
- Existing tasks имеют явную legacy classification; validator не выводит её из
  отсутствующих files и не требует backfilled evidence. Task вне frozen legacy
  allowlist не может объявить legacy model.

## Проверка

- Запустить: `python3 -m unittest tests.test_package_layout tests.test_artifact_contract -v`
- Ожидание: templates упакованы, а authority, receipt и checkbox invariants
  проходят.
