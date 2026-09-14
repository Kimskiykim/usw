## MODIFIED Requirements

### Requirement: Явное намерение находит существующий runnable flow
USW SHALL предоставлять `usw-find-flow` как явно вызываемую read-only capability,
которая ищет direct developer-local и настроенные shared flat или packaged
flows для одного переданного намерения.

#### Scenario: Один flow явно подходит лучше остальных
- **WHEN** один существующий runnable flat или packaged flow явно соответствует
  переданному намерению
- **THEN** finder возвращает его имя, origin, path entrypoint, обоснование и
  команду `usw-run-flow` с явным origin и исходным намерением

### Requirement: Discovery использует безопасное bounded resolution
Finder MUST проверять только safe kebab-case regular entries `*.md` и direct
safe kebab-case каталоги, содержащие regular `FLOW.md`, внутри local и shared
flow roots. Он MUST NOT рекурсивно обходить package directories и MUST загружать
candidates через ту же contained descriptor-relative no-symlink boundary
разрешения, что и `usw-run-flow`.

#### Scenario: Candidate является symlink
- **WHEN** flat entry, package directory, `FLOW.md` или один из компонентов их
  path является symbolic link
- **THEN** finder исключает или отклоняет его без чтения flow

#### Scenario: Package содержит вложенные Markdown resources
- **WHEN** direct package содержит Markdown в `references/` или другом каталоге
  resources
- **THEN** finder рассматривает только direct entrypoint `FLOW.md` этого package

## ADDED Requirements

### Requirement: Discovery раскрывает неоднозначность layout
Finder MUST возвращать `ambiguous` с evidence `ambiguous_flow_layout`, когда один
origin содержит оба совместимых entrypoint для safe name. Он MUST NOT читать,
пропускать или ранжировать любой из layout как runnable candidate.

#### Scenario: Каталог содержит оба layout для одного имени
- **WHEN** при составлении каталога finder обнаруживает safe `<name>.md` и
  `<name>/FLOW.md` в одном origin
- **THEN** он возвращает `ambiguous`, называя оба path entrypoint и причину
  `ambiguous_flow_layout`
