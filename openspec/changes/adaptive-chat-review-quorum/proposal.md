## Why

Текущий `chat-review` требует вручную описывать каждого reviewer-а, запускает
фиксированно двух агентов и предлагает одно решение для всего набора findings.
Практический запуск показал, что flow нужен короткий profile-based input,
адаптивный review budget и явные решения по каждому finding без скрытых
зависимостей или автоматических исправлений.

## What Changes

- Разделить executor ревью и review profile: `usw-structured-review` выполняет
  одно ревью, а named profile задаёт scope, focus и output contract.
- Добавить режим `--reviewers auto|2|3`; в `auto` основной агент объясняет
  оценку impact, scope, ambiguity, evidence и integrations и выбирает два или
  три независимых reviewer-а.
- Проводить явное голосование `support`, `reject` или `abstain` по каждому
  дедуплицированному finding. При `1:1` после двух reviewer-ов запускать ровно
  одного третьего reviewer-а только для спорных findings.
- Ограничить quorum тремя reviewer-ами и принимать решение большинством
  `2/3`; отсутствие finding в первоначальном отчёте не считать голосом
  `reject`.
- Запрашивать у человека отдельное решение для каждого принятого finding и
  формировать read-only handoff с принятыми и отклонёнными findings для
  отдельного implementation flow.
- Объявлять bundled и external dependencies в flow и статически проверять, что
  каждый обязательный `CALL SKILL` в packaged examples либо bundled, либо явно
  объявлен external.
- Сохранить Markdown как человекочитаемую инструкцию: не добавлять parser,
  machine cursor, scheduler или автоматическое исправление findings.

## Capabilities

### New Capabilities

- `adaptive-review-flow`: Адаптивный выбор review budget, profile-based
  reviewers, bounded majority vote и per-finding human decision/handoff.

### Modified Capabilities

- `flow-examples`: Packaged review examples объявляют зависимости и
  демонстрируют адаптивный review contract; package tests проверяют dependency
  closure без исполнения flow.

## Impact

- Shared и packaged Markdown для `chat-review`.
- При необходимости developer-local initialized copy примера в этом
  репозитории.
- Package/flow scenario tests, проверяющие текстовый контракт и зависимости
  examples.
- `dev-test` может получить только декларацию уже существующей external
  зависимости `ponytail-review`; сам вызов и его обязательность не меняются.
- Runtime `$usw-run-flow`, handoff protocol и permission boundaries не
  меняются.
