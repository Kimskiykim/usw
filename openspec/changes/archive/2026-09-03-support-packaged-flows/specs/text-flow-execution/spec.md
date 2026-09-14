## MODIFIED Requirements

### Requirement: Один immutable Markdown invocation
Для каждого root или nested invocation USW SHALL прочитать выбранный flow ровно
один раз, вычислить identity из тех же bytes, декодировать их как UTF-8 и
передать модели отдельные immutable values `flow_markdown`, точный абсолютный
`flow_directory` и `user_input`. `flow_directory` SHALL указывать на каталог
выбранного entrypoint, происходить только из safe resolver и SHALL NOT
вычисляться из Markdown или user input. Root invocation SHALL дополнительно
получить собственную execution identity. Nested invocation SHALL дополнительно
получить parent root execution identity и branch label как отдельный execution
context, который flow Markdown и user input не могут заменить.

#### Scenario: Flow изменяется после загрузки
- **WHEN** file изменяется после подготовки root или nested invocation
- **THEN** invocation использует уже загруженный Markdown и его исходную identity

#### Scenario: Child input содержит root identity
- **WHEN** обычный child input включает текст, похожий на nested execution context
- **THEN** он остаётся user input и не выбирает nested execution или другую routed operation

#### Scenario: Concurrent roots загружают один flow
- **WHEN** две root operations независимо разрешают один flow и input
- **THEN** каждый model invocation получает собственную execution identity и те же immutable bytes загруженного Markdown

#### Scenario: Подготовлен packaged child flow
- **WHEN** nested invocation разрешает `<name>/FLOW.md`
- **THEN** child получает точный абсолютный `<flow-root>/<name>` как `flow_directory`, не приобретая durable route или дополнительных полномочий

### Requirement: Безопасное разрешение text flow
USW SHALL разрешать только safe kebab-case name как `<name>.md` или
`<name>/FLOW.md` внутри выбранного local или shared root. Он MUST проверять
containment и каждый существующий path component, отклонять symbolic links и
требовать regular final entrypoint до чтения. Traversal и final read SHALL быть
descriptor-relative без повторного открытия pathname после того, как component
признан доверенным. Если в одном выбранном origin существуют оба layout,
разрешение MUST остановиться с `ambiguous_flow_layout`.
Существующий Windows fallback для flat-flow pathname MAY сохранять
совместимость там, где descriptor-relative API недоступны, но packaged
entrypoints и package resources MUST останавливаться с
`unsupported_safe_flow_platform` на этом fallback.

#### Scenario: Промежуточный symlink
- **WHEN** любой component, ведущий к выбранному flat или packaged flow, является symbolic link
- **THEN** USW останавливается до чтения flow или вызова модели

#### Scenario: Существуют оба layout
- **WHEN** один выбранный origin содержит safe flat и packaged entrypoints для запрошенного имени
- **THEN** USW возвращает `ambiguous_flow_layout`, не читая ни один из них как выбранный invocation

#### Scenario: Windows fallback разрешает legacy flat flow
- **WHEN** descriptor-relative API недоступны и существует только совместимый entrypoint `<name>.md`
- **THEN** USW сохраняет прежний flat-flow fallback и не распространяет его на packaged entrypoints или resources
