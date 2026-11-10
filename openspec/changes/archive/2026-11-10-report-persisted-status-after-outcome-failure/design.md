# Design

## Context

Мотивация и границы — [proposal.md](proposal.md). Источник AUD-F05 и
`live-operation-state` расходятся с фактическим порядком записи. В
`skills/usw-manage-handoff/scripts/handoff_state.py` функция `outcome_handoff`
сначала проверяет данные, затем вызывает `_write_operation_at`, затем
`_write_readable_router_locked`. Ошибка последнего шага не отменяет первый.
`read_handoff` с exact identity проверяет router/route и читает документ;
CLI `show` без identity сначала вызывает discovery, который может обновлять
snapshot. Существующий backend достаточен для требуемого результата.

Read-only анализ не заменяет будущую регрессию: до записи возможен прежний
`paused`, после записи возможен `completed` при старом `paused` в snapshot.
Невалидный или недоступный router препятствует и exact чтению. Подтверждение
этих случаев критиком передано оркестратором. Developer сообщил о локальных
58/58 проверках прежнего незавершённого apply; этот переданный результат не
является новым прогоном planner или current evidence для `f05-c2`.

Инварианты: root владеет Outcome, child не получает durable route; flow text
не даёт полномочий. См. `openspec/context/03-architecture.md` и
`openspec/context/ADR/ADR-001-text-first-execution.md`. Нормативный дом изменения
— delta `specs/live-operation-state/spec.md`.

## Goals / Non-Goals

**Goals:** один ограниченный путь возврата после ошибки: exact чтение и честный
отчёт с предметным результатом и сохранёнными/неподтверждёнными сведениями.

**Non-Goals:** менять порядок записи, делать его общей транзакцией, восстанавливать
router, читать state-файл напрямую вместо валидации route или выбирать другую
операцию через discovery. Список статусов и публичный CLI не расширяются.

## Decisions

### 1. Использовать exact Show, сохранить backend

После ошибки Outcome root один раз вызывает существующую команду:

```text
python3 <handoff-script> show <project> <begin-operation-id>
```

Это служебное чтение своей операции внутри уже разрешённого flow. Вызовы без
ID, Resume, новый Begin, Save, Finish и повторный Outcome для исправления ошибки
автоматически не выполняются. Чтение через сгенерированный pathname в обход
router не допускается. Если ошибка доступа сохраняется, исполнитель возвращает
результат и неопределённость, не зацикливаясь на восстановлении.

Альтернативы: выводить `in_progress` из exit code неверно; доверять snapshot
недостаточно; транзакция document/router расширяет задачу и не нужна для
достоверного ответа. Изменения backend не запланированы. Неожиданное отличие
воспроизведения от описанного backend возвращается аналитику с evidence.

### 2. Согласовать две инструкции и точку возврата

В `usw-run-flow/SKILL.md` заменить неверное обещание и уточнить начало/конец
раздела Outcome: успешная запись с readback либо обработанная ошибка с exact
проверкой/явной неопределённостью завершают текущий возврат к человеку.
Сохранить разделение предметного исхода и статуса операции. После ошибки
сопоставлять прочитанные Done/Checks/References и другие существенные сведения
с намеренным отчётом; сообщать найденное и отсутствующее. Если чтение не удалось,
не называть новые сведения ни сохранёнными, ни утраченными без подтверждения.
Прежний известный статус допускается только как исторический факт.

В `usw-manage-handoff/SKILL.md` расширить перечень служебных оснований ровно
на exact Show после ошибки Outcome и дать короткую инструкцию в разделе Outcome.
Общий ручной Show/Resume по-прежнему требует прямого вызова человека. При
`handoff: false` не проверять даже наличие или тип handoff state. Не менять
`agents/openai.yaml` и `allow_implicit_invocation: false`.

Адресный поиск в run/manage, `references/state-model.md`,
`references/execution-model.md`, handoff/resume commands и связанных specs
выявил прямое неверное обещание в run skill и requirement Recoverable state.
`commands/usw-resume.md` описывает условный случай уже прочитанного `in_progress`,
а state-model корректно описывает document-before-snapshot. Эти тексты не нужно
переписывать ради одинакового wording; исправлять только реальный дубль или
противоречие, обнаруженное при итоговом просмотре.

### 3. Проверка состояния и текстового протокола

| Случай | Backend proof | Работа обычного ролевого чата |
| --- | --- | --- |
| Ошибка до document | Прежние `paused` и state bytes; exact Show возвращает старый контекст | Сообщить прочитанный `paused`, ошибку и отсутствующие новые сведения; предметный результат оставить в ответе |
| Ошибка router после document | Document содержит `completed` и новые сведения, snapshot прежний; отказ записи сохраняется при exact Show | Прочитать свой exact ID, сообщить сохранённый результат и отдельно ошибку router |
| Exact чтение недоступно | Невалидный/недоступный router либо несовпадение route даёт ошибку без обхода валидации | Сохранить предметный результат в ответе, явно назвать текущий status и сохранность новых сведений неподтверждёнными |
| Изоляция | Document/candidate соседней операции и membership неизменны | Работать только с ID своего Begin; не выбирать соседнюю операцию |
| `handoff: false` | Прежние guards запрещают state reads/writes | Не проверять даже наличие handoff state |
| Manual activation / child | Прежние identity/status/structure anchors и parent checks сохранены | Общие просьбы не активируют handoff; child не получает право root transitions |

В `tests/test_handoff_state.py` использовать временный проект и адресную
инъекцию отказа существующих write/read функций поставляемого backend.
Проверять реальные bytes document/router/candidates, поля и возвращённый
content, а не только ошибку. Для второго случая вызвать штатный Python
dispatcher `show <project> <exact-id>` под продолжающимся snapshot write failure:
exact Show не пытается писать snapshot и не меняет state. Вызов без ID
не заменяет этот proof. Другой root остаётся зарегистрированным и неизменным.

Уже исполненный предметный эффект моделируется локальным проверяемым действием:
counter до обработки ошибки равен единице и после неё также равен единице.
Call log/обычные tool outputs подтверждают одну попытку Outcome и exact Show,
отсутствие повторного эффекта, Outcome, автоматических repair/Resume/Begin.
Сохранить до очистки fixture начальные/конечные snapshots, counter, вызовы,
readback и фактический ответ агента в обычном evidence задачи. Самоотчёт
или marker в ответе не заменяет эти наблюдения; отдельный runner/export
protocol для этого не нужен.

Независимая назначенная роль читает поставляемые инструкции и реально
исполняет обработку трёх случаев в временном проекте обычными инструментами
своего чата. Проверяет соответствие ответа прочитанному состоянию, сохранение
предметного результата, границы чтения и отсутствие повторов. Авторы не
подсказывают внутренний алгоритм вместо текста skill. Исполнение обычного
ролевого чата — проверка текстового протокола, без отдельного запуска модели
через API или inference CLI и без серий before/after.

Stable-token проверки в `tests/test_atomic_skill_contracts.py` и соседних
package/scenario tests фиксируют CLI/path/structure anchors. Не закреплять
предложения или `in_progress` как следствие ошибки. Полный unittest и прежние
manual/disabled/identity/nested guards сохраняются.

Три уже подготовленных случая `outcome-error-before-document`,
`outcome-error-after-document`, `outcome-error-unreadable-state` и
`evals/fixtures/f05_fault_fixture.py` можно сохранить как данные сценариев
и локальную инъекцию отказа вокруг скопированного неизменённого backend.
Developer проверяет их пользу для описанного воспроизведения и минимально
убирает обязательную привязку к специальному runner в notes/instructions.
Это не требует новых adapters, копирования продуктового backend в поставку
или изменения общего `evals/run_evals.py`. Существующие harness/suites
сохраняются; их offline load/list допустим без inference. Новых платных
прогонов или инфраструктуры этот change не требует.

### 4. Основание смены проверки и история

2026-11-10 пользователь явно отменил модельные CLI/API прогоны и проверку
model/effort/availability как условия готовности: USW задаёт переносимый
текстовый протокол. Принятые модели ролевых чатов остаются организацией
команды, не зависимостью продукта. Это основание revision `f05-c2`,
а не успешный результат прежних запусков.

Предписание платных behavior evals из общих 04/06 context и schema rules
для этой задачи уточнено прямым указанием пользователя: проверять фактическую
работу обычных ролей и backend, не запускать отдельные модели. Остальные
детерминированные проверки, полномочия, свежая сессия и независимая приёмка
сохраняются. Смена условий не доказывает исполнение любой LLM.

Прежние `f05-c1` artifacts/delivery/receipt, результаты и ошибки CLI остаются
историей со своей revision и исходными ограничениями; их evidence не
переименовывается в current `f05-c2`. Сохранённые native Init/Resume результаты
S10 — необязательные наблюдения конкретной среды:
`.usw/state/autonomous-improvement/2026-11-10/s10-appcli-native-evidence/report.md`.
Наличие файла с `final` в имени при timeout не доказывает конечного ответа.
Новых availability probes, alternate-model attempts и benchmarks нет.

### 5. Совместимость artifacts и source

Фактический `usw.yaml`: `artifacts.root: openspec/changes`,
`flows.root: usw/flows`, `reviews.root: usw/reviews`. Legacy
`refinement.root: usw/refinements` неактивен в v1. Active exclusions:
`.git`, `.usw`, `openspec/changes`, `usw/flows`, `usw/reviews`.

Task directory:
`openspec/changes/report-persisted-status-after-outcome-failure/tasks/1.1-report-persisted-state/`.
В нём `task.md` и role-owned `development-evidence.md`/`testing-evidence.md`;
planner их evidence не создаёт и не переписывает. Stable contract — точные
bytes до строки `## Milestone log`, выбранной anchored heading; revision
`f05-c2`, Milestone не входит в stable digest. Raw hashes planning защищаются
отдельно. Старые entries/receipts сохраняются со своей revision/source.

S10 закрыт в commit `742eef5cb1ebbadb6e68f6107cc4866a5fe146a5`; повторно
его не открывать. Перед продолжением apply сверить actual HEAD, paused
операцию и незавершённые изменения developer, не повторять уже выполненное.
Proof S10-c3 о roots применим при неизменных предпосылках, без нового реестра.

До final freeze учесть sync `openspec/specs/live-operation-state/spec.md`,
согласованные `usw/backlog/AUD-F05.md`/`usw/BACKLOG.md` и уточнение
`docs/goals/usw-improvement-next.md`: они входят в product source.
Context/README не требуют нового пересказа capability: нормативный дом —
main spec, существующий context уже ссылается на неё. После любого изменения
contract/source всё прежнее evidence остаётся историческим/stale; выполнить
все обязательные проверки текущей revision/source соответствующими ролями,
без выборочного сохранения currentness.

## Risks / Trade-offs

- Router может остаться устаревшим → exact read подтверждает document,
  ошибка snapshot сообщается отдельно; автоматического repair нет.
- Router нельзя проверить → текущий state явно не подтверждён; предметный
  результат остаётся в ответе, validation не обходится.
- Заявление «не повторял» не подтверждает отсутствие эффекта → counter,
  actual state и call log проверяются независимо до удаления fixture.
- Исполнение роли — наблюдение конкретной редакции и сценария, не гарантия
  послушания любой LLM; обозначать непроверенное без model benchmarks.

## Migration Plan

Форматы state и старые документы не мигрируют. После apply и принятия
кандидатуры назначенный писатель отдельно обновляет установленный пакет.
Новая рабочая сессия сверяет исходники с установленными файлами и реально
применяет USW к разрешённому temporary-project сценарию с fault/readback,
результатом и counter. Старый успех установки S10 не подтверждает F05.

Результаты, команды и source identity принадлежат выполнявшим их ролям.
Откат — возврат ранее принятых текстов с повторной установкой; state и
предметные эффекты автоматически не откатываются и не повторяются.
