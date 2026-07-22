---
name: usw-run-flow
description: Run a task with any named shared or developer-local Markdown flow. Plain Markdown is the default; strict v1/version-2 parsing and orchestration are experimental and require explicit opt-in.
---

# Run a USW flow

Принимать два обязательных входа: задачу пользователя и безопасное kebab-case
имя flow. Формат Markdown не является частью default API.

## Selectors

- `--local` и `-l` — точные aliases, ограничивающие поиск
  `<project>/.usw/flows`.
- `--shared` ограничивает поиск настроенным `flows.root`.
- Без origin selector искать local flow первым, затем shared flow.
- `--experimental-structured` явно включает строгий v1/version-2 runtime.

Повторённые, конфликтующие или неизвестные selectors отклонять. Поле версии
внутри Markdown никогда само не включает experiment.

## Resolve

1. Найти корень проекта и прочитать shared `flows.root` из `usw.yaml`; без
   конфигурации использовать standalone default `usw/flows`.
2. Вызвать `scripts/run_flow.py resolve <project-root> <shared-root> <name>
   <task>`. Для явного origin добавить `--origin local` или `--origin shared`.
3. Принять только regular `<name>.md`; отклонить path traversal, symlink и
   другой filesystem type. Никогда не использовать packaged template как
   runtime fallback.
4. Сообщить resolved origin и identity до исполнения.

## Default Markdown execution

Default-путь не вызывает strict validator и не требует версии, DSL,
постоянных action names, input map, result bindings или normalized plan.

1. Прочитать найденный Markdown полностью и использовать исходную задачу как
   рабочий вход всего flow.
2. Прочитать `.usw/HANDOFF.md`. Незавершённая operation с той же identity не
   перезапускается автоматически; другая активная operation блокирует запуск.
3. Попросить `usw-manage-handoff` записать Begin для одной operation boundary:
   task, flow name, origin, identity и generic Markdown executor.
4. Следовать описанному в документе процессу через доступные skills, tools,
   humans и agents. Не переписывать исходный flow.
5. Если документ допускает существенно разные следующие действия, вернуть
   `decision_required`, а не угадывать.
6. Попросить `usw-manage-handoff` записать terminal Outcome и вернуть результат
   пользователю.

Вся default-работа является одной observable boundary. Markdown может содержать
несколько описанных шагов; per-action machine cursor для них не создаётся.

## Experimental structured runtime

Только с `--experimental-structured`:

1. Запустить validator с тем же flag:
   `python3 <runner> validate --experimental-structured <flow-root> <name>`;
   для local добавить `--local`/`-l` и передать project root.
2. После exact version selection прочитать применимый strict contract. Для
   `version-2` полностью прочитать
   [references/version-2.md](references/version-2.md). Не открывать его для v1.
3. Разрешить exact executors всего flow до mutation.
4. Выполнить не более одной top-level boundary, сохранить cursor/control state
   и вернуть управление.

Strict runtime поддерживает v1, typed calls, nested subagent payload, gates,
bounded loops и preflighted parallel blocks version-2. Общая задача всегда
доступна executor. Action-specific inputs и named completed results являются
необязательной experimental возможностью; отсутствие input map не блокирует
запуск.

## Safety and return

Оба режима сохраняют существующие capability contracts и permission
boundaries. Script не получает shell semantics. Commit, push, PR, deploy и
release требуют отдельного явного разрешения.

При `completed`, `failed`, `blocked`, `decision_required` или permission
boundary сначала записать Outcome, затем вернуть управление. Не продолжать
после terminal boundary и не повторять прерванную mutation автоматически.

Return point: сразу после terminal Outcome одной default operation либо одной
experimental top-level boundary.
