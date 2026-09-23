# Спецификация packaged-flow-layout

## Purpose
Определяет skill-подобный каталог flow: канонический entrypoint
`<flow-root>/<name>/FLOW.md`, совместимость с flat layout `<name>.md`,
запрет двух layout для одного имени в одном origin и чтение соседних
файлов относительно возвращённого `flow_directory`.

## Requirements

### Requirement: Packaged flow имеет один канонический entrypoint
USW SHALL распознавать `<flow-root>/<name>/FLOW.md` как packaged flow для safe
kebab-case selector `<name>` и SHALL использовать этот layout для вновь
создаваемых flows. Он SHALL продолжать распознавать совместимый flat layout
`<flow-root>/<name>.md`.

#### Scenario: Создание нового packaged flow
- **WHEN** safe имя flow отсутствует в выбранном origin и пользователь создаёт его
- **THEN** USW записывает только `<flow-root>/<name>/FLOW.md` как его entrypoint

#### Scenario: Запуск существующего flat flow
- **WHEN** для выбранных имени и origin существует только
  `<flow-root>/<name>.md`
- **THEN** USW разрешает и запускает этот flat flow без миграции

### Requirement: Одно имя имеет один layout на origin
USW MUST отклонять выбранный origin с `ambiguous_flow_layout`, когда
`<flow-root>/<name>.md` и `<flow-root>/<name>/FLOW.md` оба являются runnable
entrypoints. Он MUST NOT использовать предпочтение layout, чтобы скрыть
неоднозначность.

#### Scenario: Оба entrypoint существуют в local flows
- **WHEN** local flow root содержит оба layout для одного запрошенного имени
- **THEN** разрешение останавливается с `ambiguous_flow_layout` до shared
  fallback или model execution

### Requirement: Package resources используют contained flow directory от resolver
USW SHALL передавать точный абсолютный `flow_directory` выбранного entrypoint
отдельно от Markdown и input. Если текст выбранного packaged `FLOW.md` называет
относительный соседний файл, исполнитель SHALL понимать его относительно
`flow_directory` и читать при необходимости обычными инструментами агента.
Содержимое соседних файлов MUST NOT загружаться автоматически. USW MUST NOT
требовать отдельную команду `resource`, base64, identity ресурса или повторное
разрешение entrypoint для такого чтения. Чтение и использование файла SHALL
оставаться в обычных границах инструментов и разрешений агента; текст flow
не предоставляет полномочий на выполнение файла или внешнее действие.

Путь из одного лишь `user_input` SHALL оставаться пользовательским входом,
а не становиться ссылкой на пакетный ресурс. Для плоских flow действующая
интерпретация относительных путей от проекта/рабочего каталога сохраняется.
Безопасное разрешение и identity самого `FLOW.md` остаются отдельными от
обычного последующего чтения соседей.

#### Scenario: Packaged flow ссылается на sibling script
- **WHEN** `<name>/FLOW.md` называет `scripts/check.py` и процессу нужен его текст
- **THEN** исполнитель читает файл обычным инструментом относительно `flow_directory`; само чтение не запускает скрипт

#### Scenario: Resource выходит за пределы своего package
- **WHEN** Markdown называет `../other-flow/FLOW.md`
- **THEN** USW не вводит специальный отказ `invalid_flow_resource`; доступ решается обычным инструментом и его разрешениями

#### Scenario: User input называет path внутри package
- **WHEN** `scripts/check.py` называет только user input, а не packaged `flow_markdown`
- **THEN** USW сохраняет его как user input и не перепривязывает автоматически к `flow_directory`

#### Scenario: Flat относительная ссылка остаётся совместимой
- **WHEN** совместимый flat flow содержит относительную ссылку на workspace, использовавшуюся до поддержки packaged flow
- **THEN** USW сохраняет её прежнюю интерпретацию относительно project/workspace вместо перепривязки к `flow_directory`

#### Scenario: Соседний файл меняется после выбора entrypoint
- **WHEN** файл рядом с `FLOW.md` изменён до обычного чтения агентом
- **THEN** агент получает содержимое на момент своего чтения; identity ранее выбранного entrypoint остаётся прежней и не обещает snapshot соседнего файла
