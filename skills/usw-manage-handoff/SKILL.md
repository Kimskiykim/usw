---
name: usw-manage-handoff
description: Manage optional developer-local routed work state in .usw/HANDOFF.md.
---

# Manage USW handoff

Handoff — optional developer-local recovery state, а не shared artifact, audit
log, product-file lock или machine cursor.

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

`.usw/HANDOFF.md` — validated Markdown router и единственная таблица текущих
operations; authoritative mutable status и recovery context живут в operation
document `.usw/handoffs/<operation-hex>.md`. Статусы operation: `in_progress`,
`paused`, `blocked`, `decision_required`, `failed`, `completed`. Empty router
означает отсутствие зарегистрированной работы.

Operation document содержит flow name, origin, flow identity, input digest,
operation identity, one-line `Summary`, immutable `Started`, latest `Updated`,
`Workspace` и human-readable sections: Input, Done, Current position, Next
action, Blocker, Checks, References. `Current position` — narrative text.
Workspace и summary информационны: write authority и ownership они не дают.

Устройство router, вывод identity, семантика lock и миграции generic или
legacy HANDOFF — в [references/state-model.md](references/state-model.md).
Legacy role-based HANDOFF доступен только для Show/Resume/Finish и блокирует
Begin до Finish.

## Begin

Begin доступен после безопасного resolve flow:

```text
python3 <script> begin <project> <flow> <origin> <flow-identity> <exact-input>
  [--summary <one-line-summary>]
  [--expected-write <path-or-area>]...
```

- Executor не начинается до успешного Begin: script возвращает operation ID и
  path только после подтверждённых записей document и router.
- Другие recoverable или terminal operations не блокируют новый Begin. Даже
  одинаковые flow/input получают разные IDs. USW не проверяет, пересекаются ли
  их product writes.
- Summary передавать one-line; expected writes — только фактически следующие
  из scope, это informational hints.

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
  [--observed-change <path-or-area>]...
```

- Передавать ID, возвращённый Begin. Missing, finished, mismatched и terminal
  target script отклоняет, не меняя другие operations.
- Permission boundary записывать как `decision_required`; checks должны быть
  фактическими.
- Observed changes передавать только из фактического root outcome; изменения
  из общего `git status` operation не приписываются.

## Save

Для явного `/usw-handoff` подготовить candidate
`.usw/handoffs/<operation-hex>.next.md`, затем вызвать:

```text
python3 <script> save <project> <operation-id> <candidate>
```

- Save обновляет только exact recoverable operation: identity, flow/input
  context, Started, workspace base и expected writes не меняются, legacy и
  terminal state не заменяются.
- Не создавать историю tool calls и не записывать выдуманные результаты.
- После подтверждения candidate удаляется.

## Show и Resume

Вызвать `show` или `resume` с optional exact operation ID:

```text
python3 <script> resume <project> [operation-id]
```

- empty router — продолжать нечего;
- одна route без selector — выбрать её;
- несколько routes без selector — показать validated список
  summary/flow/status/Started/Updated и ждать выбора, ничего не продолжая;
- `in_progress` — mutation могла прерваться, не повторять автоматически;
- `paused`, `blocked`, `decision_required` — показать recovery context и ждать
  явного продолжения той же operation;
- `failed`, `completed` — показать terminal outcome и явные варианты Finish
  или Cleanup;
- legacy — показать role context только для recovery.

## Read-only parent check

Nested executor перед model execution вызывает:

```text
python3 <script> assert-current <project> <parent-operation-id>
```

Check принимает только exact registered `in_progress`, `paused`, `blocked` или
`decision_required` parent и ничего не изменяет ни при успехе, ни при отказе.
Nested executor не вызывает Begin, Outcome, Save или Finish.

## Finish

Finish адресуется exact operation ID:

```text
python3 <script> finish <project> [operation-id]
```

- Без ID применить те же zero/one/many selection rules.
- Удаляются только route выбранной operation, её document и candidate.
- Не архивировать состояние и не изменять product files.

## Cleanup

Cleanup удаляет сразу все зарегистрированные terminal operations и не трогает
`in_progress`, `paused`, `blocked` или `decision_required`:

```text
python3 <script> cleanup <project>
```

Если terminal operations отсутствуют, вернуть пустой список и ничего не
удалять. Legacy HANDOFF очищается только через explicit Finish.

Return point: после одного подтверждённого Begin, Outcome, Save, Show, Resume,
assert-current, Finish или Cleanup.
