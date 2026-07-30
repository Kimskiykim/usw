---
name: usw-create-flow
description: Создавать или обновлять именованный USW flow в Markdown без его выполнения.
---

# Создание USW flow

Создавать один понятный человеку Markdown-файл. По умолчанию не требовать
версию, DSL, постоянные action names или специальную структуру.

## Подготовка

1. Независимо разобрать selectors:
   - `--local` или `-l` выбирает `<project>/.usw/flows`;
   - `--structured` или `-s` выбирает человекочитаемый `version-2` authoring
     style.
2. Повторённый, конфликтующий или неизвестный selector отклонить.
3. Без structured selector не читать version-specific reference.
4. Со structured selector полностью прочитать только
   [references/version-2.md](references/version-2.md).
5. Выбрать один root без fallback: local либо безопасный configured
   `flows.root`.
6. Потребовать безопасное kebab-case имя и regular `<name>.md`; отклонить
   traversal, symlink и другой filesystem type.
7. При редактировании прочитать существующий flow и сохранить его выбранный
   ordinary/structured style.

## Гарантии

- Изменять только выбранный `<flow-root>/<name>.md`.
- Ordinary Markdown не требует headings или metadata.
- Structured Markdown использует маркеры только для читаемости и не обещает
  deterministic transitions, atomic parallelism, durable cursor или validation.
- Никогда не вызывать `usw-run-flow`, executor, HANDOFF или retired validator.
- Flow не может сам предоставить полномочия на внешние или destructive actions.

## Проверка и отчёт

Проверить безопасный путь, сохранение UTF-8 Markdown, понятность процесса и
отсутствие непреднамеренных изменений других файлов.

Сообщить имя, origin, путь, выбранный authoring style и обычную команду:

```text
$usw-run-flow [--local|--shared] <name> <input>
```

Не добавлять `--experimental-structured`.

## Опциональный анализ улучшений

После успешного сохранения можно отдельно предложить read-only анализ flow.
Не проводить его без согласия и не изменять flow без отдельного одобрения.
Рекомендации связывать с конкретным риском: неоднозначной веткой, отсутствующим
исходом, неограниченным повтором, опасным действием или непроверяемым
результатом. Не добавлять machine syntax ради полноты.

## Граница выполнения

Inputs: цель, имя, описание, optional local/structured selectors и config.
Output: один Markdown-flow и краткий отчёт. Return point: после сохранения и
проверки, всегда без исполнения.
