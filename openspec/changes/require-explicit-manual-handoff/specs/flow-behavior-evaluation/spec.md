## ADDED Requirements

### Requirement: Проверка активации не предполагает вызов skill
Сценарий SHALL принимать optional boolean `explicit_invocation` с default
`true`. При `false` prompt SHALL представлять инструкции как candidate skill,
не утверждая, что пользователь его вызвал; решение об активации SHALL зависеть
от user input и правил skill. Небулево значение MUST отклоняться как ошибка
сценария. Отсутствие поля SHALL сохранять прежнюю вводную.

#### Scenario: Проверяется отказ от активации
- **WHEN** scenario задаёт `explicit_invocation: false`
- **THEN** вводная не имитирует прямой вызов skill и не противоречит проверке
  неявного пользовательского запроса

#### Scenario: Старый сценарий не задаёт поле
- **WHEN** `explicit_invocation` отсутствует
- **THEN** prompt сохраняет прежнюю вводную с имитацией явного вызова

#### Scenario: Поле имеет неверный тип
- **WHEN** `explicit_invocation` задан строкой, числом или null
- **THEN** harness отклоняет scenario до обращения к runner
