# Flow: chat-review

Запускает адаптивное read-only ревью двумя или тремя независимыми агентами,
получает явные votes по каждому finding и передаёт человеку финальное решение.

## Контракт

- Версия: `version-2`

## Dependencies

- bundled skill: `usw-structured-review`
- bundled command: `usw-reviewer-llm-critic`

Если обязательная dependency недоступна, вернуть `decision_required` до
запуска subagents. Не подменять dependency другим skill или prompt.

## Вход

```markdown
Scope:
<что проверять; если отсутствует — все worktree changes относительно HEAD>

Review profile: llm-critic | custom

--reviewers auto|2|3

Custom profile:
  Review focus: <на что смотреть>
  Output contract: <как вернуть результат>
```

`--reviewers` — Markdown-параметр внутри пользовательского input, не selector
команды `$usw-run-flow`. Default — `auto`. Повторённый параметр, пропущенное
значение или значение вне `auto|2|3` возвращает `decision_required` до запуска
subagents.

Если Scope отсутствует или пуст, использовать все worktree changes
относительно `HEAD`.

## Review profiles

### `llm-critic`

- Scope: scope из input.
- Review focus: CALL COMMAND `/usw-reviewer-llm-critic`; прочитать полный
  prompt `commands/usw-reviewer-llm-critic.md` и применить без смягчения.
- Output contract: findings по severity; для каждого — точный файл и строка,
  defect, evidence, impact и минимальный fix. Если material findings нет,
  вернуть ровно `No material LLM slop found.`

### `custom`

Использовать scope из input и непустые `Review focus` и `Output contract` из
`Custom profile`. Если хотя бы один блок отсутствует, вернуть
`decision_required` до запуска subagents. Неизвестный profile обрабатывать так
же.

## Режим запуска

`$usw-run-flow` читает этот Markdown целиком и выполняет описанный процесс как
текст. Маркеры помогают чтению, но не создают parser, bindings, scheduler,
machine voting state или per-action cursor.

## Порядок действий

### 1. Выбрать review budget

**GATE review-budget**

Для `--reviewers 2` или `--reviewers 3` использовать указанное initial число и
сообщить `review-budget-source: explicit`.

Для `--reviewers auto` оценить:

- high-impact triggers: security/privacy, irreversible data, public API или
  schema migration, concurrency, deployment;
- uncertainty factors: multi-component scope, ambiguous requirements, weak
  или missing tests/evidence, external integrations.

Выбрать 3 при любом high-impact trigger либо минимум двух uncertainty factors;
иначе выбрать 2. До запуска reviewers показать:

```text
review-budget: 2|3
review-budget-source: auto|explicit
review-budget-reason: <triggers и factors либо low-risk reason>
```

### 2. Независимо найти candidates

**PARALLEL discovery**

Всегда запустить:

- CALL SUBAGENT `reviewer-a`;
- CALL SUBAGENT `reviewer-b`.

Если initial budget равен 3, одновременно запустить CALL SUBAGENT `reviewer-c`.
Каждому передать одинаковые resolved `Scope`, `Review focus` и
`Output contract`, не передавая результаты других reviewers. Каждый subagent
выполняет ровно одно discovery review: CALL SKILL `usw-structured-review`.

Reviewers ничего не меняют. Tool-unavailable, пустой или не соответствующий
output contract результат возвращает `decision_required`; автоматически не
повторять и не подменять reviewer-а.

### 3. Дедуплицировать candidates

Основной чат объединяет эквивалентные findings, сохраняет различия в evidence
и назначает стабильные в пределах invocation IDs `F-1`, `F-2`, ... .

Если material findings нет, показать `accept-as-is`, вернуть read-only outcome
без implementation scope и завершить flow со статусом `completed`.

Отсутствие finding в первоначальном отчёте reviewer-а не считать голосом
`reject`.

### 4. Получить явные votes

**PARALLEL voting**

Передать каждому active reviewer полный candidate ledger и для каждого ID
запросить ровно один vote:

- `support` — evidence подтверждает finding;
- `reject` — evidence опровергает finding;
- `abstain` — данных недостаточно.

Voting является отдельным read-only вызовом CALL SKILL
`usw-structured-review`. Его Scope — исходный scope и candidate ledger; Review
focus — проверить evidence каждого candidate; Output contract — `ID`, vote и
краткое evidence для каждого ID.

### 5. Разрешить votes

**GATE majority-vote**

При initial budget 2:

- два одинаковых non-abstain votes дают verdict `2/2`;
- любой другой результат, включая `1:1` или `abstain`, запускает ровно одного
  CALL SUBAGENT `reviewer-c` только для unresolved IDs. Передать ему
  voting-specific `Scope`, `Review focus` и `Output contract`:
  - Scope: исходный scope и unresolved candidate ledger;
  - Review focus: проверить evidence каждого unresolved candidate, используя
    resolved profile только как review lens;
  - Output contract: `ID`, explicit vote и краткое evidence для каждого
    unresolved ID.

`reviewer-c` выполняет одно read-only validation review через CALL SKILL
`usw-structured-review` и не возвращает discovery-format findings.

После трёх reviewers `support` либо `reject` становится majority verdict при
минимум двух одинаковых votes: `2/3` или `3/3`. Если двух одинаковых
non-abstain votes нет, вернуть `decision_required` с полным evidence и vote
provenance и запросить у owner `fix-finding` либо `reject-finding` для этих
IDs. После ответа возобновить flow сразу с `GATE finding-decisions`, не
запуская reviewer или voting повторно.

Reviewer-ов максимум три. Не запускать четвёртого reviewer-а, не повторять
discovery и не открывать voting loop.

### 6. Представить findings и получить решения

Для каждого candidate показать:

- ID и краткий finding;
- evidence;
- votes с provenance;
- majority verdict;
- личную оценку и рекомендацию основного чата.

Majority verdict является рекомендацией, не финальным решением.

**CALL HUMAN `owner`; GATE finding-decisions**

Для каждого ID принять одно решение:

- `fix-finding <ID>` — включить finding в отдельный implementation scope;
- `reject-finding <ID>` — сохранить отказ и исключить finding из scope.

Разрешить один ответ для нескольких IDs. Если решение дано не для всех IDs,
сохранить полученные решения и вернуть `decision_required` только для
оставшихся.

### 7. Вернуть review-to-fix handoff

После решения всех IDs показать:

```markdown
Accepted findings:
- <ID, evidence и bounded fix scope>

Rejected findings:
- <ID, evidence, vote provenance и human decision>

Review provenance:
- review budget, reason и votes

Recommended next action:
- <название отдельного implementation flow или none>
```

Завершить со статусом `completed`. Не менять reviewed files, не запускать
implementation flow автоматически и не расширять permission boundaries.
