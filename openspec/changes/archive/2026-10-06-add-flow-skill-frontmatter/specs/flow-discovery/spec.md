## MODIFIED Requirements

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
