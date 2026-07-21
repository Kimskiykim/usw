# Задача 3.2: Добавить оркестратор usw-run-flow

## Artifact model

- `legacy`

## Результат

`usw-run-flow` выполняет только выбранный scenario, возвращает управление после
каждого atomic action и предсказуемо останавливается на scope, authority, review,
blocker, permission или decision boundary.

## Область

- Добавить и упаковать orchestrator skill и agent metadata.
- Разрешать и валидировать выбранный scenario до запуска action.
- Определить action-executor contract со structured outcome и обязательным
  возвратом управления orchestrator после одного вызова.
- Оценивать branches и stop conditions после каждого atomic action.
- Показывать допустимые scope options и ждать при неоднозначном continuation.
- Проверять write authority до mutation.
- Координировать human review gates и запрашивать создание receipt через
  action-executor contract, не реализуя receipt write внутри orchestrator.
- Проверять sequencing, review, authority и stop behavior на stub actions;
  останавливать flow до mutation, если реальная capability недоступна.
- Применять per-run Delivery contract и отдельно проверять permission для
  external actions.
- Сообщать stop reason и одно следующее безопасное действие.

## Вне области

- Реализация внутренней логики atomic capabilities.
- Представление stub action как установленной реальной capability.
- Выбор неоднозначного scope вместо пользователя.
- Автоматическое human approval или параллельное выполнение actions.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/flow-orchestration/spec.md`

## Зависимости

- Задача 3.1.

## Критерии готовности

- Ни один action не запускается до успешной scenario validation.
- Каждый atomic action возвращает управление orchestrator.
- Stub и реальные actions используют один structured outcome contract.
- Write без authority останавливается до mutation.
- Отсутствующий executor останавливает flow до mutation и называет capability.
- Неоднозначное continuation показывает options и ждёт user choice.
- Delivery не выполняет external action без отдельного permission.
- Packaging и installation включают новый skill.

## Проверка

- Запустить: `python3 -m unittest tests.test_flow_orchestrator tests.test_install -v`
- Ожидание: sequencing, branching, authority, review, scope, Delivery permission
  и installation scenarios проходят на contract-compatible stub actions, а
  missing executor останавливается до записи.
