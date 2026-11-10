# Task 1.1: Сохранить компонент при неудачном обновлении

## Artifact model

- `v1`

## Result

Обработанная ошибка installer сохраняет прежний компонент по контракту delta.

## Scope

`install.sh`, `tests/test_install.py`, раздел обновления `README.md`.
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

## Contract revision

- `s10-c2`; стабильная часть не включает Milestone log.

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | planning создан | `s10-c1` | source реализации ещё не сформирован | реализация не начата | `../../proposal.md` |
| 1 | уточнение planning после critic | `s10-c2` | source реализации ещё не сформирован | реализация не начата; прежняя history сохранена | `../../design.md` |
