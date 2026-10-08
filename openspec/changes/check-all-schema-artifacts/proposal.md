# Proposal

## Why

`opsx-intent2spec` запрашивает устаревший `change.md` и проверяет только три
заранее названных файла. Это пропускает delta specs и компоненты других схем.

## What Changes

- Состав, пути, зависимости и инструкции компонентов берутся из OpenSpec CLI.
- Все компоненты выбранной схемы включаются в структурную проверку, intent
  drift и feasibility; имя схемы не ограничивает поддержку.
- Разбиение задач применяется по назначению компонента из инструкций схемы.
- Пропущенные и условные компоненты имеют явное основание; ошибка CLI или
  неполное чтение не превращаются в успешный результат.

## Scope

Общий flow `usw/flows/opsx-intent2spec.md`, его контракт и адресные проверки.

## Non-goals

Изменение OpenSpec CLI, создание runtime parser, запуск реализации change,
переделка пользовательских гейтов и исправление других пунктов аудита.

## Capabilities

### New Capabilities

- `intent-to-spec-planning`: согласование intent с полным набором компонентов
  OpenSpec change независимо от выбранной схемы.

### Modified Capabilities

Нет. `intent-clarification` описывает другой flow, который не начинает planning.

## Impact

Markdown flow, stable-token тесты, локальные behavior scenarios и AUD-F02.
Новых runtime dependencies нет; OpenSpec CLI остаётся внешней зависимостью.
