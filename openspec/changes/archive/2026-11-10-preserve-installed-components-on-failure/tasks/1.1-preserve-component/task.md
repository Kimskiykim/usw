# Task 1.1: Сохранить компонент при неудачном обновлении

## Artifact model

- `v1`

## Result

Обработанная ошибка installer сохраняет прежний компонент по контракту delta.

## Scope

`install.sh`, `tests/test_install.py`, раздел обновления `README.md`.
`usw.yaml` — project prerequisite `artifacts.root: openspec/changes` по design §5;
прочие явные roots, существующие материалы и defaults поставки сохраняются.
Preflight источников/назначений, подготовленная копия, переключение и rollback,
leaf symlink, сообщения о частичном результате. Tests и документация входят
в ту же coding task, чтобы итоговая source identity была общей. Stable-token
проверки в `tests/test_install.py` обновляются для путей/имён компонентов и
структуры дерева; формулировки целых сообщений не фиксируются.

## Non-scope

Ограничения proposal; исходники skills, generated skills, plugin managers,
другие AUD-карточки, обработка родительских symlink и общая транзакция. Реальная общая
установка, независимая приёмка и archive выполняются после coding task.

## References

- Proposal: `../../proposal.md`; design: `../../design.md`.
- Delta: `../../specs/component-installation/spec.md`.
- Источник: `usw/backlog/AUD-S10.md`; процесс: `openspec/context/08-process-conventions.md`.
- Evidence contract: `openspec/specs/execution-artifacts/spec.md`.

## Dependencies

Завершённое planning и отдельное поручение apply; исключительное право записи
разработчика, исходный HEAD `95ab1345582f293e7eb74a76471d4f0e00c27802` плюс
принятые planning files. Перед началом сверить фактическую редакцию, сохранить
посторонние правки и не переиспользовать snapshot вместо проверки checkout.

## Definition of done

Все сценарии delta покрыты матрицей design и детерминированными tests.
Постоянные tests сравнивают полные рекурсивные paths/types/bytes/link-target
прежнего target, retained backup и нового дерева. Proof source compatibility
из design §5 выполнен; фактические config/manifest/exclusions общие для ролей.
Сначала записан неуспех регрессии на исходном installer; затем все checks
ниже успешны на окончательной редакции. Успех установки/force/legacy из четырёх
прежних tests сохранён. Bytecode не попадает в установленную копию. README
ссылается на capability, не дублирует её контракт. Нет новых зависимостей.
Development evidence содержит command, result, timestamp, contract revision,
`USW-SOURCE-V1` по нормативному конечному manifest и ссылки на raw logs.
Перед `[x]` завершены применимые USW-операции с Outcome/readback.

## Verification

1. В temporary source/target fixture подтвердить red минимум для partial
   skill copy и missing late source, без изменения общей установки.
2. Выполнить `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_install.py -v`;
   ожидание: все новые и прежние install tests зелёные.
3. Выполнить `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`,
   `sh -n install.sh`, `openspec validate preserve-installed-components-on-failure --strict`
   и `git diff --check`; ожидание: exit 0 у каждой команды, без пропущенных
   применимых installer-сценариев. Проверить structural/path anchors package.
4. Связать каждый сценарий delta с конкретным test/log и observed bytes/type;
   отдельно проверить partial command write, отказ удаления bytecode до активации,
   отказ final cleanup после активации и два последовательных отказа rename.
   Сообщённые оставшиеся пути сверить с диском, обязательный полный backup сохранён.
   stdout процесса не заменяет filesystem assertions. При новом source
   всё прежнее v1 evidence stale; выполнить обязательные checks заново.
5. Проверить в fixture инвариантность digest при checkbox/Milestone/evidence
   и его изменение при installer/main spec. После actual config/source/contract
   change повторить checks 2–3; прежние raw logs и invalid entries не переписывать.
   Поздний sync/main spec или правка включённого backlog требует нового manifest/checks.

## Contract revision

- `s10-c3`; стабильная часть не включает Milestone log.

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | planning создан | `s10-c1` | source реализации ещё не сформирован | реализация не начата | `../../proposal.md` |
| 1 | уточнение planning после critic | `s10-c2` | source реализации ещё не сформирован | реализация не начата; прежняя history сохранена | `../../design.md` |
| 1 | development проверен, ожидание критика | `s10-c2` | `usw-source-v1:73242e2698005f5a25ca9504eb76a316c5f86b871860f9ce63bf3fc59b3905cc` | local checks пройдены; USW operation и task остаются открытыми | `development-evidence.md` |
| 1 | исправление source attribution | `s10-c2` | прежний digest invalid для v1 | команды остаются фактами; entries не являются current pass | `development-evidence.md` — раздел исправления |
| 2 | repair1: config prerequisite и полнота assertions | `s10-c3` | окончательный source ещё не сформирован | ожидаются отдельный apply и повторные checks | `../../design.md` §4–5 |
| 2 | repair1 checks, ожидание критика | `s10-c3` | `usw-source-v1:59f9f0b0f89b8c8c7ee461d0adb00963bd6ceb536f4f7d318ac2666cac98c0ed` | local checks пройдены; задача открыта до завершения операции и review | `development-evidence.md` |
| 2 | sync spec и история AUD-S10; ожидание независимой приёмки | `s10-c3` | `usw-source-v1:0e7680de35299206af642e8ea99d8f158bbb5ce9546bf8bc6169ce89eac1930d` | Development checks пройдены; предыдущие evidence stale; USW operation и task остаются открыты | `development-evidence.md` |
| 2 | final source после решения AUD-S10 | `s10-c3` | `usw-source-v1:67d3b00e07be3aebb9beac40241d38efb77b4c9cf836f4adb9fb33ffaf5e2cc3` | Development checks пройдены; ожидание независимых Testing и review, задача открыта | `development-evidence.md` |
| 2 | flow завершён после accepted review | `s10-c3` | `usw-source-v1:67d3b00e07be3aebb9beac40241d38efb77b4c9cf836f4adb9fb33ffaf5e2cc3` | Outcome completed/readback; coding task завершена, transition ожидается | `development-evidence.md` |
