# Refinement decisions: Live operation state

## `D-001` — Использовать task-scoped summary-first operational state

- Case: `C-001`
- Status: accepted
- Decided: 2026-07-21T16:49:30+03:00
- Decision: хранить одну компактную текущую операцию и список завершённых
  операций активной задачи; подробности оставлять в существующих артефактах и
  открывать по ссылкам только при необходимости.
- Basis: пользователь принял упрощённый эскиз как достаточный для первой версии.
- Consequences: состояние фиксирует начало до mutation, завершённая операция
  переносится в журнал одной строкой, а постоянный audit-log и логирование
  tool-call не вводятся. Task-scoped записи очищаются при явном finish.
- Supersedes: None.
- Follow-up cases: `C-002`, `C-003`, `C-004`, `C-005`.

## `D-002` — Записывать begin после preflight и до executor

- Case: `C-002`
- Status: accepted
- Decided: 2026-07-21T16:50:59+03:00
- Decision: orchestrator полностью валидирует flow, scope, capability и write
  authority, затем сохраняет операцию со статусом `in_progress` и только после
  успешной записи вызывает executor.
- Basis: пользователь принял рекомендуемую границу начала операции.
- Consequences: отказ preflight не создаёт ложную активную операцию; сохранённый
  `in_progress` без outcome означает возможное прерывание внутри executor и
  требует проверки состояния перед повторным запуском. Outcome обновляется до
  выбора следующего шага.
- Supersedes: None.
- Follow-up cases: `C-003`, `C-004`, `C-005`.

## `D-003` — Использовать компактный типизированный контракт операции

- Case: `C-003`
- Status: accepted
- Decided: 2026-07-21T16:52:24+03:00
- Decision: обязательны operation ID, actor/role, точный executor, task/change
  scope, flow step, однострочный intent, declared write roles/areas, status,
  started timestamp и references. Точные planned paths необязательны; actual
  changed paths записываются после выполнения.
- Basis: пользователь принял контракт после оценки его преимуществ и стоимости.
- Consequences: preflight может проверять scope и полномочия без ложного знания
  будущих файлов; resume получает компактный индекс, а подробности читает по
  references. Цена ограничена одной локальной записью на границу операции.
- Supersedes: None.
- Follow-up cases: `C-004`, `C-005`.

## `D-004` — Использовать HANDOFF.md как единственный operational state

- Case: `C-004`
- Status: accepted
- Decided: 2026-07-21T16:53:41+03:00
- Decision: `.usw/HANDOFF.md` атомарно хранит operation journal вместе с flow
  identity, scope и next step; отдельный `.usw/FLOW.json` из модели удаляется.
- Basis: пользователь принял упрощение после Ponytail-review двух конкурирующих
  локальных state-файлов.
- Consequences: один Markdown parser/validator отвечает за begin, outcome и
  resume; `in_progress` обозначает возможное прерывание внутри executor, а
  reconciliation двух файлов и correlation между ними не требуются.
- Supersedes: None.
- Follow-up cases: `C-005`.

## `D-005` — Сохранять состояние до явного finish и блокировать перезапись

- Case: `C-005`
- Status: accepted
- Decided: 2026-07-21T16:55:48+03:00
- Decision: любое non-idle состояние сохраняется до отдельной команды
  `/usw-handoff finish`; продолжать разрешено только тот же flow и scope, а новая
  работа не может перезаписать существующий journal.
- Basis: пользователь выбрал строгую политику после сравнения с разрешённой
  перезаписью.
- Consequences: `in_progress` сначала требует проверки фактических изменений и
  не перезапускает executor автоматически; `completed` остаётся доступным для
  просмотра до ручной очистки; забытое состояние наблюдаемо блокирует новый flow
  и указывает команды resume или finish.
- Supersedes: None.
- Follow-up cases: None.
