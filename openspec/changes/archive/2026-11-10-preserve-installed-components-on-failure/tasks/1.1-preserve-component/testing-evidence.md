# Testing evidence: AUD-S10, task 1.1

Все entries относятся к contract `s10-c3` и source `usw-source-v1:59f9f0b0f89b8c8c7ee461d0adb00963bd6ceb536f4f7d318ac2666cac98c0ed`; HEAD `1b8c08b5e6e7d42234ffda5c75199afb499e2104`. Новые source или contract делают эти entries stale.

| ID | Check | Result | Timestamp UTC | Finding |
|---|---|---|---|---|
| s10-c3-test-fresh-01 | `PYTHONDONTWRITEBYTECODE=1 python3 .usw/state/autonomous-improvement/2026-11-10/s10-fresh-package-check.py` | 6 installed skills / 73 files и 10 commands: paths, types, bytes, executable bits совпадают с source без намеренно исключённых bytecode caches; в установленном пакете caches нет. Log: `.usw/state/autonomous-improvement/2026-11-10/s10-fresh-package-check.log`. | 2026-11-10T06:35:21Z | По проверенному составу отсутствует. |
| s10-c3-test-fresh-02 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_install.py -v` | 11/11 успешно, 13.597 s; subprocess fixtures, без изменения общей установки. Log: `.usw/state/autonomous-improvement/2026-11-10/s10-fresh-install-tests.log`. | 2026-11-10T06:35:21Z | В проверенных сценариях отсутствует. Это не проверка Linux. |
| s10-c3-test-fresh-03 | `init_usw.load_config` + `artifact_contract.build_source_manifest`, сравнение с сохранённым manifest | Побайтовое совпадение manifest; configured roots `openspec/changes`, `usw/flows`, `usw/reviews`; installer SHA-256 `92517929752913b6d9c80274284aa168acdeeedf922b448e3e4830aa0ddcb04a`. | 2026-11-10T06:35:21Z | Отсутствует; при sync main spec или изменении включённого backlog нужна новая identity и checks по контракту. |
| s10-c3-test-fresh-04 | Явный запрос `/usw-resume` по точной операции; чтение установленных command/skill и вызов установленного `handoff_state.py resume` | Скрипт вернул exit 0, `paused`, контекст и точный путь операции; выполненные изменения не повторялись. | 2026-11-10T06:35:21Z | Нативный выбор host command/skill не наблюдался и не доказан; ручное чтение файлов не является его подтверждением. |

Фактическая переустановка подтверждена отдельным журналом `.usw/state/autonomous-improvement/2026-11-10/s10-real-install.log` и снимками `.json`, а не этой ролью. Первая наивная сверка source включила локальные `__pycache__` и выявила различия с установленной копией; повтор выполнен с штатным исключением bytecode только из source и отдельным контролем отсутствия caches в target. README-ссылка на main spec остаётся pending до sync. Полный suite не повторялся; Development сообщил 299/299 на этом source. Нативный picker и продолжение после Save в следующей новой сессии остаются непроверенными. Это evidence не закрывает task, change или цель и не заменяет review receipt.

| ID | Contract | Source | Check | Result | Timestamp UTC | Finding |
|---|---|---|---|---|---|---|
| s10-c3-test-native-01 | `s10-c3` | `usw-source-v1:59f9f0b0f89b8c8c7ee461d0adb00963bd6ceb536f4f7d318ac2666cac98c0ed` | Два последовательных `codex exec --json -s workspace-write` с явными `$usw-initialize-project` и `$usw-manage-handoff`, `gpt-6.1-terra`, xhigh, временный проект; анализ только их rollout. | В обоих rollout хост добавил блок `<skill>` с именем, точным installed path и полным совпадающим `SKILL.md` при `allow_implicit_invocation: false`. Оба model requests завершились HTTP 400 `model_not_found`, exit 1, до команд агента. Вторая fixture operation подготовлена отдельно скриптами и осталась `paused`. | 2026-11-10T06:44:17Z | Связывание CLI подтверждено; выполнение Init/Resume в native CLI и Desktop picker не подтверждены. Подробности, команды и ссылки на два rollout: `.usw/state/autonomous-improvement/2026-11-10/s10-native-cli-probe-report.md`. |

## Final Testing: s10-c3, current source

Предыдущие записи и ограничения выше относятся к исторической source `59f9…` и stale; новые проверки ниже выполнены на `usw-source-v1:67d3b00e07be3aebb9beac40241d38efb77b4c9cf836f4adb9fb33ffaf5e2cc3`. Подробности и raw: `.usw/state/autonomous-improvement/2026-11-10/s10-final-testing/`.

| ID | Check / command | Result | UTC | Finding |
|---|---|---|---|---|
| s10-final-test-01 | `manifest-check.py`, before/after и Development manifest | Побайтово совпали; текущий source `67d3…`, contract `s10-c3`. | 2026-11-10T08:31:35Z | Нет. |
| s10-final-test-02 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_install.py -v` | 11/11, exit 0; изолированные fixtures. | 2026-11-10T08:31:35Z | Нет в проверенном охвате; Linux не проверен. |
| s10-final-test-03 | `s10-fresh-package-check.py`; `spec-check.log` | 73 файла 6 skills и 10 commands совпадают с source, кэшей нет; README → main spec и требования delta совпадают. | 2026-11-10T08:31:35Z | Нет. |
| s10-final-test-04 | `evidence-check.py`: проверка ранее сохранённых установки, Save→Resume и native CLI | Исторические факты сопоставимы по installer/package; `0e`→`67` изменились только card/index. Установка и native-вызовы не повторялись; старые v1 entries остаются stale. | 2026-11-10T08:31:35Z | Нет в проверенном охвате; Desktop picker не проверен. |
