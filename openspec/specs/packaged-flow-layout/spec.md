# Спецификация packaged-flow-layout

## Purpose
Определяет skill-подобный каталог flow: канонический entrypoint
`<flow-root>/<name>/FLOW.md`, совместимость с flat layout `<name>.md`,
запрет двух layout для одного имени в одном origin и правила доступа к
package resources через принадлежащий resolver `flow_directory`.

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
отдельно от Markdown и input. Относительный resource, названный в packaged
`flow_markdown`, SHALL разрешаться от принадлежащего resolver каталога этого
invocation и MUST быть отклонён на границе использования, если его path
абсолютный, выходит наружу через `..`, проходит через обнаруженный symbolic link
либо не имеет filesystem type, требуемого запрошенной операцией. Тот же path,
переданный только через `user_input`, MUST NOT становиться package dependency.
Содержимое resource MUST NOT загружаться автоматически и MUST NOT давать
дополнительных полномочий. При явном использовании boundary MUST читать final
regular file через удерживаемый no-follow descriptor, возвращать immutable
content и отдельную resource identity и считать pathname метаданными только для
отчёта, которые MUST NOT открываться повторно.

#### Scenario: Packaged flow ссылается на sibling script
- **WHEN** `<name>/FLOW.md` явно ссылается на `scripts/check.py`
- **THEN** USW читает точные immutable bytes через удерживаемую package boundary
  и применяет обычные permission boundaries до их интерпретации или выполнения

#### Scenario: Resource выходит за пределы своего package
- **WHEN** packaged Markdown ссылается на `../other-flow/FLOW.md` как на package
  resource
- **THEN** USW отклоняет path resource до чтения или выполнения

#### Scenario: User input называет path внутри package
- **WHEN** `scripts/check.py` называет только user input, а не packaged
  `flow_markdown`
- **THEN** USW сохраняет его как user input и не считает package dependency

#### Scenario: Flat относительная ссылка остаётся совместимой
- **WHEN** совместимый flat flow содержит относительную ссылку на workspace,
  использовавшуюся до поддержки packaged flow
- **THEN** USW сохраняет её прежнюю интерпретацию относительно project/workspace
  вместо перепривязки к `flow_directory`
