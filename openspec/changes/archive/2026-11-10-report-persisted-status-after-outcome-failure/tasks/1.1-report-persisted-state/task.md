# Task 1.1: Сообщать сохранённое состояние после ошибки Outcome

## Artifact model

- `v1`

## Result

После ошибки Outcome человек получает предметный результат flow, проверенный
status и сведения о сохранности контекста либо явную неопределённость текущего
state. Автоматического повтора исполненных действий нет.

## Scope

Узкие Outcome/activation/return sections `skills/usw-run-flow/SKILL.md` и
`skills/usw-manage-handoff/SKILL.md`; необходимые fault tests в
`tests/test_handoff_state.py`, stable CLI/path/structural anchors в atomic
и связанных package/scenario tests; полезные существующие F05 fixtures/scenarios
по design §3. Связанные references/commands меняются только при конкретном
противоречии. Main-spec sync, goal и согласованные backlog edits учитываются
до конечного freeze по Workflow follow-up.

## Non-scope

Backend/форматы/CLI/status enum, транзакция или repair router, новый runtime
и eval adapter, implicit invocation policy, S10, установка и независимая
приёмка. Специальные CLI/API inference, availability/model/effort benchmarks,
before/after серии и новая eval инфраструктура не требуются.
Общие существующие model-agnostic harness/suites не удалять.

## References

- Proposal: `../../proposal.md`; design: `../../design.md`.
- Delta: `../../specs/live-operation-state/spec.md`.
- Кандидат: `usw/backlog/AUD-F05.md`; evidence contract:
  `openspec/specs/execution-artifacts/spec.md`.
- Проверки: `openspec/context/06-testing-and-quality.md`; процесс:
  `openspec/context/08-process-conventions.md`.
- Явное уточнение пользователя 2026-11-10 и
  `docs/goals/usw-improvement-next.md` — основание отмены специальных
  модельных прогонов; общие 04/06/schema rules применяются с этим уточнением.

## Dependencies

Принятое planning `f05-c2` и отдельное поручение продолжить apply.
S10 закрыт в commit `742eef5cb1ebbadb6e68f6107cc4866a5fe146a5`.
Сверить actual HEAD, paused operation, незавершённый patch и product manifest;
не повторять уже выполненные изменения. Право записи принадлежит назначенному
Development. Модели ролей команды сохраняются; продукт от них не зависит.
Roots/task/evidence и planning hashes сверены по design §5. Прежний
`f05-c1` source/evidence не назначается текущим для новой revision.

## Definition of done

Три точки отказа различены на поставляемом backend: до document, после
document при продолжающемся отказе snapshot, при невозможном exact чтении.
Проверены actual bytes/status/content, counter=1 и изоляция второй операции;
exact Show не пишет snapshot и не обходит router validation.

Инструкции сохраняют предметный результат в ответе, различают прочитанные,
отсутствующие и неподтверждённые сведения, не выводят `in_progress` из ошибки.
Назначенные роли независимо прочитали и реально исполнили текстовый путь
в временном проекте; их действия/ответ сверены с состоянием и call log.
Manual invocation, `handoff: false`, root/child authority и существующие
suites сохранены. Статическое чтение и самоотчёт не заменяют actual proof;
успех конкретного случая не доказывает послушание любой LLM.

Обязательные offline checks ниже успешны на конечном source.
`development-evidence.md` принадлежит Development: immutable entry содержит
ID, `f05-c2`, актуальный `USW-SOURCE-V1`, command/check, result, timestamp
и evidence links. Testing пишет только своё evidence. При изменении
contract/source все прежние entries/receipts сохраняются как history/stale;
до нового `[x]` выполнены все обязательные проверки текущей редакции.
До `[x]` применимые операции завершены проверенным Outcome либо честно
обработанной ошибкой с actual readback/uncertainty. Свежая установленная
проверка и независимая Delivery — отдельные Workflow follow-up.

## Verification

1. В temporary project воспроизвести три fault cases design §3 на реальном
   backend с исходными/конечными snapshots document/router/candidates и
   соседнего root. Под продолжающимся snapshot write failure вызвать обычный
   Python dispatcher `show <project> <exact-id>`: content из document,
   отсутствие write attempts и неизменность state от самого чтения.
2. Обычными инструментами назначенных ролевых чатов реально исполнить
   обработку трёх случаев по поставляемому тексту. Независимая роль сверяет
   exact ID, ошибку, предметный результат и сохранённые/отсутствующие сведения;
   при read failure текущий status явно не подтверждён. Не давать алгоритм
   автора вместо инструкции skill и не запускать отдельную модель.
3. Проверить counter=1, одну попытку Outcome, отсутствие повторов эффекта,
   repair/Resume/Begin, неизменность соседней операции и manual/disabled/child
   guards. Сохранить actual calls/readback/snapshots/ответ до cleanup.
4. Выполнить `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_handoff_state.py -v`,
   применимые atomic/package tests, затем
   `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`.
   Ожидание: exit 0 и сохранные прежние guards.
5. Выполнить `openspec validate report-persisted-status-after-outcome-failure --strict`,
   `git diff --check`, offline scenario load/list и адресный поиск дублей
   неверного обещания. Общий eval harness сохраняется; inference не запускать.
6. Учесть main-spec sync, goal и согласованные backlog edits до конечного
   manifest. После смены contract/source повторить все обязательные проверки
   task и Testing на текущей редакции, без выборочного сохранения currentness.
   Raw planning hashes и anchored stable digest проверяются отдельно.

## Contract revision

- `f05-c2`
- Стабильная часть: всё до `## Milestone log`, включая эту revision.
  Milestone log не входит в contract identity.

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
| --- | --- | --- | --- | --- | --- |
| — | Создан planning contract | `f05-c1` | Не назначен: implementation не начата | Проверки запланированы, результатов исполнения нет | Proposal, design, delta |
| 1 | 2026-11-10: явное указание пользователя отменить специальные model/effort/availability прогоны | `f05-c2` | Для c2 не назначен; исходный незавершённый apply сохранён | Перепланирование, реализация pending; c1 evidence/history не переименованы в current | Design §3–5; docs/goals/usw-improvement-next.md |
