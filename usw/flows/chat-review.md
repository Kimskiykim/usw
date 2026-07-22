# Flow: chat-review

Запускает два настраиваемых ревью параллельно. Затем основной чат готовит
презентацию по контракту flow и ожидает реакции человека.

## Контракт

- Версия: `version-2`

## Структурированный вход

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
<как основному чату объединить отчёты, добавить личную оценку и показать результат>

Human response contract:
<свободный ответ или конечный GATE, заданный этим flow>
```

## Ограничение runtime

Текущий runner не связывает reviewer-specific input и результаты `PARALLEL` со
следующим `CALL HUMAN`. До появления data binding этот flow не считать
end-to-end исполнимым.

## Порядок действий

1. `parallel-reviews` — PARALLEL:
   - `review-a` — передать Reviewer A его три блока: CALL SUBAGENT `reviewer-a`.
     - Действия субагента:
       1. `run-review-a` — выполнить одно ревью: CALL SKILL `usw-structured-review`.
   - `review-b` — передать Reviewer B его три блока: CALL SUBAGENT `reviewer-b`.
     - Действия субагента:
       1. `run-review-b` — выполнить одно ревью: CALL SKILL `usw-structured-review`.
2. `prepare-presentation` — основному чату объединить отчёты, добавить личную оценку, показать результат и ожидать реакции: CALL HUMAN `owner`.
