# Задача 5.1: Реализовать явный OpenSpec provider mapping и role frontier

## Результат

Проект может явно выбрать OpenSpec provider и разрешить поддерживаемые USW
artifact roles с frontier `Analysis: proposal/specs` и
`Development: design/tasks`, без silent fallback и standalone runtime dependency.

## Область

- Добавить явный OpenSpec provider selection в configuration v1.
- Получать реальные artifact paths и capabilities через OpenSpec CLI.
- Разделить Analysis и Development frontier по нативному `spec-driven` graph.
- Запрашивать artifact instructions по отдельности и не вызывать
  `openspec-propose` через role boundary.
- Различать missing required artifact, missing optional artifact и unsupported
  provider operation.
- Хранить review receipts под provider-neutral USW review root и только
  ссылаться на OpenSpec subject.
- Гарантировать, что standalone paths не вызывают OpenSpec.

## Вне области

- Сторонние template packs и arbitrary artifact maps.
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

## Критерии готовности

- OpenSpec behavior активируется только явной valid configuration.
- Analysis может завершить свой frontier при незавершённом aggregate change.
- Development создаёт design и затем ставший доступным tasks.
- Missing capabilities дают structured errors без fallback planning artifacts.
- OpenSpec-backed receipt не изменяет OpenSpec workspace.
- Standalone tests проходят без установленного OpenSpec.

## Проверка

- Запустить: `python3 -m unittest tests.test_openspec_provider tests.test_init_usw -v`
- Ожидание: explicit selection, role frontier, semantic resolution, review-root
  isolation, error distinction и standalone independence проходят.
