# Задача 3.3: Согласовать и дополнить atomic capabilities

## Результат

Каждый lifecycle action обеспечен одним bounded atomic skill, а ни один atomic
skill не выбирает следующий action, не расширяет scope и не пишет чужую
artifact role.

## Область

- Согласовать initialization, handoff, brainstorming, planning, refinement и
  explanation skills со scenario-owned orchestration.
- Убрать конфликтующие implicit execution defaults из planning behavior.
- Добавить provider-aware capability для role-authorized planning artifacts и
  reviewer receipts.
- Добавить capability bounded task execution с local verification и Development
  evidence.
- Добавить capability independent verification с Testing-owned checks,
  findings и evidence.
- Объявить для каждого skill inputs, outputs, permitted writes и return point.
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

- Задача 3.1.
- Задача 3.2.

## Критерии готовности

- Existing skills имеют bounded capability и наблюдаемый return point.
- Три недостающие capability-группы доступны и упакованы.
- Только flow scenarios владеют inter-skill ordering и branches.
- Planning не выполняет default microstep и не выбирает ambiguous scope.
- Static tests обнаруживают hidden orchestration и запрещённые writes.

## Проверка

- Запустить: `python3 -m unittest tests.test_package_layout tests.test_flow_scenarios tests.test_atomic_skill_contracts -v`
- Ожидание: все packaged atomic skills удовлетворяют boundary contract, а три
  role scenarios разрешают каждую action reference.
