---
name: usw-run-flow
description: Run a task with any named shared or developer-local Markdown flow through one text-first model execution path. Use when the user explicitly says «запусти флоу», «запусти flow» or «run the flow» and names a flow, or invokes `$usw-run-flow`.
---

# Run a USW flow

## Activation

Natural-language requests such as «запусти флоу `intent-to-spec` для этого intent»
are explicit requests to invoke this skill. Extract the flow name and the
remaining text as its input, then apply the same safe resolve rules as for the
`$usw-run-flow` command. Do not start a flow when the user only discusses,
reviews or creates a flow.

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
3. Runner обязан вернуть `name`, `origin`, `identity`, `path`, абсолютный
   `flow_directory`, точный `markdown`, исходный `input` и `warnings`.
4. Использовать только возвращённый `markdown`. Не перечитывать `path` после
   вычисления identity.
5. Показать каждое warning не более одного раза за текущий invocation.

Runner принимает только один contained regular entrypoint: `<name>.md` или
`<name>/FLOW.md`. Он отклоняет traversal, любой symlink component и наличие
обеих форм в одном origin. Обе формы и package resources разрешаются одинаково
на Linux, macOS и Windows.

Доступ к файлам идёт через один общий safe-access boundary с backend по
платформе. Там, где доступен `dir_fd`, traversal остаётся
descriptor-relative: после проверки компонента к нему больше не обращаются по
имени. Там, где `dir_fd` отсутствует, включая Windows, boundary отвергает
symlink и reparse point на каждом entry и запрещает имена, пересекающие
границу каталога, но адресует entries по pathname. Это сужает, но не закрывает
окно между проверкой и использованием. Разница намеренная и раскрыта: не
описывать backends как равнозначные.

## Package resources

`flow_directory` принадлежит resolved invocation и не выводится из Markdown
или input. Брать package dependency только из `flow_markdown`, не из `user_input`.
Только для packaged `<name>/FLOW.md` непосредственно перед
использованием явно названного относительного resource вызвать
`scripts/run_flow.py resource` с arguments `<project-root> <shared-root> <name>
<flow-identity> <entrypoint-path> <relative-path> --origin <flow-origin>`.
Команда обязана повторно safe-resolve тот же origin, связать lookup с исходными
`flow_identity` и exact `path`, открыть final resource через held no-follow
descriptor и вернуть `resource_identity` и immutable `content_base64` вместе с
report-only `resource_path`. При `stale_flow_resource` остановиться. Использовать
только декодированные returned bytes и не перечитывать `resource_path`. Не
конструировать `MarkdownFlow` вручную и не сканировать соседние файлы заранее.

Absolute path, `..`, missing path, symlink component и неожиданный filesystem
type останавливают использование resource. Returned bytes не расширяют
полномочия: их чтение или запуск сохраняют обычные tool и permission boundaries.
Flat flow сохраняет project/workspace-relative семантику существующих ссылок;
не передавать его пути в package resource boundary и не ребейзить их к
`flow_directory`.

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

В Begin передать короткий one-line summary исходной задачи и bounded
expected-write paths/areas, которые фактически следуют из user scope и flow.
Если writes до исполнения неизвестны, не выдумывать их. Hints не расширяют
разрешения и не означают, что concurrent operations изолированы.

Exact Begin operation ID является root execution identity. Каждый root владеет
только своим operation document. Конкурентность означает заявление
пользователя о независимости; USW не сериализует и не разрешает пересекающиеся
product-file writes.

## Root model execution

Передать модели один immutable logical invocation:

- `flow_name`;
- `flow_origin`;
- `flow_identity`;
- абсолютный `flow_directory`;
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

`blocked` и `decision_required` различаются тем, кто способен снять остановку.
`blocked` — внешнее препятствие, которое решением человека в этом диалоге не
устраняется: недоступный сервис, отсутствующая зависимость, отсутствующие
здесь данные. `decision_required` — выбор, который человек может сделать прямо
сейчас. Если остановку снимает ответ собеседника, это `decision_required`, а
не `blocked`.

## Nested flow execution

Root executor может передать subagent внутренний nested context:

- exact root execution identity;
- effective handoff mode;
- human-readable branch label;
- child flow selector и original child input.

Обычный пользовательский input и child Markdown не создают nested mode. Каждый
child независимо проходит обычный safe resolve и получает exact immutable
Markdown, resolver-owned `flow_directory` и input. При enabled handoff непосредственно перед model execution
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

В Outcome передать observed changed paths/areas только из фактического root
result. Не выводить ownership operation из общего `git status`: concurrent
process мог изменить те же файлы.

Неожиданное прерывание или ошибка Outcome оставляет только эту operation
`in_progress`; не повторять root или nested mutations автоматически.
Recoverable и terminal operation сохраняется для inspect до её exact Finish.
Новый Begin создаёт другую route и ничего не заменяет.

Return point: сразу после естественной остановки root text flow и
подтверждённого exact Outcome либо после остановившей pre-execution boundary.
