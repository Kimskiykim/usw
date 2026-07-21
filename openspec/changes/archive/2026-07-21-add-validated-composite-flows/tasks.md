## 1. Контракт и загрузка flow

- [x] 1.1 Реализовать parser минимального Markdown-контракта с секциями `Контракт`, `Порядок действий` и `Полномочия записи`, двумя типами шагов и точными ошибками; проверить fixtures.
- [x] 1.2 Добавить рядом с role loader безопасное разрешение custom `<flows.root>/<name>.md`, отклоняющее абсолютные пути, `..`, symlink escape и отсутствующие файлы; подтвердить targeted tests.
- [x] 1.3 Представить custom flow как линейный список, использующий номер пункта вместо step ID и не принимающий branches; подтвердить parser tests.

## 2. Исполнение типизированных шагов

- [x] 2.1 Обобщить `run_next` для одного линейного step: переходить дальше только после `completed`, а остальные statuses возвращать как наблюдаемую остановку; подтвердить `tests/test_flow_orchestrator.py`.
- [x] 2.2 Подключить exact-name skill executor к общему `ActionOutcome`, включая проверку доступности и declared writes до вызова; подтвердить contract tests.
- [x] 2.3 Добавить script executor с project-relative regular-file validation, отдельными arguments, запретом shell semantics и permission boundary; подтвердить safety tests для traversal, symlink и command string.
- [x] 2.4 Проверять reported writes и output references после каждого executor и останавливать последующие steps при contract violation; подтвердить orchestrator tests.

## 3. Checkpoint и продолжение

- [x] 3.1 Добавить в developer-local checkpoint имя flow, digest нормативного Markdown, scope и индекс следующего шага без изменения shared artifacts; подтвердить round-trip tests.
- [x] 3.2 Реализовать resume только для fresh flow identity и source context, возвращая явный stale/unsupported result после изменения flow; подтвердить handoff integration tests.

## 4. Пользовательский контракт и сквозная проверка

- [x] 4.1 Обновить `usw-run-flow/SKILL.md` и README: вызов по имени, минимальный Markdown-контракт, skill/script steps, stop/resume и permission boundaries.
- [x] 4.2 Добавить end-to-end test custom flow со skill и script, проверяющий порядок, остановку, resume и неизменность существующих role flows.
- [x] 4.3 Запустить полный standalone test suite и OpenSpec validation; зафиксировать отсутствие новых runtime dependencies и shell execution paths.
