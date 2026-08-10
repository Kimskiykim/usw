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

`.usw/HANDOFF.md` — validated Markdown router и человекочитаемая таблица текущих
operations. Для каждой строки она показывает summary задачи, flow, status,
Updated и operation как ссылку на generated relative path. Эта таблица является
единственным router: exact operation ID восстанавливается из validated path.
Operation document в `.usw/handoffs/<operation-hex>.md` остаётся authoritative
для mutable status и recovery context.

Operation document содержит flow name, origin, flow identity, input digest,
operation identity, one-line `Summary`, immutable `Started`, latest `Updated` и
human-readable sections:

- Input;
- Done;
- Current position;
- Next action;
- Blocker;
- Checks;
- References;
- Workspace.

`Workspace` хранит Git base revision, bounded expected-write hints из Begin и
фактически reported changed areas последнего Outcome. Эти сведения нужны только
для recovery: они не предоставляют write authority, не доказывают ownership и
не обнаруживают пересечения между concurrent operations.

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
  [--summary <one-line-summary>]
  [--expected-write <path-or-area>]...
```

Script создаёт уникальный invocation token и operation ID из token, origin,
flow identity и SHA-256 exact input. Он фиксирует текущую Git revision либо
явное `unborn`, `not-git` или `unknown`; summary нормализует и ограничивает, а
при отсутствии выводит из exact input. Expected writes сохраняет как
informational hints.
Под общим коротким lock он:

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
  [--observed-change <path-or-area>]...
```

Outcome разрешает exact ID через router, проверяет embedded identity и immutable
flow/input context и изменяет только выбранный operation document. Missing,
finished, mismatched и terminal target отклоняются без изменения других
operations. Permission boundary записывать как `decision_required`; checks
должны быть фактическими. Observed changes передавать только из фактического
root outcome; script сохраняет их как hints и не приписывает operation изменения
из общего `git status`.

## Save

Для явного `/usw-handoff` подготовить candidate
`.usw/handoffs/<operation-hex>.next.md`, затем вызвать:

```text
python3 <script> save <project> <operation-id> <candidate>
```

Save обновляет только exact recoverable operation, не меняет identity,
flow/input context, Started, workspace base или expected writes и не заменяет
legacy или terminal state. Enriched operation нельзя заменить старой формой.
Старую generic operation разрешено обновить только enriched candidate с
`Started: unknown`, unknown base и пустыми expected writes. После подтверждения
candidate удаляется. Не создавать историю tool calls и не записывать выдуманные
результаты.

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
- `failed`, `completed` — показать terminal outcome и явные варианты Finish или
  Cleanup;
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

## Cleanup

Cleanup удаляет сразу все зарегистрированные terminal operations и не трогает
`in_progress`, `paused`, `blocked` или `decision_required`:

```text
python3 <script> cleanup <project>
```

Сначала подтвердить новый router без terminal routes, затем удалить только их
operation documents и candidates. Если terminal operations отсутствуют,
вернуть пустой список и ничего не удалять. Legacy HANDOFF очищается только через
explicit Finish.

Return point: после одного подтверждённого Begin, Outcome, Save, Show, Resume,
assert-current, Finish или Cleanup.
