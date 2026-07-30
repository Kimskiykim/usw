# Text-first authoring convention `version-2`

Использовать только после явного `--structured` или `-s`. Это соглашение для
чтения человеком и моделью, не machine DSL.

## Форма

Создавать prose-first Markdown с целью, входом, ожидаемым результатом и порядком
работы. Добавить metadata:

```markdown
- Версия: `version-2`
```

Metadata не переключает execution mode.

Допустимые маркеры:

- `CALL` — явно назвать skill, script, flow, subagent или human;
- `GATE` — перечислить понятные варианты решения;
- `LOOP` — описать условие выхода и разумный предел;
- `PARALLEL` — отметить действительно независимую работу.

Маркеры можно писать в удобной человеку форме. Они не требуют строгих labels,
indentation, постоянных имён, bindings или normalized transitions.

## Ограничения

- Не заявлять parser или validator.
- Не обещать deterministic routing либо одинаковую интерпретацию разными моделями.
- Не обещать atomic parallelism.
- Не создавать per-action cursor или `.usw/FLOW.json`.
- Не считать текст flow источником write authority.
- При существенной неоднозначности сформулировать human decision point.

## Пример

```markdown
# Review change

- Версия: `version-2`

Проверь изменение по исходному запросу пользователя.

1. CALL два независимых read-only reviewer.
2. PARALLEL допустим, если reviewers не изменяют файлы и не зависят друг от друга.
3. GATE:
   - если есть blocking findings — вернуть `needs-work`;
   - если требуется выбор пользователя — вернуть `decision_required`;
   - иначе вернуть `accepted`.
4. LOOP исправлений здесь не выполнять: этот flow только review.
```

## Проверка

Проверить только:

- документ является читаемым UTF-8 Markdown;
- цель, вход и terminal outcomes понятны;
- loops ограничены текстом;
- parallel не заявлен для зависимых или изменяющих один state действий;
- опасные действия не представлены как уже разрешённые.

После сохранения предложить обычную `$usw-run-flow` команду без experimental
flag.
