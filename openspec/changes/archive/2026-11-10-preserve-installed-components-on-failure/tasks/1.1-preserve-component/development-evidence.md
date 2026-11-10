# Development evidence: 1.1

Writer authority: Development only.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| s10-dev-01 | `s10-c2` | `usw-source-v1:73242e2698005f5a25ca9504eb76a316c5f86b871860f9ce63bf3fc59b3905cc` | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_install.py -v` | 11/11 passed | 2026-11-10T05:42:16Z |
| s10-dev-02 | `s10-c2` | `usw-source-v1:73242e2698005f5a25ca9504eb76a316c5f86b871860f9ce63bf3fc59b3905cc` | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | 299/299 passed | 2026-11-10T05:42:16Z |
| s10-dev-03 | `s10-c2` | `usw-source-v1:73242e2698005f5a25ca9504eb76a316c5f86b871860f9ce63bf3fc59b3905cc` | `sh -n install.sh` | exit 0 | 2026-11-10T05:42:16Z |
| s10-dev-04 | `s10-c2` | `usw-source-v1:73242e2698005f5a25ca9504eb76a316c5f86b871860f9ce63bf3fc59b3905cc` | `openspec validate preserve-installed-components-on-failure --strict` | exit 0 | 2026-11-10T05:42:16Z |
| s10-dev-05 | `s10-c2` | `usw-source-v1:73242e2698005f5a25ca9504eb76a316c5f86b871860f9ce63bf3fc59b3905cc` | `git diff --check` | exit 0 | 2026-11-10T05:42:16Z |

Raw logs и сопоставление сценариев: `.usw/state/autonomous-improvement/2026-11-10/s10-development-report.md`.

## Исправление: identity и evidence ожидают разрешения

Записи `s10-dev-01`–`s10-dev-05` сохраняют фактически выполненные команды и их
результаты, но указанный в них source ID недействителен для v1: manifest
ошибочно исключил весь `openspec/changes`, чего конфигурация не задаёт.
Эти записи не являются актуальным успешным Development evidence. Task checkbox
остаётся открытым. Точный текущий manifest и проблема самоссылки описаны в
`.usw/state/autonomous-improvement/2026-11-10/s10-development-report.md`.

## Attempt 2: s10-c3

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| s10-c3-dev-01 | `s10-c3` | `usw-source-v1:59f9f0b0f89b8c8c7ee461d0adb00963bd6ceb536f4f7d318ac2666cac98c0ed` | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_install.py -v` | 11/11 passed | 2026-11-10T06:11:53Z |
| s10-c3-dev-02 | `s10-c3` | `usw-source-v1:59f9f0b0f89b8c8c7ee461d0adb00963bd6ceb536f4f7d318ac2666cac98c0ed` | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | 299/299 passed | 2026-11-10T06:11:53Z |
| s10-c3-dev-03 | `s10-c3` | `usw-source-v1:59f9f0b0f89b8c8c7ee461d0adb00963bd6ceb536f4f7d318ac2666cac98c0ed` | `sh -n install.sh` | exit 0 | 2026-11-10T06:11:53Z |
| s10-c3-dev-04 | `s10-c3` | `usw-source-v1:59f9f0b0f89b8c8c7ee461d0adb00963bd6ceb536f4f7d318ac2666cac98c0ed` | `openspec validate preserve-installed-components-on-failure --strict` | exit 0 | 2026-11-10T06:11:53Z |
| s10-c3-dev-05 | `s10-c3` | `usw-source-v1:59f9f0b0f89b8c8c7ee461d0adb00963bd6ceb536f4f7d318ac2666cac98c0ed` | `git diff --check` | exit 0 | 2026-11-10T06:11:53Z |
| s10-c3-dev-06 | `s10-c3` | `usw-source-v1:59f9f0b0f89b8c8c7ee461d0adb00963bd6ceb536f4f7d318ac2666cac98c0ed` | `PYTHONDONTWRITEBYTECODE=1 python3 .usw/state/autonomous-improvement/2026-11-10/s10-c3-source-proof.py` | fixture proof passed | 2026-11-10T06:11:53Z |

Raw logs и матрица: `.usw/state/autonomous-improvement/2026-11-10/s10-c3-development-report.md`.

## Closeout: текущий source после sync и backlog

Записи `s10-c3-dev-01`–`s10-c3-dev-06` и прежнее Testing evidence сохранены как
история: после включённых изменений их source identity больше не текущая.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| s10-c3-closeout-dev-01 | `s10-c3` | `usw-source-v1:0e7680de35299206af642e8ea99d8f158bbb5ce9546bf8bc6169ce89eac1930d` | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_install.py -v` | passed: 11/11 | 2026-11-10T07:45:52Z |
| s10-c3-closeout-dev-02 | `s10-c3` | `usw-source-v1:0e7680de35299206af642e8ea99d8f158bbb5ce9546bf8bc6169ce89eac1930d` | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | passed: 299/299 | 2026-11-10T07:46:10Z |
| s10-c3-closeout-dev-03 | `s10-c3` | `usw-source-v1:0e7680de35299206af642e8ea99d8f158bbb5ce9546bf8bc6169ce89eac1930d` | `sh -n install.sh` | passed: exit 0 | 2026-11-10T07:46:10Z |
| s10-c3-closeout-dev-04 | `s10-c3` | `usw-source-v1:0e7680de35299206af642e8ea99d8f158bbb5ce9546bf8bc6169ce89eac1930d` | `openspec validate preserve-installed-components-on-failure --strict` | passed: exit 0 | 2026-11-10T07:46:11Z |
| s10-c3-closeout-dev-05 | `s10-c3` | `usw-source-v1:0e7680de35299206af642e8ea99d8f158bbb5ce9546bf8bc6169ce89eac1930d` | `git diff --check` | passed: exit 0 | 2026-11-10T07:46:11Z |
| s10-c3-closeout-dev-06 | `s10-c3` | `usw-source-v1:0e7680de35299206af642e8ea99d8f158bbb5ce9546bf8bc6169ce89eac1930d` | `PYTHONDONTWRITEBYTECODE=1 python3 .usw/state/autonomous-improvement/2026-11-10/s10-c3-source-proof.py` | passed: fixture proof | 2026-11-10T07:46:11Z |
| s10-c3-closeout-dev-07 | `s10-c3` | `usw-source-v1:0e7680de35299206af642e8ea99d8f158bbb5ce9546bf8bc6169ce89eac1930d` | `openspec validate --specs` | passed: 22/22, warnings в других specs | 2026-11-10T07:46:12Z |

Raw logs: `.usw/state/autonomous-improvement/2026-11-10/s10-closeout-{install,full,shell,validate,diff,proof,specs}.log`; время и exit: `s10-closeout-checks.summary`. Manifest и config: `s10-closeout-source-v1.manifest` и `.json` в том же каталоге. Матрица сценариев и исходный red сохранены в `s10-c3-development-report.md` и упомянутых им raw logs; installer и tests после той редакции не менялись. Package anchors входят в полный suite. Поведенческие evals неприменимы: `SKILL.md` не изменён.

## Финальный source после решения по AUD-S10

Предыдущие v1 entries, включая `s10-c3-closeout-dev-*` и Testing entries, stale после изменения включённых card/index; они остаются историей. Для всех строк ниже contract `s10-c3`, source `usw-source-v1:67d3b00e07be3aebb9beac40241d38efb77b4c9cf836f4adb9fb33ffaf5e2cc3`; raw logs и время начала/конца — `.usw/state/autonomous-improvement/2026-11-10/s10-final-checks.summary` и `s10-final-{install,full,shell,validate,diff,proof}.log`.

| ID | Contract revision | Source identity | Check | Result | Detail | Timestamp UTC |
|---|---|---|---|---|---|---|
| s10-final-dev-01 | `s10-c3` | `usw-source-v1:67d3b00e07be3aebb9beac40241d38efb77b4c9cf836f4adb9fb33ffaf5e2cc3` | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_install.py -v` | passed | 11/11 | 2026-11-10T08:28:10Z |
| s10-final-dev-02 | `s10-c3` | `usw-source-v1:67d3b00e07be3aebb9beac40241d38efb77b4c9cf836f4adb9fb33ffaf5e2cc3` | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | passed | 299/299; package anchors | 2026-11-10T08:28:33Z |
| s10-final-dev-03 | `s10-c3` | `usw-source-v1:67d3b00e07be3aebb9beac40241d38efb77b4c9cf836f4adb9fb33ffaf5e2cc3` | `sh -n install.sh` | passed | exit 0 | 2026-11-10T08:28:33Z |
| s10-final-dev-04 | `s10-c3` | `usw-source-v1:67d3b00e07be3aebb9beac40241d38efb77b4c9cf836f4adb9fb33ffaf5e2cc3` | `openspec validate preserve-installed-components-on-failure --strict` | passed | exit 0 | 2026-11-10T08:28:33Z |
| s10-final-dev-05 | `s10-c3` | `usw-source-v1:67d3b00e07be3aebb9beac40241d38efb77b4c9cf836f4adb9fb33ffaf5e2cc3` | `git diff --check` | passed | exit 0 | 2026-11-10T08:28:33Z |
| s10-final-dev-06 | `s10-c3` | `usw-source-v1:67d3b00e07be3aebb9beac40241d38efb77b4c9cf836f4adb9fb33ffaf5e2cc3` | `PYTHONDONTWRITEBYTECODE=1 python3 .usw/state/autonomous-improvement/2026-11-10/s10-c3-source-proof.py` | passed | fixture proof | 2026-11-10T08:28:34Z |

Manifest/exclusions: `.usw/state/autonomous-improvement/2026-11-10/s10-final-source-v1.manifest` и `s10-final-source-v1.json`; совпадение до/после проверок подтверждено. Исходные red и матрица наблюдаемых bytes/types остаются в `s10-c3-development-report.md`; старые native проверки не переисполнялись на новой identity.
