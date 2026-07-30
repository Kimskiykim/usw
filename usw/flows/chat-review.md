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

Human decision contract:
<как зафиксировать одно финальное решение:
`accept-as-is` — принять результат без изменений;
`fix-findings` — принять findings для последующей отдельной реализации>
```

## Режим запуска

`$usw-run-flow` читает этот Markdown целиком и выполняет описанный процесс как
текст. Маркеры ниже помогают чтению, но не создают parser, bindings или
per-action cursor. При неоднозначности основной чат запрашивает решение.

## Порядок действий

1. `parallel-reviews` — PARALLEL:
   - `review-a` — передать Reviewer A его три блока: CALL SUBAGENT `reviewer-a`.
     - Действия субагента:
       1. `run-review-a` — выполнить одно ревью: CALL SKILL `usw-structured-review`.
   - `review-b` — передать Reviewer B его три блока: CALL SUBAGENT `reviewer-b`.
     - Действия субагента:
       1. `run-review-b` — выполнить одно ревью: CALL SKILL `usw-structured-review`.
2. `prepare-presentation` — основному чату объединить и дедуплицировать отчёты,
   добавить личную оценку и рекомендацию, затем показать результат.
3. `make-decision` — сразу после презентации запросить одно финальное решение:
   CALL HUMAN `owner`; GATE: выбрать `accept-as-is` или `fix-findings`.
   - IF `accept-as-is`: зафиксировать решение по Human decision contract и
     завершить flow со статусом `completed`.
   - ELIF `fix-findings`: зафиксировать findings для последующей отдельной
     реализации по Human decision contract и завершить flow со статусом
     `completed`. Этот read-only flow не исправляет код.
   - ELSE: вернуть `decision_required` и запросить только один из двух
     объявленных вариантов, не добавляя промежуточный выбор режима.
