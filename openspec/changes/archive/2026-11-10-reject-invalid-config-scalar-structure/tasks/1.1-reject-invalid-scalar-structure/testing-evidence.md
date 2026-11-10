# Testing evidence: reject-invalid-config-scalar-structure/1.1

Writer authority: Testing only. Эти результаты относятся к предварительному
source и не подтверждают final source или выполнение всей задачи.

| Evidence ID | Contract revision | Source identity | Check | Result | Finding | Timestamp |
|---|---|---|---|---|---|---|
| T01-fresh-package-1 | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | Независимое сравнение всех 83 файлов source/installed с `t01-install.json`, повторный расчёт source и contract digest | PASS: 83/83; source и contract совпали | none | 2026-11-10T18:07:07Z |
| T01-fresh-fixture-1 | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | Запуск установленного initializer на копиях обоих переданных проектов без изменения конфигурации | BLOCKED для исходных проектов: обе копии завершились с кодом 0 и создали корневой config и HANDOFF; исходные деревья не изменены | Ошибка подготовки fixture: конфигурации переданы в `.usw/usw.yaml`, тогда как initializer читает `usw.yaml` в корне; не finding продукта. Выполнение в исходном disabled-проекте создало бы запрещённый HANDOFF. | 2026-11-10T18:08:03Z |
| T01-fresh-controls-1 | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | Отдельные копии: config в корне; N1, разрешённая замена `notes` на mapping, init и повтор; false control | PASS на копиях: `invalid_config`, полное дерево равно; четыре примера и README совпадают с шаблонами, HANDOFF создан, embedded-text отсутствует; повтор побайтно равен; false control без HANDOFF | none для проверенного поведения; отсутствие чтения state не измерено | 2026-11-10T18:08:03Z |

Raw proof: `.usw/state/autonomous-improvement/2026-11-10/t01-fresh-installed/`
от корня проекта: `package-comparison.json`, `source-manifest.bin`,
`results.json`, отдельные JSON вызовов и отсортированные snapshots с base64
сырых байтов. Ошибочное первое сопоставление шаблонов по несуществующему пути
сохранено как `package-comparison-initial-wrong-path.json`; последующая проверка
использовала фактический путь в `skills/`. Временные проекты и копии сохранены.
Непроверены обычные запрошенные действия в исходных проектах, состояние App
createdAt, final source, другие среды и отсутствие чтения handoff paths.
Исполнитель вызвал установленные инструкции init на копиях; init возвращает
отчёт вызывающему и не начинает handoff operation. Результаты и readback
представлены raw вызовами и snapshots; открытых вызовов нет.

## Уточнение назначения и итог на исправленных копиях

Root подтвердил ошибку подготовки fixture и разрешил перенести config в
корень отдельных копий, сохранив исходные проекты и bytes. Первоначальные
результаты выше сохранены как история, исходный setup не засчитывается как
отрицательный T01. Обычная задача выполнена на копиях `root-config-invalid`
и `root-config-disabled`: `T01-fresh-controls-1` и `readback-check.json`
подтверждают перенос только config с идентичными bytes, точные examples для
обоих проектов и точный HANDOFF router в первом. Findings по продукту: none
в проверенном scope. Исходные проекты не инициализировались.

Копии: `/tmp/usw-t01-fresh-controls-5q4q0wil/invalid-notes-as-provided`,
`/tmp/usw-t01-fresh-controls-5q4q0wil/handoff-disabled-as-provided`,
`/tmp/usw-t01-fresh-controls-5q4q0wil/root-config-invalid`,
`/tmp/usw-t01-fresh-controls-5q4q0wil/root-config-disabled`. Исходные fixture
— `/tmp/usw-t01-fresh-j_gwkcil/invalid-notes` и
`/tmp/usw-t01-fresh-j_gwkcil/handoff-disabled`. Все оставлены root.

## Дополнение пользовательского отчёта

| Evidence ID | Contract revision | Source identity | Check | Result | Finding | Timestamp |
|---|---|---|---|---|---|---|
| T01-fresh-user-report-1 | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | Сопоставление созданных и существовавших путей и указаний об examples со штатным skill и сохранёнными ответами | PASS: [пользовательское дополнение](../../../../../.usw/state/autonomous-improvement/2026-11-10/t01-fresh-installed/user-report-completion.md), SHA-256 `b7b301c35712c8de0a5f9a77153d748f9021cf0cd7f57c342487f1fd19f3fc5b`; существующие raw и результаты сохранены | none; завершение отчёта, не новый runtime/model test | 2026-11-10T18:24:16.840971+00:00 |

## Current independent Testing: t01-c2 / source 02154

| Evidence ID | Contract revision | Source identity | Check | Result | Finding | Timestamp |
|---|---|---|---|---|---|---|
| t01-testing-current-matrix | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | N1–N4, P1–P4, actual authoring/Handoff and supplied-root resolve | PASS: 14 negative trees, 4 positive controls; raw `.usw/state/autonomous-improvement/2026-11-10/t01-testing-current/matrix.json` | none; resolve не читает config | 2026-11-10T19:26:17.702371+00:00 |
| t01-testing-current-suites | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | 5 targeted suites, full 306, strict validate, diff/scope; package 83 | PASS; raw `.usw/state/autonomous-improvement/2026-11-10/t01-testing-current/commands.json`, `scope.json`, `package.json` | none в этих вызовах | 2026-11-10T19:26:17.702371+00:00 |
| t01-testing-current-installed | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | installed init N1/mapping/retry/disabled | PASS; raw `.usw/state/autonomous-improvement/2026-11-10/t01-testing-current/installed-init.json`, отчёт `user-report.md` там же | snapshots не измеряют чтение state | 2026-11-10T19:26:17.702371+00:00 |
| t01-testing-current-fallback-mutation | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | in-memory удаление из fallback требования block scalar и повтор package/atomic suites | 44/44 проходят при отсутствии нормы; raw `.usw/state/autonomous-improvement/2026-11-10/t01-testing-current/fallback-mutation.json` | in-scope DoD 4: отсутствует адресная regression-защита нормы block scalar/modifiers | 2026-11-10T19:26:17.702371+00:00 |

| Evidence ID | Contract revision | Source identity | Check | Result | Finding | Timestamp |
|---|---|---|---|---|---|---|
| t01-testing-current-scope-clarification | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | Пересмотр DoD 4 и результата `t01-testing-current-fallback-mutation` | Текущий fallback содержит block scalar, `|`/`>`/модификаторы и nested-scalar guard; текущий parser и реальные негативные тесты с ним согласованы | Предыдущая квалификация mutation gap как blocker отозвана: исходный DoD не требует mutation-покрытия каждого утверждения. Эксперимент сохранён как ограничение будущей защиты текста, без наблюдаемого текущего нарушения | 2026-11-10T19:26:54.317290+00:00 |
