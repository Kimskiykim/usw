# Design

## Context

Мотивация — proposal.md. Find/assess выполняются моделью поверх существующих
resolve/inspect; runtime не разбирает естественный язык. Native metadata
сейчас запрещает выбор обоих skills без прямого указания их имени.

## Goals / Non-Goals

Согласовать описания, начальную границу активации и metadata с явным намерением
человека. Не расширять права read-only skills, не менять selector parsing,
loader и handoff policy.

## Decisions

- Native `allow_implicit_invocation: true` разрешает хосту выбрать candidate
  по обычному запросу. Это не разрешение действовать по простому упоминанию:
  начальный раздел SKILL.md проверяет прямую просьбу до чтения конфигурации.
- Для assess извлекать safe name, явно выбранный origin и отдельно заданный
  сценарий из запроса/контекста, затем применять прежний контракт аргументов.
  Не превращать всё предложение в flow name или scenario input.
- Неясный объект уточнять до чтения каталога/flow. Уже однозначный объект
  из контекста повторно не спрашивать.
- README содержит общую матрицу native selection и границ полномочий всех
  шести skills. У create/run/init/handoff metadata не меняется.

## Risks / Trade-offs

- Хост может предложить candidate при простом упоминании → явный guard и
  отрицательные activation scenarios через `explicit_invocation: false`.
- Prompt acceptance не доказывает native selection → отдельно фиксировать
  эту границу и не объявлять host behavior проверенным.
- Вызов finder/assessor может превратиться в запуск → положительные сценарии
  проверяют read-only результат, отсутствие записей и Begin/Outcome.
