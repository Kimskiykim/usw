# Спецификация local-custom-flows

## Purpose
Определяет безопасный выбор local/shared без изменения режима text execution.

## Requirements

### Requirement: Явный выбор origin
Система SHALL считать `--local` и `-l` равнозначными явными selectors для
developer-local flows, а `--shared` — явным selector shared origin. Разрешение
layout SHALL происходить только внутри явно выбранного origin.

#### Scenario: Создание local flow
- **WHEN** пользователь создаёт отсутствующий именованный flow с `--local`
  или `-l`
- **THEN** система записывает только `.usw/flows/<name>/FLOW.md`

#### Scenario: Запуск shared flow
- **WHEN** пользователь запускает именованный flow с `--shared`
- **THEN** система загружает единственный совместимый entrypoint
  `<flows.root>/<name>.md` или `<flows.root>/<name>/FLOW.md`

### Requirement: Неявный lookup использует local-first
Без явного selector система SHALL сначала искать в `.usw/flows`, а затем в
настроенном `flows.root`.

#### Scenario: Оба origin содержат одинаковое имя
- **WHEN** local и shared flows имеют одинаковое safe name
- **THEN** выбирается local file и возвращается его origin

### Requirement: Local и shared используют единый text path
После выбора origin USW SHALL создавать одинаковый immutable Markdown
invocation. Metadata, origin и markers `version-2` MUST NOT выбирать другой
executor. Identity SHALL включать origin, даже если names и Markdown bytes
совпадают.

#### Scenario: Одинаковый content в разных origins
- **WHEN** local и shared flows имеют одинаковые names и Markdown
- **THEN** каждый выбранный invocation получает origin-specific identity и
  одинаковую execution semantics

### Requirement: Paths local flow остаются внутри безопасного local state
Система MUST отклонять local root, package directory или entrypoint,
которые выходят за пределы local state, проходят через symbolic link либо
имеют неожиданный filesystem type. Последующее чтение обычных файлов по
инструкции flow выполняется инструментами агента с их обычными границами;
USW не добавляет для таких файлов отдельную защиту или identity.

#### Scenario: Path local flow небезопасен
- **WHEN** `.usw`, `.usw/flows`, component package или выбранный entrypoint небезопасен
- **THEN** создание или execution останавливается до чтения, записи или вызова flow

#### Scenario: Локальный packaged flow читает соседний файл
- **WHEN** безопасно разрешённый local `FLOW.md` называет файл внутри своего каталога
- **THEN** исполнитель читает его обычным инструментом при необходимости, без повторного разрешения flow через USW

### Requirement: Новое authoring использует packages, существующее сохраняет layout
Когда запрошенное safe имя flow отсутствует в выбранном origin,
`usw-create-flow` SHALL создавать `<name>/FLOW.md`. Когда уже существует ровно
один совместимый flat или packaged entrypoint, skill SHALL обновлять именно его,
не перемещая и не меняя его layout. Непосредственно перед записью он MUST
повторно проверить оба кандидатных entrypoint и components package, не следуя
symlinks, и остановиться, если target или альтернативный layout появился,
изменился либо имеет неожиданный filesystem type.

#### Scenario: Создание отсутствующего shared flow
- **WHEN** пользователь создаёт новый shared flow с именем `review`
- **THEN** система записывает `<flows.root>/review/FLOW.md`

#### Scenario: Редактирование существующего flat flow
- **WHEN** `<flows.root>/review.md` является единственным существующим
  entrypoint и пользователь обновляет `review`
- **THEN** система обновляет `review.md` и не создаёт `review/FLOW.md`

#### Scenario: Safe package directory уже содержит resources
- **WHEN** `<flows.root>/review/` является safe каталогом с resources, но без
  entrypoint, и пользователь создаёт `review`
- **THEN** система записывает только `review/FLOW.md` и сохраняет остальное
  содержимое каталога

#### Scenario: Альтернативный layout появляется перед записью
- **WHEN** authoring выбрало отсутствующий или packaged flow, а `<name>.md`
  появляется до записи entrypoint
- **THEN** authoring останавливается, не перезаписывая ни один из layout
