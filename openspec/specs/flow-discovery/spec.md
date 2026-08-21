# Спецификация flow-discovery

## Purpose
Не заполнено — создано при архивации change `replace-flow-router-with-finder`.
Заполнить Purpose после архивации.
## Requirements
### Requirement: Явное намерение находит существующий runnable flow
USW SHALL предоставлять `usw-find-flow` как явно вызываемую read-only capability,
которая ищет direct developer-local и настроенные shared Markdown flows для
одного переданного намерения.

#### Scenario: Один flow явно подходит лучше остальных
- **WHEN** один существующий runnable flow явно соответствует переданному
  намерению
- **THEN** finder возвращает его имя, origin, path, обоснование и команду
  `usw-run-flow` с явным origin и исходным намерением

### Requirement: Discovery использует безопасное bounded resolution
Finder MUST проверять только safe kebab-case regular entries `*.md`
непосредственно в local и shared flow roots и MUST загружать candidates через ту
же contained no-symlink boundary разрешения, что и `usw-run-flow`.

#### Scenario: Candidate является symlink
- **WHEN** entry каталога или один из компонентов его path является symbolic link
- **THEN** finder исключает или отклоняет его без чтения flow

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
