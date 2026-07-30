---
name: usw-manage-handoff
description: Manage optional developer-local generic work state in .usw/HANDOFF.md.
---

# Manage USW handoff

Handoff является optional developer-local recovery state, а не shared artifact,
audit log или machine cursor.

## Configuration boundary

Сначала найти ближайший Git root и прочитать top-level `handoff` из `usw.yaml`.
Отсутствующее поле означает `true`.

При `handoff: false` не проверять наличие, тип или содержимое
`.usw/HANDOFF.md`, не создавать и не изменять его. Для любого mode объяснить,
что capability отключена конфигурацией, и вернуть управление.

При enabled handoff использовать
`scripts/handoff_state.py`. Missing HANDOFF требует `/usw-init`.

## Generic state

Generic state содержит flow name, origin, flow identity, input digest, operation
identity и human-readable sections:

- Input;
- Done;
- Current position;
- Next action;
- Blocker;
- Checks;
- References.

`Current position` — narrative text, не machine cursor. Handoff не требует
role, typed subject, write authority или evidence.

Статусы: `idle`, `in_progress`, `paused`, `blocked`, `decision_required`,
`failed`, `completed`.

`in_progress`, `paused`, `blocked` и `decision_required` блокируют новую
operation до explicit finish. `failed` и `completed` сохраняются для inspect,
но следующий Begin может атомарно заменить их новой operation.

## Begin

Begin доступен только после безопасного resolve flow и когда HANDOFF находится
в `idle`, `failed` или `completed`:

```text
python3 <script> begin <project> <flow> <origin> <flow-identity> <exact-input>
```

Script создаёт уникальный invocation token, вычисляет operation identity из
token, origin, flow identity и SHA-256 exact input, atomарно записывает
`in_progress` и подтверждает exact-byte readback. Даже одинаковые повторные
запуски имеют разные operation ID. Executor MUST NOT начинаться до успешного
Begin.

Legacy role-based HANDOFF и любой generic recoverable state блокируют Begin.
Begin поверх terminal state создаёт новый invocation и operation identity под
тем же lock; stale Outcome прежней operation после этого отклоняется.

## Outcome

После естественной остановки вызвать:

```text
python3 <script> outcome <project> <status>
  --operation <begin-operation-id>
  --done <fact>
  --position <narrative-position>
  --next-action <one-line-action>
  --blocker <fact-or-none>
  [--check <fact>]...
  [--reference <path-or-fact>]...
```

Передавать exact operation ID, возвращённый Begin. Stale Outcome отклоняется,
если этот ID больше не является текущим. Permission boundary записывать как
`decision_required`. Записывать только фактические checks. Если Outcome не
удалось подтвердить, считать прежний `in_progress` потенциально активным и не
запускать следующую operation.

## Save

Для явного `/usw-handoff` подготовить generic
`.usw/HANDOFF.next.md`, затем вызвать:

```text
python3 <script> save <project> <candidate>
```

Save обновляет только текущую recoverable operation с неизменным flow/input
context. При каждом чтении decoded Input обязан совпадать со своим digest. Save
не создаёт operation из idle, не очищает state, не заменяет legacy/terminal
HANDOFF и не меняет operation identity. Не создавать историю tool calls и не
записывать выдуманные результаты.

## Resume

Вызвать `resume` и прочитать state:

- `idle` — продолжать нечего;
- `in_progress` — mutation могла прерваться, не повторять автоматически;
- `paused`, `blocked`, `decision_required` — показать recovery context и ждать
  явного продолжения той же operation;
- `failed`, `completed` — показать terminal outcome; следующий Begin может
  заменить его без предварительного finish;
- legacy — показать сохранённый role context только для recovery, не запускать
  executor и не переписывать generic Outcome поверх старого формата.

## Finish

Только явный finish заменяет generic или legacy HANDOFF на generic idle:

```text
python3 <script> finish <project>
```

Не архивировать прежнее содержимое и не изменять product files.

Return point: после одного подтверждённого begin, outcome, save, resume, show
или finish.
