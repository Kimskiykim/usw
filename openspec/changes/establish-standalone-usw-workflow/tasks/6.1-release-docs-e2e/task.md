# Задача 6.1: Документировать и проверить workspace modes и Delivery contract

## Artifact model

- `legacy`

## Результат

Packaging, installation, документация и end-to-end tests согласованно показывают
standalone USW как default, OpenSpec как явный compatibility provider и Delivery
как per-run terminal contract без неявной внешней authority.

## Область

- Обновить README, architecture notes, commands, package manifests и installer
  skill lists.
- Документировать три role scenarios, human review receipts, owner-routed returns
  как shared transitions, локальный табличный checkpoint и per-run Delivery owner.
- Добавить clean-project, reinitialization, existing-OpenSpec, explicit-provider,
  flow-scope, artifact-authority, interrupted-session-resume, review-retry,
  Delivery-permission и local-checkpoint/shared-receipt
  end-to-end scenarios.
- Покрыть explicit legacy/v1 task boundary, стабильность product-candidate digest
  при workflow-only writes, его изменение при product writes и conditional
  internal/transition receipt fields.
- Покрыть frozen legacy allowlist, legacy human review без v1 backfill,
  invalidation receipt после planning-artifact change, workflow-only commit,
  exact manifest serialization и разделение config/runtime provider errors.
- Удалить или явно пометить superseded documentation об обязательном OpenSpec и
  четвёртом Review flow.
- Валидировать полный OpenSpec change и запустить full local test suite.

## Вне области

- Publication, push, pull request, deployment или release.
- Сторонние providers, parallel agents и постоянная project Delivery policy.
- Release-blocking статус latest OpenSpec probe.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification deltas: `../../specs/`

## Зависимости

- Задачи 1.2, 2.2, 3.3, 4.1, 5.2 и 5.3.

## Критерии готовности

- Все package layouts содержат одинаковые commands, skills, templates, flow и
  review assets.
- Документация соответствует standalone default и explicit OpenSpec opt-in.
- E2E scenarios доказывают non-destructive behavior, authority boundaries,
  resumable review и отдельные permissions внешних действий.
- Full unit suite и strict OpenSpec validation проходят.

## Проверка

- Запустить: `python3 -m unittest discover -s tests -v`
- Ожидание: полный local suite проходит без skipped standalone behavior.
- Запустить: `openspec validate establish-standalone-usw-workflow --strict`
- Ожидание: change валиден без issues.
