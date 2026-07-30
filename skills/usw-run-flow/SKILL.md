---
name: usw-run-flow
description: Run a task with any named shared or developer-local Markdown flow through one text-first model execution path.
---

# Run a USW flow

Принимать безопасное kebab-case имя flow, исходный пользовательский input и
необязательный origin selector.

## Selectors

- `--local` и `-l` выбирают только `<project>/.usw/flows`.
- `--shared` выбирает только настроенный `flows.root`.
- Без selector искать local flow первым, затем shared.
- Повторённые, конфликтующие и неизвестные selectors отклонять.
- `--experimental-structured` больше не поддерживается. Остановиться до
  исполнения и предложить убрать flag, сохранив тот же flow и input.

Metadata, версия и маркеры внутри Markdown никогда не переключают execution
mode.

## Resolve

1. Найти ближайший Git root. Прочитать `usw.yaml`; без файла использовать
   `flows.root: usw/flows` и `handoff: true`.
2. Вызвать `scripts/run_flow.py resolve <project-root> <shared-root> <name>
   <input>`. Для явного origin добавить `--origin local` или `--origin shared`.
3. Runner обязан вернуть `name`, `origin`, `identity`, `path`, точный
   `markdown`, исходный `input` и `warnings`.
4. Использовать только возвращённый `markdown`. Не перечитывать `path` после
   вычисления identity.
5. Показать каждое warning не более одного раза за текущий invocation.

Runner принимает только contained regular file, отклоняет traversal и любой
symlink component. Packaged template никогда не является runtime fallback.

## Handoff boundary

Определить effective top-level `handoff`: отсутствие поля означает `true`.

При `false` не читать, не проверять, не создавать и не изменять
`.usw/HANDOFF.md`. `/usw-handoff` и `/usw-resume` должны объяснить, что
capability отключена.

При `true` вызвать `usw-manage-handoff`:

1. Missing HANDOFF останавливает запуск с предложением `/usw-init`.
2. `idle`, `failed` и `completed` разрешают записать и перечитать новый generic
   `in_progress` Begin; terminal state заменяется атомарно.
3. `in_progress`, `paused`, `blocked` и `decision_required` блокируют новую
   operation, включая тот же flow с новым input, до явного finish.
4. Legacy role-based HANDOFF доступен только для recovery read/resume/finish и
   не является Begin нового text flow.

Operation identity состоит из origin, flow identity, SHA-256 exact input и
уникального invocation token, создаваемого каждым Begin. Поэтому два
последовательных запуска с одинаковыми flow и input получают разные ID.

## Model execution

Передать модели один immutable logical invocation:

- `flow_name`;
- `flow_origin`;
- `flow_identity`;
- полный `flow_markdown`;
- исходный `user_input`.

Следовать всему Markdown до `completed`, `failed`, `blocked`,
`decision_required`, permission boundary или явной паузы. `version-2`,
`CALL`, `GATE`, `LOOP` и `PARALLEL` являются человекочитаемыми инструкциями, а
не machine DSL. Не создавать parser, normalized plan, bindings, cursor или JSON
checkpoint.

Если текст допускает существенно разные следующие действия, вернуть
`decision_required`. Permission boundary также отображать как
`decision_required`. Flow text не предоставляет полномочия: commit, push, PR,
deploy, release, destructive и другие внешние действия по-прежнему требуют
обычных разрешений.

## Outcome

При effective `handoff: true` до возврата пользователю записать и перечитать
generic Outcome всей operation, передав exact operation ID, возвращённый Begin.
Stale Outcome для другого ID отклоняется. Допустимые Outcome statuses:

`paused`, `blocked`, `decision_required`, `failed`, `completed`.

`in_progress` создаётся только Begin, а `idle` — только explicit Finish. Полный
набор наблюдаемых состояний включает оба этих статуса.

Неожиданное прерывание или ошибка записи Outcome оставляет operation
`in_progress`; не повторять mutation автоматически. Recoverable handoff
сохраняется до explicit finish. Terminal handoff сохраняется для inspect до
следующего Begin или explicit finish.

Return point: сразу после естественной остановки text flow и подтверждённого
Outcome либо сразу после остановившей pre-execution boundary.
