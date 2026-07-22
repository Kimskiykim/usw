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

Обычный `$usw-run-flow` читает этот Markdown целиком и выполняет описанный flow
без action map. Строгий parser, именованные bindings и per-action cursor
доступны только с явным `--experimental-structured` и не требуются для
default-запуска.

## Порядок действий

1. `parallel-reviews` — PARALLEL:
   - `review-a` — передать Reviewer A его три блока: CALL SUBAGENT `reviewer-a`.
     - Действия субагента:
       1. `run-review-a` — выполнить одно ревью: CALL SKILL `usw-structured-review`.
   - `review-b` — передать Reviewer B его три блока: CALL SUBAGENT `reviewer-b`.
     - Действия субагента:
       1. `run-review-b` — выполнить одно ревью: CALL SKILL `usw-structured-review`.
2. `prepare-presentation` — основному чату объединить отчёты, добавить личную оценку, показать результат и запросить режим продолжения: CALL HUMAN `owner`; GATE: выбрать `iterate-findings`, `show-proposal` или `make-decision`.
   - IF `iterate-findings`: продолжить к `handle-follow-up`.
   - ELIF `show-proposal`: продолжить к `handle-follow-up`.
   - ELIF `make-decision`: продолжить к `handle-follow-up`.
   - ELSE: запросить один из объявленных вариантов.
3. `handle-follow-up` — основному чату обработать completed outcome `prepare-presentation` по Human response contract: начать поштучное обсуждение findings, сразу показать собственную рекомендацию либо запросить и зафиксировать решение человека: CALL HUMAN `owner`.
