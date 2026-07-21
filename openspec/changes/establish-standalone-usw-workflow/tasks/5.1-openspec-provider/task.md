# Задача 5.1: Реализовать явный OpenSpec provider mapping и role frontier

## Artifact model

- `legacy`

## Результат

Проект может явно выбрать OpenSpec provider и разрешить поддерживаемые USW
artifact roles с frontier `Analysis: proposal/specs` и
`Development: design/tasks`, без silent fallback и standalone runtime dependency.

## Область

- Подключить уже разобранное задачей 1.1 значение `artifacts.provider: openspec`
  к operational OpenSpec adapter без изменения config schema.
- Добавить OpenSpec CLI adapter в общий provider interface из задачи 3.3, не
  создавая отдельный artifact или receipt mechanism.
- Получать реальные artifact paths и capabilities через OpenSpec CLI.
- Разделить Analysis и Development frontier по нативному `spec-driven` graph.
- Различать artifact status `ready` («разрешено создать») и существующий
  завершённый artifact file на каждом frontier transition.
- Запрашивать artifact instructions по отдельности и не вызывать
  `openspec-propose` через role boundary.
- Различать missing required artifact, missing optional artifact и unsupported
  provider operation.
- Хранить review receipts под provider-neutral USW review root и только
  ссылаться на OpenSpec subject через общий receipt writer задачи 3.3.
- Гарантировать, что standalone paths не вызывают OpenSpec.

## Вне области

- Сторонние template packs и arbitrary artifact maps.
- Declarative path mapping и executable provider/plugin API; v1 ограничен
  встроенными standalone и OpenSpec adapters.
- Custom OpenSpec schema с role gates.
- Изменение OpenSpec files во время discovery.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/openspec-compatibility/spec.md`
- Specification delta: `../../specs/flow-orchestration/spec.md`

## Зависимости

- Задача 1.1.
- Задача 2.1.
- Задача 3.3.

## Критерии готовности

- OpenSpec behavior активируется только явной valid configuration.
- Задача 1.1 владеет parsing/defaults/validation provider field, а 5.1 — только
  operational adapter behavior и OpenSpec artifact capabilities.
- Analysis может завершить свой frontier при незавершённом aggregate change.
- Analysis handoff фиксирует `design: ready` при отсутствующем `design.md` и
  `tasks: blocked`; Development создаёт design, повторно читает status и затем
  создаёт ставший `ready` tasks.
- Missing capabilities дают structured errors без fallback planning artifacts.
- OpenSpec-backed receipt не изменяет OpenSpec workspace.
- OpenSpec mapping расширяет общий provider interface и не дублирует standalone
  artifact или receipt implementation.
- Неизвестное config value отклоняется задачей 1.1 как `unsupported_provider`;
  валидный встроенный provider с недоступной operation получает
  `unsupported_provider_operation` до записи. Public extension contract не
  создаётся.
- Standalone tests проходят без установленного OpenSpec.

## Проверка

- Запустить: `python3 -m unittest tests.test_openspec_provider tests.test_init_usw -v`
- Ожидание: explicit selection, role frontier, semantic resolution, review-root
  isolation, error distinction и standalone independence проходят.
