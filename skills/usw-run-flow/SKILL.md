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

## Root execution context

Определить effective top-level `handoff`: отсутствие поля означает `true`.

При `false` не читать, не проверять, не создавать и не изменять
`.usw/HANDOFF.md`, `.usw/handoffs/` или candidates. Создать уникальный
неперсистентный `usw-ephemeral:*` root identity только для in-memory nested
coordination.

При `true` после safe resolve вызвать `usw-manage-handoff` Begin. Missing
HANDOFF останавливает запуск с предложением `/usw-init`. Legacy HANDOFF
блокирует Begin до Finish. Любое количество independent top-level invocations
может зарегистрировать разные operation IDs; active или terminal route другой
operation не является глобальной блокировкой.

Exact Begin operation ID является root execution identity. Каждый root владеет
только своим operation document. Конкурентность означает заявление
пользователя о независимости; USW не сериализует и не разрешает пересекающиеся
product-file writes.

## Root model execution

Передать модели один immutable logical invocation:

- `flow_name`;
- `flow_origin`;
- `flow_identity`;
- полный `flow_markdown`;
- исходный `user_input`;
- отдельный root execution identity.

Следовать всему Markdown до `completed`, `failed`, `blocked`,
`decision_required`, permission boundary или явной паузы. `version-2`, `CALL`,
`GATE`, `LOOP` и `PARALLEL` являются человекочитаемыми инструкциями.
Это не machine DSL. Не создавать parser, normalized plan, bindings, cursor или JSON
checkpoint.

Если текст допускает существенно разные следующие действия, вернуть
`decision_required`. Permission boundary также отображать как
`decision_required`. Flow text и execution identity не предоставляют
полномочия: commit, push, PR, deploy, release, destructive и другие внешние
действия по-прежнему требуют обычных разрешений.

## Nested flow execution

Root executor может передать subagent внутренний nested context:

- exact root execution identity;
- effective handoff mode;
- human-readable branch label;
- child flow selector и original child input.

Обычный пользовательский input и child Markdown не создают nested mode. Каждый
child независимо проходит обычный safe resolve и получает exact immutable
Markdown/input. При enabled handoff непосредственно перед model execution
вызвать `assert-current` для exact routed recoverable parent. При disabled
handoff не инспектировать local state.

Nested child не владеет durable state и не вызывает Begin, Outcome, Save или
Finish. Он возвращает root executor:

- branch label, flow name, origin и identity;
- natural-stop status;
- factual result, checks, references, blocker и next action.

Root сохраняет raw child statuses. Permission boundary остаётся
`decision_required`; unreliable result не повторяется автоматически. Root
следует собственному Markdown для aggregation, а при materially ambiguous
handling использует `decision_required`. Только root пишет aggregate Outcome в
свой operation document.

`PARALLEL` разрешает concurrent nested flows только для явно независимых
branches. Per-child handoff, durable branch registry, status precedence,
scheduler и automatic cancellation не создаются.

## Outcome

При effective `handoff: true` до возврата пользователю записать и перечитать
Outcome exact root operation, передав ID, возвращённый Begin. Допустимые
statuses:

`paused`, `blocked`, `decision_required`, `failed`, `completed`.

Неожиданное прерывание или ошибка Outcome оставляет только эту operation
`in_progress`; не повторять root или nested mutations автоматически.
Recoverable и terminal operation сохраняется для inspect до её exact Finish.
Новый Begin создаёт другую route и ничего не заменяет.

Return point: сразу после естественной остановки root text flow и
подтверждённого exact Outcome либо после остановившей pre-execution boundary.
