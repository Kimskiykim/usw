# Задача 3.1: Определить три role scenarios и human review gates

## Artifact model

- `legacy`

## Результат

USW поставляет нормативный flow-scenario template, scenarios Analysis,
Development и Testing и validator, который отклоняет неоднозначный orchestration
contract до выполнения actions.

## Область

- Определить обязательные sections Purpose, Inputs, Ordered actions, Branches,
  Write authority, Stop conditions и Outputs.
- Добавить `flow-scenario-analysis.md`, `flow-scenario-development.md` и
  `flow-scenario-testing.md`.
- Дополнить initializer аддитивным созданием отсутствующих standard scenarios в
  configured `flows.root` без перезаписи существующих files.
- Включить internal review и receiving-role transition review как human gate
  actions, создающие reviewer receipts.
- Требовать owner role для обоих gates, sender/receiver только для transition и
  запрещать ложный self-transition internal review.
- Передавать receipt writer точные identities всех reviewed planning artifacts;
  для legacy task передавать task digest и observed verification references
  вместо отсутствующих v1 fields.
- Зафиксировать owner-routed returns, earliest-invalidated-gate rule и terminal
  Delivery boundary.
- Валидировать action references, artifact roles, branch targets и stops.
- Запрещать orchestrator скрыто использовать packaged template, если project
  scenario отсутствует.
- Добавить valid и invalid scenario fixtures.

## Вне области

- Запуск skills из scenario.
- Отдельный Review flow или automated approval machine.
- Project-specific и сторонние executable scenario extensions.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/flow-orchestration/spec.md`

## Зависимости

- Задача 1.1.
- Задача 1.2.
- Задача 2.1.

## Критерии готовности

- Все обязательные scenario sections имеют нормативную семантику.
- Ровно три initial role scenarios объявляют actions, branches, authority,
  review gates и stops.
- Internal gate не меняет responsibility; transition gate называет sender и receiver.
- Неполные или недопустимые scenarios отклоняются до запуска action.
- Scenario assets входят во все поддерживаемые package layouts.
- Clean initialization создаёт три project-owned scenarios; reinitialization
  добавляет только отсутствующие и сохраняет существующие byte-for-byte.

## Проверка

- Запустить: `python3 -m unittest tests.test_flow_scenarios tests.test_init_usw -v`
- Ожидание: три valid role scenarios проходят, а missing authority, invalid
  branch, fourth Review flow и missing stop отклоняются без execution; scenario
  seeding остаётся additive и не использует runtime fallback.
