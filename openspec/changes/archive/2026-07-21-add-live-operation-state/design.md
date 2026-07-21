## Context

`.usw/HANDOFF.md` уже является developer-local точкой возобновления, а
`usw-run-flow` уже задаёт порядок preflight и одного atomic skill/script step.
Для live operation state не нужен ещё один программный слой: достаточно сделать
границы begin/outcome обязательной частью Markdown-инструкций orchestrator.

Пользователь явно ограничил реализацию: не добавлять и не изменять
Python-скрипты. Поэтому design не обещает parser-level validation, filesystem
atomic replace или автоматическую миграцию legacy checkpoint.

## Goals / Non-Goals

**Goals:**

- записывать наблюдаемый `in_progress` после preflight и до executor;
- сохранять actor, executor, scope, intent, authority, result и flow cursor;
- не повторять возможно прерванную mutation автоматически;
- удерживать non-idle state до явного finish;
- сохранить один понятный Markdown entry point для resume.

**Non-Goals:**

- новый Python runtime, parser, validator или writer;
- строгая транзакционность filesystem write;
- автоматическая миграция или удаление `.usw/FLOW.json`;
- постоянный audit log, tool-call log или configurable retention.

## Decisions

### Операционный протокол принадлежит `usw-run-flow`

Перед каждым executor orchestrator выполняет:

1. Полностью проверяет flow, scope, capability и write authority.
2. Проверяет, что HANDOFF idle либо относится к тому же flow/scope.
3. Записывает current operation как `in_progress`.
4. Читает HANDOFF обратно и проверяет обязательные поля.
5. Только после этого вызывает ровно один executor.
6. Сверяет outcome с authority и обновляет HANDOFF до выбора следующего шага.

Если запись или read-back не подтверждены, executor не запускается. Это
намеренно instruction-level invariant, а не новый программный state machine.

### HANDOFF остаётся компактной summary

Шаблон хранит одну current operation и одну строку на каждый завершённый flow
step. Operation ID имеет локальную форму `op-NNN`. Details остаются в referenced
artifacts; tool calls и прочитанные файлы не журналируются.

Минимальные поля: actor, role, exact executor, scope, flow/step, intent,
declared writes, status, started/updated, result, actual areas, verification,
next action и references.

### Resume консервативен

`in_progress` без result означает возможное прерывание внутри executor. Resume
показывает summary и не повторяет mutation. References открываются только при
stale/unknown source, failed/blocked outcome или явном запросе подробностей.

### Lifecycle ручной

Любой non-idle HANDOFF блокирует другой flow/scope. Продолжение допустимо только
для того же flow/scope, а очистка — только через `/usw-handoff finish`.

### Legacy FLOW не мигрируется автоматически

Если `.usw/FLOW.json` существует, agent не читает его параллельно с active
HANDOFF и не удаляет. Он останавливается и предлагает явный finish либо ручной
перенос подтверждённых cursor facts в HANDOFF.

## Risks / Trade-offs

- [Запись не является filesystem-транзакцией] → executor запрещён до успешного read-back.
- [Агент может нарушить инструкцию] → begin/outcome порядок повторён в runner и handoff skills и проверяется сценарным review.
- [Legacy checkpoint требует ручного решения] → никакой автоматической потери или выдуманной истории.
- [Забытый completed state блокирует новую работу] → показывать одну команду `/usw-handoff finish`.

## Migration Plan

1. Обновить HANDOFF template новым summary-first форматом.
2. Обновить `usw-run-flow` порядком begin/read-back/executor/outcome.
3. Обновить `usw-manage-handoff`, команды и README для resume/finish.
4. Проверить Markdown-контракты, отсутствие Python diff и OpenSpec validation.

Rollback возвращает предыдущие Markdown-шаблоны и инструкции; runtime-код не
затрагивается.

## Open Questions

Нет.
