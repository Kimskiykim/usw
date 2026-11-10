# Task 1.1: Честный повторный вход после ожидания события

## Artifact model

- `v1`

## Result

Автор flow предлагает блок ожидания события с доступным способом продолжения:
при `handoff: false` человек получает ручной контекст повторного входа без
обещания resume той же operation. Одна проверка, `blocked` и отсутствие
polling сохраняются в обоих authoring styles.

## Scope

Production: `skills/usw-create-flow/references/recipes/external-event-wait.md`.
Test: узкие stable-token/structure checks в `tests/test_package_layout.py`.
Norm: delta `../../specs/guided-flow-authoring/spec.md` и её sync в
`openspec/specs/guided-flow-authoring/spec.md` до конечного source freeze.
Связанный учёт после доказанного apply: `usw/backlog/AUD-I13.md` и строка
AUD-I13 в `usw/BACKLOG.md` получают только точную отметку wait subitem со
ссылкой на этот change и явным остатком двух других частей; статус карточки
остаётся `backlog`, строка остаётся в индексе. Эти files входят в source.

## Non-scope

Другие рецепты AUD-I13, `SKILL.md`, catalog/pattern changes, backend, commands,
CLI, state format/status, scheduler, polling, новая очередь/курсор/обязательный
recovery файл. Установка/global package, коммит/index/push/интеграция не входят
в эту задачу. Специальные model CLI/API inference, availability/effort probes,
платные before/after серии и новый harness запрещены поручением.

## References

- [Proposal](../../proposal.md), [design](../../design.md),
  [delta](../../specs/guided-flow-authoring/spec.md).
- Нормы: `openspec/specs/live-operation-state/spec.md`,
  `openspec/specs/execution-artifacts/spec.md`, architecture/ADR-001,
  `openspec/context/06-testing-and-quality.md` и `08-process-conventions.md`.
- Источник: `usw/backlog/AUD-I13.md`; audit REVIEW строка 215.
- Baseline evidence/reader limits и actual roots/paths — design § Decisions.
  Local delivery: `.usw/state/create-flow-improvement/condition-external-event-resume/delivery.md`.

## Dependencies

Независимый critic принимает точные шесть planning artifacts, затем пользователь
или назначающий root отдельно поручает apply. Проверить HEAD/branch/source,
raw planning hashes и stable digest из local `planning-identities.json`.
Baseline: `2cee3137e6ed637a7ab94558f637fc1259014b9d`,
`usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90`.
T01 не включён; не переносить его полномочия или installed package в proof.

## Definition of done

Рецепт убирает безусловное same-operation promise. Контекст ручного входа
конкретизируется создаваемым flow: его имя/origin/project, проверенные факты,
ожидаемое событие, одна проверка, оставшееся действие и ограничения повторов.
Это данные для ответа человеку, не новый обязательный формат, destination или
файл. При `false` нельзя читать/проверять/создавать handoff artifacts; нельзя
обещать их сохранение, автоматический запуск либо курсор. При `true` действует
существующий recovery contract и фактически сохранённые сведения. Рецепт не
включает handoff и не предоставляет полномочия сам по себе.

Обычная назначенная роль читает поставляемый каталог/рецепт без алгоритма от
автора и показывает применимый preview в обычной прозе и `version-2`.
По отдельному разрешению fixture записи она реально записывает и исполняет
минимальный flow в `/tmp` проекте. Событие отсутствует: один check и `blocked`;
в false-режиме ответ содержит ручной контекст без same-operation promise,
state access отсутствует. Затем явный повторный вход с переданным context:
одна новая проверка, уже завершённый локальный effect не повторяется.
Проверить также `true`: фактический `blocked` Outcome и saved fields
соответствуют ответу; после остановки нет самовольного Resume, второго Begin
или эффекта. Это проверка остановки и честности guidance, не отдельный repair
протокола продолжения run/manage. Independent Testing сверяет actual calls,
bytes и ответ.

Evidence включает actual preview/записанный текст, разрешение fixture записи,
check/effect counters, call trace, начальные/конечные snapshots и readback до
cleanup; тестовая instrumentation может читать snapshots, исполнитель при
`false` — нет. Статическое чтение или наличие markers не заменяют эти действия.
Один наблюдённый путь не доказывает поведение всех моделей или реальных CI.

Stable-token tests фиксируют `blocked`, условие `handoff: false`, разделение
продолжения и обычный/structured styles; не закрепляют полные предложения.
Main-spec/card/index edits учтены до конечного manifest. Все обязательные
checks ниже имеют успешное актуальное Development evidence. Development пишет
только `development-evidence.md`, Testing — только `testing-evidence.md`;
entries содержат ID, `i13-wait-c1`, source, command/check, result, timestamp.
Смена contract/source делает все прежние entries/receipts stale; до `[x]`
повторяются все обязательные checks текущих identities. Milestone/history не
переписываются. `[x]` означает только выполнение Development, не независимую
приёмку. Закрывать всю AUD-I13 или другие изменения нельзя.

## Verification

1. Воспроизвести два режима обычными инструментами назначенных ролей по DoD;
   `TemporaryDirectory(dir='/tmp')`, Python `-B`, разрешённые действия локальны.
   False: actual call log не содержит handoff calls, snapshot state неизменен,
   один check за вход и effect-counter=1 после повторного входа. True: actual
   blocked operation context/response сверены, scheduler/машинный cursor не
   заявлены, автоматических Resume/второго Begin после остановки нет.
2. Выполнить `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_package_layout.py -v`,
   затем `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`.
   Сохранить успешные outputs, прежние disabled/manual/nested guards.
3. Выполнить `openspec validate condition-external-event-resume --strict`,
   v1 task contract validation существующим helper и `git diff --check`;
   отдельно проверить LF, links и whitespace новых untracked artifacts.
4. Поиск `resume`/`handoff` в изменённом рецепте и actual generated previews:
   нет безусловного обещания той же operation при `false`; обычный Markdown
   без `CALL`/`GATE`/`LOOP`/`PARALLEL`, token `blocked` сохранён.
5. После main-spec/card/index edits вычислить полный canonical source;
   выполнить все checks на нём, зафиксировать role-owned evidence и передать
   independent Testing. `SKILL.md` не меняется; paid behavior evals не нужны
   и запрещены текущим поручением. Общие harness/suites сохраняются.

## Contract revision

- `i13-wait-c1`
- Stable bytes: всё до anchored heading `## Milestone log`; digest по
  существующему `task_contract_identity`, Milestone не входит в identity.
  Raw planning hashes защищают полные artifacts отдельно.

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
| --- | --- | --- | --- | --- | --- |
| — | Создан planning contract; ordinary reader и disabled backend подтвердили узкий дефект | `i13-wait-c1` | Baseline указан в Dependencies; implementation source не назначен | Review/apply pending, verification только запланирована | Design; local planning evidence |
