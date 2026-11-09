## MODIFIED Requirements

### Requirement: Assessment выбирается явно и остаётся read-only
USW SHALL предоставлять
`$usw-assess-flow [--local|-l|--shared] <flow-name> [<scenario-input>]` только
по явному запросу пользователя. Он MUST NOT создавать, обновлять, исполнять или исправлять
flow, читать или изменять HANDOFF, execution state либо product files. Только
leading tokens до safe name SHALL считаться origin selectors; недопустимые
комбинации SHALL возвращать `insufficient-data`, а trailing text SHALL
оставаться opaque scenario input.

#### Scenario: У assessment нет origin selector
- **WHEN** пользователь передаёт одно safe flow name и optional scenario input
- **THEN** USW оценивает сначала local, затем shared, не исполняя flow

#### Scenario: У assessment конфликтующие selectors
- **WHEN** перед flow name одновременно указаны `--local` и `--shared`
- **THEN** USW возвращает `insufficient-data` до чтения flow

## ADDED Requirements

### Requirement: Обычная прямая просьба активирует оценку flow
Прямая просьба оценить или проверить именно flow SHALL считаться явным запросом
без обязательного имени skill или команды. Простое упоминание flow и общая
проверка кода MUST NOT активировать assessor. Неоднозначный объект SHALL
уточняться до загрузки flow; оценка MUST NOT давать разрешение на запуск или правки.

#### Scenario: Просьба обычными словами
- **WHEN** пользователь просит «оцени flow test-evidence»
- **THEN** assessor извлекает однозначное безопасное имя и выполняет read-only
  оценку по действующим правилам selector и scenario input

#### Scenario: Flow только упомянут
- **WHEN** пользователь обсуждает сроки существующего flow либо просит проверить код
- **THEN** assessor не активируется без прямой просьбы оценить именно flow

#### Scenario: Объект оценки неоднозначен
- **WHEN** пользователь просит оценить flow, а однозначное имя не дано и
  не определяется из контекста
- **THEN** агент спрашивает, какой flow требуется, до inspect или чтения entrypoint

#### Scenario: Объект уже выбран в контексте
- **WHEN** запрос «оцени этот flow» однозначно относится к ранее выбранному safe name
- **THEN** assessor использует этот объект, не требуя повторного вызова по имени skill
