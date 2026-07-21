# Задача 4.1: Завершить и упаковать persistent task refinement

## Artifact model

- `legacy`

## Результат

`usw-refine-task` полностью упакован и проверен как standalone atomic skill,
который сохраняет один decision case за ход и возвращает переиспользуемый ready
outcome.

## Область

- Завершить skill, metadata и templates session/decisions/outcome.
- Разрешать настроенный refinement root через `usw.yaml`; при отсутствующем
  optional поле использовать нормативный standalone default `usw/refinements`.
  Не использовать этот default как fallback для неизвестного provider или
  provider operation, завершившейся ошибкой.
- Сохранять accepted и superseded decisions со стабильными IDs.
- Обновлять ready outcome только из актуальных accepted decisions.
- Добавить installation и behavioral contract coverage.
- Согласовать текущую реализацию с принятой specification.

## Вне области

- Автоматическое создание change proposal после refinement.
- Изменение target code или target change artifacts во время refinement.
- Обсуждение более одного decision case за пользовательский ход.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/task-refinement/spec.md`

## Зависимости

- Задача 1.1.
- Задача 3.3.

## Критерии готовности

- Новые и resumed sessions используют configured shared refinement root.
- Один ход показывает один case и записывает только однозначный user decision.
- Superseded decisions остаются прослеживаемыми.
- Ready outcome достаточен для следующего разрешённого planning flow.
- Skill устанавливается для каждого поддерживаемого harness.

## Проверка

- Запустить: `python3 -m unittest tests.test_package_layout tests.test_install tests.test_refine_task -v`
- Ожидание: packaging, one-case behavior, persistence, supersession и ready
  outcome scenarios проходят.
