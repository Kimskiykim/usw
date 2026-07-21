# Задача 3.3: Согласовать и дополнить atomic capabilities

## Artifact model

- `legacy`

## Результат

Каждый lifecycle action обеспечен одним bounded atomic skill, а ни один atomic
skill не выбирает следующий action, не расширяет scope и не пишет чужую
artifact role.

## Область

- Согласовать initialization, local checkpoint, brainstorming, task decomposition, refinement и
  explanation skills со scenario-owned orchestration.
- Убрать создание task-level `plan.md`/`handoff.md` и конфликтующие implicit
  execution defaults из decomposition behavior.
- Добавить общий provider adapter interface, standalone implementation для
  role-authorized planning artifacts и provider-neutral immutable writer для
  reviewer receipts.
- Сохранить adapter interface внутренней implementation boundary v1 без
  declarative path mapping или public executable provider/plugin API.
- Возвращать structured `unsupported_provider_operation` без fallback write,
  если выбран provider, adapter которого ещё не подключён.
- Добавить capability bounded task execution с табличным session journal в
  `.usw/HANDOFF.md`, local verification и `development-evidence.md`.
- Использовать единый canonical product-candidate digest задачи 2.2 в checkpoint,
  evidence, receipts и Delivery inputs.
- Добавить capability independent verification с Testing-owned checks,
  findings и `testing-evidence.md`.
- Объявить для каждого skill inputs, outputs, permitted writes и return point.
- Реализовать единый action-executor outcome contract, определённый задачей 3.2,
  и подключить реальные capabilities к action references трёх scenarios.
- Добавить static contract tests против hidden chaining и authority violations.

## Вне области

- Изменение смыслового результата brainstorming или explanation.
- Четвёртый role flow или skill на каждый lifecycle stage.
- Выполнение product change, описанного skill.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/flow-orchestration/spec.md`
- Specification delta: `../../specs/execution-artifacts/spec.md`

## Зависимости

- Задача 2.2.
- Задача 3.1.
- Задача 3.2.

## Критерии готовности

- Existing skills имеют bounded capability и наблюдаемый return point.
- Три недостающие capability-группы доступны и упакованы.
- Artifact capability полностью работает для standalone, хранит receipts вне
  planning provider и безопасно отклоняет OpenSpec до подключения задачи 5.1.
- Provider interface не объявляет сторонний extension contract в v1.
- Реальные capabilities разрешают все action references и возвращают outcomes в
  формате orchestrator contract; stub actions не используются как production
  fallback.
- Только flow scenarios владеют inter-skill ordering и branches.
- Task decomposition не выполняет default operation и не выбирает ambiguous scope.
- Static tests обнаруживают hidden orchestration и запрещённые writes.
- Receipt writer проверяет conditional internal/transition fields по gate.
- Receipt writer проверяет reviewed artifact identities и conditional
  legacy/v1 task fields без backfill.

## Проверка

- Запустить: `python3 -m unittest tests.test_package_layout tests.test_flow_scenarios tests.test_atomic_skill_contracts -v`
- Ожидание: все packaged atomic skills удовлетворяют boundary contract, а три
  role scenarios разрешают каждую action reference реальной capability без
  production fallback на test stubs; standalone adapter работает, а
  неподдерживаемый provider не создаёт fallback artifacts.
