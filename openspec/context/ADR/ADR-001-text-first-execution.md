---
owner: maintainer
updated: 2026-09-01
---
# ADR-001: Text-first исполнение, structured runtime снят

## Status: Accepted

## Context

Ранний structured runtime (parser, `.usw/FLOW.json`, machine-исполнение)
обещал детерминизм, но требовал compiler-цепочку и дублировал то, что модель
делает по тексту. Сложность росла быстрее пользы.

## Decision

Flow исполняются моделью как текст по одному текстовому пути. `version-2` —
читаемая авторская конвенция (`CALL`, `GATE`, `LOOP`, `PARALLEL`), не DSL.
Runtime снят: `--experimental-structured` и `.usw/FLOW.json` отклоняются до
mutation; parser сохранён в `research/structured-runtime/` и не
устанавливается.

## Consequences

Исполнение — семантика модели: сложные flow ненадёжны, поэтому существуют
сигналы сложности, design scan и `$usw-assess-flow`. Machine guarantees
недоступны by design.

## Alternatives considered

Compiler → machine flow → iterator. Отвергнуто до появления измеримой
потребности; вернуться можно только отдельным change (ненормативный roadmap
в README).

## Review date

2027-03
