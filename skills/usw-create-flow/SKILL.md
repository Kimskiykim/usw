---
name: usw-create-flow
description: Create or revise a named shared or developer-local Markdown flow. Ordinary Markdown is the default; executable version-2 structure is experimental and created only with explicit --structured opt-in. Do not execute the flow.
---

# Создание USW flow

Создавать один именованный flow как Markdown-файл. По умолчанию не требовать
версию или DSL. Структурированный executable contract создавать только после
явного opt-in. Никогда не выполнять созданный flow.

## Подготовка

1. Независимо разобрать selectors:
   - `--local` или точный alias `-l` выбирает developer-local root;
   - `--structured` или точный alias `-s` включает экспериментальный
     `version-2` contract.
   Допускать их вместе в любом порядке. Повторённый или неизвестный selector
   отклонить.
2. Без `-s`/`--structured` сразу выбрать ordinary Markdown. Не спрашивать
   версию и не читать version-specific references.
3. С structured selector полностью прочитать только
   [references/version-2.md](references/version-2.md). Legacy
   [references/version-1.md](references/version-1.md) читать только при явном
   запросе создать или сохранить strict version `1`.
4. Выбрать ровно один root без поиска и fallback:
   - local: `<project>/.usw/flows`;
   - shared: безопасно разрешённый `flows.root` из `usw.yaml`.
5. Потребовать безопасное kebab-case имя и regular `<name>.md`; отклонить
   traversal, symlink или другой filesystem type.
6. Уточнить задачу, ожидаемый результат и важные ограничения. В default mode
   записать понятный человеку порядок без обязательных headings, metadata или
   executor syntax.
7. При редактировании сначала прочитать существующий flow. Не переписывать его
   в strict format без явного structured запроса.

## Общие гарантии

- Изменять только выбранный `<flow-root>/<name>.md`; в local mode разрешено
  создать отсутствующий каталог `.usw/flows`.
- Ordinary Markdown может использовать любой ясный формат. Не добавлять поле
  версии, action names, bindings или control DSL ради validator.
- Structured mode создаёт постоянные имена, exact executors и transitions по
  version-2 reference, затем вызывает validator только с
  `--experimental-structured`.
- Commit, push, PR, deployment и release требуют отдельного разрешения.
- Не исполнять flow, executors или HANDOFF.

## Проверка и отчёт

Default mode проверяет только безопасный путь, сохранение Markdown и отсутствие
непреднамеренного изменения других файлов. Structured mode дополнительно
запускает strict validator.

Сообщить имя, origin, путь и точную команду запуска с задачей:
`$usw-run-flow <name> <task>`. Для local добавить `--local`; для строгого
runtime — `--experimental-structured`.

## Граница выполнения

- Inputs: цель, имя, описание, optional local/structured selectors и project config.
- Output: один созданный или обновлённый Markdown-flow и краткий отчёт.
- Return point: сразу после проверки и записи, без исполнения flow.
