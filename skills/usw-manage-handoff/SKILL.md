---
name: usw-manage-handoff
description: Manage optional developer-local routed work state in .usw/HANDOFF.md.
---

# Manage USW handoff

Handoff является optional developer-local recovery state, а не shared artifact,
audit log, product-file lock или machine cursor.

## Configuration boundary

Сначала найти ближайший Git root и прочитать top-level `handoff` из `usw.yaml`.
Отсутствующее поле означает `true`.

При `handoff: false` не проверять наличие, тип или содержимое
`.usw/HANDOFF.md`, `.usw/handoffs/` и operation-scoped candidates, не создавать
и не изменять их. Для любого mode объяснить, что capability отключена
конфигурацией, и вернуть управление.

При enabled handoff использовать `scripts/handoff_state.py`. Missing HANDOFF
требует `/usw-init`.

## Routed state

`.usw/HANDOFF.md` — validated Markdown router. Он хранит только exact operation
IDs и generated relative paths. Mutable status и recovery context каждой
operation находятся в `.usw/handoffs/<operation-hex>.md`.

Operation document содержит flow name, origin, flow identity, input digest,
operation identity и human-readable sections:

- Input;
- Done;
- Current position;
- Next action;
- Blocker;
- Checks;
- References.

`Current position` — narrative text, не machine cursor. Статусы operation:
`in_progress`, `paused`, `blocked`, `decision_required`, `failed`, `completed`.
Empty router означает отсутствие зарегистрированной работы.

Generic single-state HANDOFF мигрировать под lock: idle превращается в empty
router, non-idle сначала exact-byte записывается в operation document и только
потом регистрируется. Legacy role-based HANDOFF доступен только для
Show/Resume/Finish, блокирует Begin и не мигрируется автоматически.

## Begin

Begin доступен после безопасного resolve flow:

```text
python3 <script> begin <project> <flow> <origin> <flow-identity> <exact-input>
```

Script создаёт уникальный invocation token и operation ID из token, origin,
flow identity и SHA-256 exact input. Под общим коротким lock он:

1. создаёт и подтверждает `in_progress` operation document;
2. добавляет exact operation ID в router и подтверждает readback;
3. возвращает operation ID и path.

Executor MUST NOT начинаться до успешного Begin. Другие recoverable или
terminal operations не блокируют новый Begin. Даже одинаковые flow/input
получают разные IDs. USW не проверяет, пересекаются ли их product writes.

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

Outcome разрешает exact ID через router, проверяет embedded identity и immutable
flow/input context и изменяет только выбранный operation document. Missing,
finished, mismatched и terminal target отклоняются без изменения других
operations. Permission boundary записывать как `decision_required`; checks
должны быть фактическими.

## Save

Для явного `/usw-handoff` подготовить candidate
`.usw/handoffs/<operation-hex>.next.md`, затем вызвать:

```text
python3 <script> save <project> <operation-id> <candidate>
```

Save обновляет только exact recoverable operation, не меняет identity,
flow/input context и не заменяет legacy или terminal state. После подтверждения
candidate удаляется. Не создавать историю tool calls и не записывать
выдуманные результаты.

## Show и Resume

Вызвать `show` или `resume` с optional exact operation ID:

```text
python3 <script> resume <project> [operation-id]
```

- empty router — продолжать нечего;
- одна route без selector — выбрать её;
- несколько routes без selector — показать validated список flow/status и
  ждать выбора, ничего не продолжая;
- `in_progress` — mutation могла прерваться, не повторять автоматически;
- `paused`, `blocked`, `decision_required` — показать recovery context и ждать
  явного продолжения той же operation;
- `failed`, `completed` — показать terminal outcome до Finish;
- legacy — показать role context только для recovery.

## Read-only parent check

Nested executor перед model execution вызывает:

```text
python3 <script> assert-current <project> <parent-operation-id>
```

Check принимает только exact registered `in_progress`, `paused`, `blocked` или
`decision_required` parent. Он не мигрирует и не изменяет router или operation
document. Nested executor не вызывает Begin, Outcome, Save или Finish.

## Finish

Finish адресуется exact operation ID:

```text
python3 <script> finish <project> [operation-id]
```

Без ID применить те же zero/one/many selection rules. Finish сначала
подтверждённо удаляет route, затем только её operation document и candidate.
Cleanup failure после unregistration может оставить безопасный orphan, но не
возвращает operation в recovery. Legacy Finish создаёт empty router. Не
архивировать состояние и не изменять product files.

Return point: после одного подтверждённого Begin, Outcome, Save, Show, Resume,
assert-current или Finish.
