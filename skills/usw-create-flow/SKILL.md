---
name: usw-create-flow
description: Create or revise a shared or developer-local USW custom flow as a linear version-1 sequence or a structured version-2 Markdown contract. Use when the user asks to create, compose, describe, or update a named USW flow, workflow, pipeline, or reusable sequence. Do not execute the flow or claim that the current runner supports version-2.
---

# Создание USW flow

Создавать один именованный custom flow и сохранять его обычным Markdown-файлом.
Поддерживать линейную версию `1` и структурированную creation-only версию
`version-2`. Не выполнять действия созданного flow.

## Подготовка

1. Независимо разобрать два selector:
   - `--local` или точный alias `-l` выбирает developer-local root;
   - `--structured` или точный alias `-s` выбирает `version-2`.
   Допускать их вместе в любом порядке. Повторённый selector или другой флаг
   отклонить.
2. Если нет `-s` и `--structured`, до любой записи спросить пользователя,
   создать линейную версию `1` или структурированную `version-2`. Не
   выбирать версию по описанию и не записывать flow до ответа.
3. До выбора версии не читать version-specific reference. После выбора
   прочитать полностью ровно один файл и следовать ему:
   - версия `1`: [references/version-1.md](references/version-1.md);
   - версия `version-2`: [references/version-2.md](references/version-2.md).
   Не загружать оба reference для сравнения или предварительной подготовки.
4. Выбрать ровно один root без поиска и fallback:
   - с `--local` или `-l` использовать `<project>/.usw/flows`; через `lstat`
     проверить, что существующие `.usw` и `flows` являются directories и не
     symlinks, и создать только отсутствующий каталог `flows`;
   - без local selector прочитать проектный `usw.yaml` и безопасно разрешить
     `flows.root` относительно корня проекта.
   Остановиться, если USW не инициализирован, конфигурация или root невалидны,
   выходят за проект либо проходят через symlink. Не инициализировать USW
   скрытно; предложить пользователю `/usw-init`.
5. Определить безопасное имя в kebab-case: только строчные латинские буквы,
   цифры и дефисы. Цель — `<selected-flow-root>/<name>.md`; для существующей
   цели через `lstat` потребовать regular file и отклонить symlink или другой
   тип до записи.
6. Уточнить цель, результат и действия. Если разные толкования меняют
   поведение, исполнителя, управляющие связи или внешние последствия, задать
   один необходимый вопрос до записи.
7. Разрешить каждого executor:
   - skill — точное доступное имя и прочитанный capability contract;
   - script — существующий исполняемый regular file по безопасному
     project-relative пути, без symlink, с отдельными аргументами;
   - nested flow — существующий flow, безопасно разрешённый в выбранном root;
   - human или subagent — точное имя или роль.
8. При редактировании сначала прочитать существующий flow. Не искать одно имя
   во втором root, не перезаписывать файл без явного запроса, не подменять
   отсутствующий executor похожим и не создавать отсутствующий script или
   nested flow.

## Общие гарантии

- Создать или изменить только `<selected-flow-root>/<name>.md`; в local-режиме
  также разрешено создать отсутствующий каталог `.usw/flows`.
- Commit, push, pull request, deployment и release требуют отдельного явного
  разрешения и не выводятся из описания flow.
- При ошибке исправить документ либо запросить недостающую информацию и
  повторить проверку выбранной версии.
- Не запускать runner, executor, HANDOFF или следующий skill; не вычислять
  runtime-условия и не выдавать предположение за подтверждённый факт.

## Граница выполнения

- Inputs: цель, имя, описание, выбранная версия и конфигурация проекта.
- Output: созданный flow выбранной версии и краткий отчёт из её reference.
- Return point: сразу после проверки и записи, без исполнения flow.
