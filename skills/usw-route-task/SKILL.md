---
name: usw-route-task
description: Assess one explicitly supplied task, preview an existing or newly authored USW Markdown flow when useful, and execute it only after approval. Use only when the user explicitly invokes usw-route-task.
---

# Route one task through a USW flow

Принимать одну исходную задачу. Этот skill является разовым opt-in: не
устанавливать режим, не изменять `usw.yaml` и не применять маршрутизацию к
следующим задачам.

## Capability contract

- Input: одна исходная задача и, при продолжении, явное решение по последнему
  preview в текущем разговоре.
- Pre-approval writes: none.
- Output: рекомендация прямого выполнения, один flow preview либо outcome
  одобренного `usw-run-flow`.
- Return point: сразу после рекомендации, preview или завершения/остановки
  делегированного run.

## Оценка задачи

Сначала определить, даёт ли отдельный flow существенную пользу. Flow полезен,
когда задача многоэтапная, рискованная, неоднозначная, требует разных проверок
или повторяемого процесса.

Если задача простая:

1. Коротко объяснить, почему отдельный flow не нужен.
2. Рекомендовать выполнить исходную задачу напрямую.
3. Остановиться. Не выполнять задачу, не искать или создавать flow и не
   читать или изменять HANDOFF.

## Bounded discovery

Если flow полезен, найти ближайший Git root и использовать тот же config
resolution, что и `usw-run-flow`: отсутствующий `usw.yaml` означает
`flows.root: usw/flows`.

Искать только среди прямых `*.md` entries:

1. developer-local `<project>/.usw/flows`;
2. configured shared `<project>/<flows.root>`;
3. packaged
   `../usw-initialize-project/templates/flows/examples`.

Не искать в интернете, других проектах или пользовательских каталогах вне
текущего проекта. Не обходить каталоги рекурсивно и не следовать symlink.
При перечислении принимать только безопасные kebab-case имена regular files.

Сначала сравнить имена flow с намерением задачи. Для правдоподобных
local/shared кандидатов использовать safe resolve из
`../usw-run-flow/scripts/run_flow.py` и только возвращённый им Markdown.
Packaged examples читать только по известным regular-file путям выше. Если
имена неоднозначны, прочитать дополнительные безопасные кандидаты; не
создавать index, score, parser или machine plan.

Классифицировать лучший результат:

- `exact` — существующий runnable local/shared flow подходит без материального
  изменения процесса;
- `adapted` — существующий flow или packaged example является полезной основой,
  но процесс нужно изменить;
- `new` — подходящей основы нет.

## Authoring decision

Для `adapted` и `new` подготовить полный ordinary Markdown flow. Не изменять
исходный flow. Выбрать новое свободное kebab-case имя.

Выбрать destination:

- `shared` для процесса, зависящего от файлов, команд, архитектуры или правил
  текущего проекта и полезного другим участникам;
- `local` для личного, экспериментального или общего процесса;
- при сомнении — `local`.

Packaged example всегда является только authoring source и никогда не
исполняется на месте.

## Approval preview

До preview ничего не записывать и не вызывать `usw-create-flow`,
`usw-run-flow` или HANDOFF.

Показать:

- classification и краткое основание;
- flow name, origin/destination и точный будущий path;
- для `adapted` — source flow и существенные изменения;
- полный Markdown в fenced block;
- один явный запрос подтвердить именно показанные content, destination и
  выполнение для исходной задачи.

Для `exact` показать точный Markdown, возвращённый safe resolver. Для
`adapted` и `new` показать точные bytes, которые будут сохранены как UTF-8
Markdown.

Если пользователь отклоняет preview, просит только правки или не даёт
однозначного согласия, ничего не записывать и не исполнять. После правок
показать новый полный preview и снова ждать. Если preview или исходная задача
утрачены из контекста, провести routing заново.

## Approved continuation

Явное подтверждение разрешает только сохранение показанного flow, если нужно,
и запуск показанного flow с исходной задачей.

Для `adapted` или `new`:

1. Передать одобренные name, destination и Markdown в `usw-create-flow`;
   использовать `--local` только для local destination.
2. После возврата authoring capability перечитать saved regular file и
   убедиться, что он совпадает с одобренным Markdown. При несовпадении
   остановиться без запуска.
3. Передать точное имя, original task и явный `--local` или `--shared` selector
   в `usw-run-flow`.

Для `exact` не вызывать authoring capability и не переписывать flow. Передать
его точное имя, original task и явный origin selector в `usw-run-flow`.

Следовать outcome и return boundary `usw-run-flow`. Preview или approval не
предоставляет полномочия на commit, push, pull request, deploy, release,
destructive или другие внешние действия; сохранять обычные permission
boundaries исходного запроса и платформы.

## Invariants

- Один invocation маршрутизирует ровно одну исходную задачу.
- До явного approval нет writes и HANDOFF begin.
- Новый или адаптированный flow всегда сохраняется до запуска.
- Existing source flow никогда не изменяется при адаптации.
- Никакой catalog candidate не исполняется без полного preview и approval.
- Skill не добавляет config, runtime state, DSL, parser или external search.
