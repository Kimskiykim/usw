---
name: usw-find-flow
description: Find an existing runnable local or shared USW Markdown flow for one explicit intent without creating or executing anything. Use only when the user explicitly invokes usw-find-flow.
---

# Find a USW flow

Принимать одно описание намерения и искать подходящий уже существующий
runnable flow.

## Capability contract

- Input: одно явное описание намерения.
- Writes and side effects: none.
- Output: `match`, `ambiguous` или `no-match`.
- Return point: сразу после результата поиска; не создавать и не запускать
  flow и не вызывать другой skill.

## Bounded discovery

1. Найти ближайший Git root и использовать config resolution
   `usw-run-flow`: без `usw.yaml` shared root равен `usw/flows`.
2. Рассматривать только direct entrypoints в:
   - developer-local `<project>/.usw/flows`;
   - configured shared `<project>/<flows.root>`.
3. Принимать direct regular `<name>.md` и direct `<name>/FLOW.md` только с
   safe kebab-case name, real package directory и regular entrypoint.
   Не обходить package resource directories или другие каталоги и не следовать symlink.
4. Для каждого dual-layout name вызвать safe `resolve` с точным origin. Только
   его `ambiguous_flow_layout` считать подтверждённой layout ambiguity и
   использовать paths только из resolver error. Вернуть `ambiguous` с этой
   причиной и обоими entrypoint paths; не читать, не пропускать и не
   ранжировать ни одну форму.
5. Сначала сравнить имена flow с намерением. Только для правдоподобных
   кандидатов вызвать safe `resolve` из
   `../usw-run-flow/scripts/run_flow.py` с точным origin и использовать только
   возвращённый `markdown`.
6. Не искать packaged examples, внешние каталоги, интернет, другие проекты или
   пользовательские директории вне текущего проекта.

## Match

Если один flow явно лучше остальных, вернуть:

- status: `match`;
- name, `local` или `shared` origin и exact entrypoint path;
- краткое основание выбора;
- готовую команду `$usw-run-flow` с явным `--local` или `--shared`, найденным
  name и исходным намерением.

Не запускать эту команду.

## Ambiguous

Если существенно разные flows одинаково правдоподобны, вернуть:

- status: `ambiguous`;
- имена, origins, paths и краткое различие кандидатов.

Layout ambiguity одного name также возвращает status `ambiguous`, exact cause
`ambiguous_flow_layout` и оба entrypoint paths до semantic matching.

Не выбирать победителя и не запрашивать approval на запуск.

## No match

Если подходящего runnable flow нет, вернуть status `no-match`. Можно назвать
`$usw-create-flow` как отдельное следующее действие, но не вызывать его и не
готовить новый Markdown.

## Invariants

- Finder не оценивает сложность задачи и не рекомендует direct execution.
- Finder не создаёт, не адаптирует и не исполняет flow.
- Finder не читает и не изменяет HANDOFF или configuration.
- Finder не создаёт index, score, parser, registry или runtime state.
