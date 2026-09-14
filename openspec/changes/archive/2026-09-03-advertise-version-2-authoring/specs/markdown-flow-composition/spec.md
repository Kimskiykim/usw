## MODIFIED Requirements

### Requirement: Обычный Markdown является форматом по умолчанию
`usw-create-flow` SHALL создавать обычный Markdown без version или DSL, если
пользователь явно не выбрал `-s` или `--structured`. Оба selectors SHALL выбирать
один и тот же authoring style `version-2`. Для нового flow без флага выбора
стиля скилл SHALL до первого черновика кратко сообщить о доступном `version-2`,
`--structured`, `-s` и маркерах `CALL`, `GATE`, `LOOP`, `PARALLEL`, пояснив,
что это подсказки для модели, а не исполняемый язык. Сообщение MUST NOT
останавливать создание в обычном формате или требовать отдельного решения.

#### Scenario: Structured selector отсутствует
- **WHEN** пользователь создаёт flow без `-s` или `--structured`
- **THEN** сохранённый file является обычным Markdown

#### Scenario: Новый flow создаётся без флага выбора стиля
- **WHEN** обе точки входа нового flow отсутствуют и пользователь не передал
  `-s` или `--structured`
- **THEN** до первого черновика скилл сообщает о доступной нотации `version-2`
  и без ожидания ответа продолжает создание в обычном формате

#### Scenario: Structured selector передан
- **WHEN** пользователь создаёт flow с любым structured selector
- **THEN** сохранённый file использует ту же readable convention `version-2`
