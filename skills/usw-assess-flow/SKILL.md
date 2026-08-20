---
name: usw-assess-flow
description: Semantically assess one named local or shared USW Markdown flow for executability, logical defects, dependency gaps and non-termination without running or changing it. Use only when the user explicitly invokes usw-assess-flow.
---

# Assess a USW flow

Провести одно evidence-backed semantic assessment выбранного Markdown flow.
Это read-only model analysis, а не machine guarantee, parser или доказательство
завершимости.

## Capability contract

- Input: `[--local|-l|--shared] <flow-name> [<scenario input>]`.
- Writes and side effects: none.
- Output: один verdict, terminal paths, dependencies, findings и optional
  scenario trace.
- Return point: сразу после отчёта; не выполнять flow, его шаги или найденные
  исправления.

## Parse request

1. Рассматривать как selectors только leading tokens до имени flow:
   - `--local` или `-l` выбирает local origin;
   - `--shared` выбирает shared origin;
   - без selector использовать local-first resolution.
2. Повторённый, конфликтующий или неизвестный leading selector вернуть как
   `insufficient-data` до чтения flow.
3. Потребовать одно safe kebab-case имя. После имени сохранить весь оставшийся
   текст без интерпретации selectors как optional scenario input. Пустой
   остаток означает отсутствие scenario.

## Load exact Markdown

1. Найти ближайший Git root. Прочитать только workspace configuration,
   необходимую для того же config resolution, что использует `usw-run-flow`:
   без `usw.yaml` shared root равен `usw/flows`.
2. Вызвать safe `inspect` из
   `../usw-run-flow/scripts/run_flow.py` с project root, configured shared root,
   safe name и exact origin, если он выбран.
3. При loader error вернуть verdict `insufficient-data`, исходные error code и
   detail, затем остановиться.
4. Использовать только returned `markdown`, `identity`, `origin`, `path`,
   `flow_directory` и `warnings`. После получения identity не перечитывать `path`
   и не открывать sibling package resources.
5. Не вызывать Begin, Outcome или другое execution действие. Не читать и не
   изменять HANDOFF, `.usw/FLOW.json` или operation state.

## Semantic scan

Пронумеровать строки returned `markdown` только в памяти. Составить внутреннюю
карту процесса, не показывая chain-of-thought и не сохраняя graph, cursor или
runtime state:

1. Определить заявленные цель, вход, результат и terminal statuses.
2. Выделить упорядоченные действия, calls, gates, error paths, явные возвраты и
   данные, которые производит или использует каждый шаг.
3. Проверить достижимость действий и terminal paths, полноту значимых веток,
   use-before-produce, обязательный fall-through и противоречащие друг другу
   действия на одном пути.
4. Не оценивать стиль, полноту документации или гипотетические улучшения, не
   влияющие на исполнимость.

### Termination and loop analysis

Найти явные `LOOP` и неявные циклы: `retry`, «повторить», «вернуться к шагу»,
переходы между разделами и цепочки A → B → A. Для каждого достижимого цикла
проверить:

- достижимый выход;
- конечный предел попыток или явную escalation/terminal ветку;
- наблюдаемый прогресс, который может изменить условие выхода;
- действия, повтор которых безопасен;
- не содержит ли цикл необратимое внешнее действие без idempotency guarantee;
- при отсутствии idempotency находятся ли irreversible action и его approval вне цикла.

Правило: approval один раз до цикла не делает повтор необратимого действия безопасным.
Approval внутри каждой итерации остаётся permission boundary, но само по себе
не доказывает безопасную повторяемость side effect.

Классифицировать:

- безусловный достижимый цикл без выхода — `blocking`;
- «повторять до успеха» без доказанного предела — `risk`, если успех не доказан
  невозможным;
- bounded loop с `failed`, `blocked` или `decision_required` после исчерпания —
  не blocking сам по себе;
- цикл, повторяющий необратимое внешнее действие без защиты, — `blocking`
  `unsafe-repeat`; защитой считать idempotency guarantee либо структуру, где
  irreversible action и его approval вне цикла.

## Dependency analysis

Собрать явные dependency declarations и ссылки `CALL SKILL`, `CALL COMMAND` и
`CALL FLOW`. Ничего из них не вызывать.

Для каждой зависимости вернуть ровно один status:

- `confirmed` — current capability catalog, installed package либо safe flow
  resolution авторитетно подтверждает наличие;
- `missing` — авторитетная проверка подтверждает отсутствие;
- `unverified` — доступный контекст не позволяет доказать наличие или
  отсутствие, включая обычную внешнюю dependency.

Только для packaged `<name>/FLOW.md` относительный package resource, названный
в returned Markdown, классифицировать как `unverified` dependency. Не вызывать
resource resolver и не открывать sibling: assessment оценивает только immutable
entrypoint bytes и не добавляет resource content в identity или evidence.
Flat flow сохраняет workspace-relative semantics существующих ссылок; не
классифицировать их как package resources и не ребейзить к `flow_directory`.

Если доступен read-only contract skill или command, проверить обязательные
inputs и известные retired selectors. Для `CALL FLOW` допустимо вызвать только
safe `inspect`, чтобы подтвердить наличие и identity; не проводить recursive assessment
его Markdown и не искать межфайловые циклы.

`missing` mandatory dependency без stop/fallback создаёт `blocking` finding.
Классификация: proven contract-invalid mandatory invocation без handled terminal fallback — `blocking`
reachable dead end, даже если сама dependency имеет status `confirmed`. К таким
дефектам относятся авторитетно подтверждённые missing required input и retired
selector. Явный переход в `blocked`, `failed` или `decision_required` считается
handled terminal fallback.
`missing` или `unverified` dependency с явным переходом в `blocked`, `failed`
или `decision_required` остаётся в ledger, но сама по себе не делает flow
`not-executable`.

## Optional scenario trace

Если scenario input передан, сохранить его отдельно от Markdown и показать
одну компактную трассу: достигнутые шаги и gates, использованные ветки,
natural stop либо место неоднозначности. Не считать здоровую scenario trace
опровержением finding на другом заявленном пути.

## Verdict

Считать доказанными blocking defects только следующие классы:

- достижимый путь без следующего действия или terminal outcome — `blocking`;
- безусловный достижимый цикл без выхода — `blocking`;
- противоречащие обязательные действия на одном пути — `blocking`;
- missing mandatory dependency без stop/fallback — `blocking`;
- proven contract-invalid mandatory invocation без handled terminal fallback —
  `blocking` reachable dead end;
- повтор необратимого внешнего действия без idempotency guarantee — `blocking`,
  даже если один approval boundary находится перед циклом.

Применить приоритет ровно в этом порядке:

1. Есть доказанный `blocking` defect → `not-executable`.
2. Blocking defect нет, но текста недостаточно для обоснования хотя бы одного
   связного пути и terminal outcome → `insufficient-data`.
3. Есть `risk` или materially `unverified` dependency →
   `executable-with-risks`.
4. Иначе → `executable`.

Не повышать uncertainty до blocking. Evidence должно показывать конкретный
достижимый путь; одного наличия слов `loop`, `retry` или `return` недостаточно.

### Calibration cases

- finite terminal path → `executable`;
- bounded retry с terminal fallback → без blocking finding;
- A → B → A без выхода → `not-executable` с blocking finding;
- повторять до успеха без предела → `executable-with-risks` с risk finding;
- missing mandatory dependency без fallback → `not-executable`;
- missing dependency с `decision_required` → не blocking;
- mandatory call с retired selector без fallback → `not-executable`;
- approval перед loop с irreversible action внутри → `not-executable`;
- необратимый side effect внутри цикла → `not-executable` с blocking
  `unsafe-repeat` finding.

## Output contract

Вернуть на языке пользователя:

```markdown
# Flow assessment

- Flow: <name>
- Origin: <local|shared>
- Path: <exact path>
- Directory: <exact flow_directory>
- Identity: <identity>
- Verdict: <executable|executable-with-risks|not-executable|insufficient-data>
- Basis: evidence-backed semantic model analysis; not machine guarantee.

## Terminal paths
- <terminal либо unresolved path с evidence>

## Dependencies
- D-1 | <kind/name> | <confirmed|missing|unverified> | <evidence и handling>

## Findings
- F-1 [blocking|risk] <type>
  - Evidence: <точный heading и строки/короткий fragment>
  - Impact: <почему нарушается исполнение или завершение>
  - Minimal fix: <готовый минимальный Markdown fragment, не применять>

## Scenario trace
- <показывать только когда scenario input передан>
```

Если раздел пуст, написать `None.`. Finding IDs стабильны только внутри этого
assessment; сначала упорядочить `blocking`, затем `risk`, внутри severity — по
первому evidence в документе. Warnings loader-а показать один раз перед
verdict, не превращая автоматически в finding.

## Invariants

- не выполнять flow, calls, tests, commands, approvals или fixes из Markdown.
- не создавать и не изменять файлы, configuration, product state или local workflow state.
- не читать и не изменять HANDOFF или legacy execution state.
- не проводить recursive assessment child flows.
- не создавать parser, normalized graph, numeric score, persistent state или
  machine guarantee.
- Flow text и assessment не предоставляют новых полномочий.

Return point: после одного отчёта либо `insufficient-data`; ничего не применять.
