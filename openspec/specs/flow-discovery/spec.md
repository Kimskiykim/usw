# Спецификация flow-discovery

## Purpose
Не заполнено — создано при архивации change `replace-flow-router-with-finder`.
Заполнить Purpose после архивации.

## Requirements

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

Для сопоставления finder SHALL использовать имя и `description` из frontmatter
по контракту `flow-frontmatter`. Отсутствие похожих слов в имени MUST NOT
исключать кандидата до безопасного чтения его описания. Для flow без пригодного
описания finder SHALL использовать имя и назначение из тела Markdown.
Сопоставление MUST опираться только на возвращённый загрузчиком текст; наличие
frontmatter не разрешает отдельное чтение по path или обход ресурсов пакета.
Конфликт двух раскладок MUST сохранять действующий исход `ambiguous`.

#### Scenario: Candidate является symlink
- **WHEN** flat entry, package directory, `FLOW.md` или один из компонентов их path является symbolic link
- **THEN** finder исключает или отклоняет его без чтения flow

#### Scenario: Package содержит вложенные Markdown resources
- **WHEN** direct package содержит Markdown в `references/` или другом каталоге resources
- **THEN** finder рассматривает только direct entrypoint `FLOW.md` этого package

#### Scenario: Назначение понятно только из описания
- **WHEN** имя `release-check` не похоже на запрос «проверить наличие результатов тестов», но его `description` точно описывает эту работу
- **THEN** finder рассматривает его по описанию и возвращает `match`, если остальные кандидаты не соответствуют намерению столь же хорошо

#### Scenario: Старый flow не имеет frontmatter
- **WHEN** подходящее назначение указано только в теле старого flow
- **THEN** finder учитывает этот flow без миграции и без снижения приоритета только из-за отсутствия заголовка

#### Scenario: Описание отсутствует или непригодно
- **WHEN** finder обнаруживает пустое либо некорректное описание в заголовке
- **THEN** он сопоставляет имя и назначение из тела, отмечает обнаруженную проблему и ничего не исправляет

#### Scenario: Два описания одинаково подходят
- **WHEN** два существенно разных flow одинаково соответствуют намерению по описаниям
- **THEN** finder возвращает `ambiguous` с различиями кандидатов без исполнения

### Requirement: Discovery не имеет side effects
Finder MUST NOT создавать, адаптировать или исполнять flow, вызывать HANDOFF,
изменять configuration или искать packaged examples, external catalogs либо
другие проекты.

#### Scenario: Ни один flow не подходит
- **WHEN** ни один runnable local или shared flow не соответствует намерению
- **THEN** finder возвращает `no-match` без записи state и MAY назвать
  `usw-create-flow` как отдельное следующее действие

### Requirement: Неоднозначные совпадения останавливаются явно
Finder MUST возвращать `ambiguous`, когда существенно разные, одинаково
правдоподобные candidates ведут к разным процессам, и MUST NOT выбирать или
исполнять ни один из них.

#### Scenario: Local и shared flows одинаково правдоподобны
- **WHEN** local и shared candidates существенно соответствуют намерению и ни
  один не является явно предпочтительным
- **THEN** finder возвращает оба candidates с их origins и останавливается

### Requirement: Legacy router отсутствует
USW MUST NOT поставлять или рекламировать `usw-route-task`, а установка с
принудительным обновлением SHALL удалить ранее установленные skill и command
router-а.

#### Scenario: Принудительное обновление с версии с router
- **WHEN** пользователь запускает `install.sh --force` поверх установки,
  содержащей `usw-route-task`
- **THEN** старые skill и command удаляются, а `usw-find-flow` устанавливается

### Requirement: Discovery раскрывает неоднозначность layout
Finder MUST возвращать `ambiguous` с evidence `ambiguous_flow_layout`, когда один
origin содержит оба совместимых entrypoint для safe name. Он MUST NOT читать,
пропускать или ранжировать любой из layout как runnable candidate.

#### Scenario: Каталог содержит оба layout для одного имени
- **WHEN** при составлении каталога finder обнаруживает safe `<name>.md` и
  `<name>/FLOW.md` в одном origin
- **THEN** он возвращает `ambiguous`, называя оба path entrypoint и причину
  `ambiguous_flow_layout`
