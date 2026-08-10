> **Ненормативный пример.** Этот файл не запускается на месте. Скопируйте его в
> `<flows.root>/<name>.md`, адаптируйте под проект и только затем запускайте
> `$usw-run-flow <name> "<task>"`.

# Flow: chat-review

Запускает два настраиваемых ревью параллельно. Затем основной чат готовит
презентацию по контракту flow и ожидает реакции человека.

## Контракт

- Версия: `version-2`

## Вход

```markdown
Reviewer A:
  Scope: <что проверять>
  Review focus: <на что смотреть>
  Output contract: <как вернуть результат>

Reviewer B:
  Scope: <что проверять>
  Review focus: <на что смотреть>
  Output contract: <как вернуть результат>

Presentation contract:
<как объединить отчёты, добавить личную оценку и показать результат>

Human response contract:
<как ожидать и обработать реакцию человека для каждого режима:
`iterate-findings` — разбирать findings по одному и после каждого ждать ответа;
`show-proposal` — сразу показать рекомендацию основного чата;
`make-decision` — сразу запросить и зафиксировать решение человека>
```

## Режим запуска

`$usw-run-flow` читает этот Markdown целиком и выполняет описанный процесс как
текст. Маркеры ниже помогают чтению, но не создают parser, bindings или
per-action cursor. При неоднозначности основной чат запрашивает решение.

## Порядок действий

1. `parallel-reviews` — PARALLEL:
   - `review-a` — передать Reviewer A его три блока: CALL SUBAGENT `reviewer-a`.
     - Действия субагента:
       1. `run-review-a` — выполнить одно read-only ревью строго по переданным Scope, Review focus и Output contract.
   - `review-b` — передать Reviewer B его три блока: CALL SUBAGENT `reviewer-b`.
     - Действия субагента:
       1. `run-review-b` — выполнить одно read-only ревью строго по переданным Scope, Review focus и Output contract.
2. `prepare-presentation` — основному чату объединить отчёты, добавить личную оценку, показать результат и запросить режим продолжения: CALL HUMAN `owner`; GATE: выбрать `iterate-findings`, `show-proposal` или `make-decision`.
   - IF `iterate-findings`: продолжить к `handle-follow-up`.
   - ELIF `show-proposal`: продолжить к `handle-follow-up`.
   - ELIF `make-decision`: продолжить к `handle-follow-up`.
   - ELSE: запросить один из объявленных вариантов.
3. `handle-follow-up` — основному чату обработать completed outcome `prepare-presentation` по Human response contract: начать поштучное обсуждение findings, сразу показать собственную рекомендацию либо запросить и зафиксировать решение человека: CALL HUMAN `owner`.
