# Development evidence: 1.1

Writer authority: Development only.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| dev-t08-01 | `t08-c1` | `usw-source-v1:d7c8624a3aa96d968a96158a60b2bdfb979caa2b5b0d1adf15268081a6adbbb1` | `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_execution_recovery_contract.py -v` | passed | 2026-11-10T19:09:57Z |
| dev-t08-02 | `t08-c1` | `usw-source-v1:d7c8624a3aa96d968a96158a60b2bdfb979caa2b5b0d1adf15268081a6adbbb1` | `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v` | passed | 2026-11-10T19:09:57Z |
| dev-t08-03 | `t08-c1` | `usw-source-v1:d7c8624a3aa96d968a96158a60b2bdfb979caa2b5b0d1adf15268081a6adbbb1` | `openspec validate align-execution-recovery-owner --strict` | passed | 2026-11-10T19:09:57Z |
| dev-t08-04 | `t08-c1` | `usw-source-v1:d7c8624a3aa96d968a96158a60b2bdfb979caa2b5b0d1adf15268081a6adbbb1` | `git diff --check` | passed | 2026-11-10T19:09:57Z |

## Наблюдения

- Адресный тест до изменения обнаружил три ошибки прежнего owner; после применения delta прошли 4 теста. Полная suite: 306 тестов, exit 0. Повторена после последней правки product source.
- Сверка с baseline: семь requirements без изменений; три блока равны принятой delta; сохранены пять scenario identities, две непредметные scenarios и paragraph владельцев task/evidence/receipts. В индексе изменены только строка AUD-T08 и счётчик P2.
- Native v1 task validation и OpenSpec strict прошли; raw identities шести planning artifacts и stable identity совпали с candidate-v2 freeze.
- Независимый ordinary reader ещё не проверил три ситуации. Development readiness и checkbox остаются открытыми; Testing и merged-source приёмка выполняются отдельно. При изменении revision или product source этот evidence становится stale.

## Независимый ordinary-reader proof

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| dev-t08-05 | `t08-c1` | `usw-source-v1:d7c8624a3aa96d968a96158a60b2bdfb979caa2b5b0d1adf15268081a6adbbb1` | `independent ordinary-reader: pause, replanning, generic flow` | passed | 2026-11-10T19:12:19Z |

- Исполнитель: субагент `/root/ordinary_reader`, `gpt-6.1-terra`, effort `xhigh`, fresh context `fork:none`; только чтение. Ему переданы обе действующие спецификации и три ситуации без ожидаемых выводов.
- Прочитанные спецификации (raw SHA-256): `openspec/specs/execution-artifacts/spec.md` — `02b712c178a7083beab91b3442cd1d5e4c8005df446cb74e2151483aa8fb5605`; `openspec/specs/live-operation-state/spec.md` — `e6fe4caa5dd4ad1d6336aa0b9cf2f1160603bd641ef59b9e07aafd3e638f92d3`.
- Оценка Development: для всех трёх ситуаций указан точный operation document; HANDOFF назван router, при replanning сохраняются факты, а generic handoff не требует shared artifacts/receipts. Условие `handoff: false` отдельно отмечено. Это наблюдение одной редакции, не доказательство для всех читателей.
- Ранее записанное отсутствие reader описывало состояние до этого результата; независимые Testing и merged-source приёмка остаются открыты.
- SHA-256 UTF-8 exact payload без завершающего LF: `eaada25257a6911000d5b98977ecb3b90c5f4234c22065fcff16360c67f2b85c`.

### Exact reader payload

```text
При включённом `handoff` восстановительный контекст хранится в точном документе операции `.usw/handoffs/<operation-hex>.md`. Файл `.usw/HANDOFF.md` — локальный маршрутизатор и человекочитаемый снимок зарегистрированных операций. При `handoff: false` к этим файлам и candidate обращаться нельзя. Источники: [execution-artifacts](</Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff/openspec/specs/execution-artifacts/spec.md:14>), [live-operation-state](</Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff/openspec/specs/live-operation-state/spec.md:254>).

1. **Development приостанавливает активную задачу.** При естественной паузе Outcome записывает в точный документ операции статус `paused`, текущую позицию и одно следующее действие; также сохраняется достаточный контекст выполненной работы, проверок, препятствия и ссылок. После обновления документа обновляется снимок в router. Shared task artifacts не должны получать выдуманный результат или отметку завершения. Фактически выполненные обязательные локальные проверки фиксируются в `development-evidence.md` со всеми необходимыми данными, включая результат; запланированная проверка не считается выполненной. Завершение задачи отмечается только в change `tasks.md` после выполнения условий задачи и обязательных проверок. Источники: [execution-artifacts, приостановка](</Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff/openspec/specs/execution-artifacts/spec.md:20>), [live-operation-state, пауза](</Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff/openspec/specs/live-operation-state/spec.md:21>).

2. **После частичного выполнения меняется порядок pending действий.** Оставшиеся локальные действия обновляются в точном документе операции; подтверждённые факты, `Milestone log`, evidence и receipts сохраняются. Запись в `Milestone log` добавляется только при новой попытке или значимом переходе. Само изменение порядка не меняет revision стабильного контракта и актуальность evidence. Если при этом отдельно меняется стабильный контракт, нужна новая revision, а прежнее evidence сохраняется, но становится неактуальным для неё; изменение source identity также инвалидирует evidence v1. Отдельный task-level `plan.md` не является обязательным или каноническим артефактом. Источники: [execution-artifacts, replanning](</Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff/openspec/specs/execution-artifacts/spec.md:177>), [раздельное evidence](</Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff/openspec/specs/execution-artifacts/spec.md:75>).

3. **Приостанавливается generic text flow без shared task artifacts.** При включённом handoff его точный документ операции сохраняет достаточный narrative recovery context: исходный результат и проверенную часть в `Done`, остаток и причины в `Current position`, препятствие в `Blocker` или `none`, одно следующее действие в `Next action`, а также проверки и ссылки. Статус определяется причиной остановки: естественная пауза — `paused`, устранимое внешнее препятствие — `blocked`, граница разрешения — `decision_required`. Документ также содержит identity и сведения flow, статус, `Summary`, timestamps и `Workspace`; router хранит соответствующую route. Generic handoff не требует typed subject, роли, write authority, shared evidence или review receipts и сам не является общей долговременной историей задачи. Служебный handoff внутри flow следует конфигурации без отдельного ручного вызова. Источники: [generic handoff](</Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff/openspec/specs/execution-artifacts/spec.md:65>), [содержимое и статусы](</Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff/openspec/specs/live-operation-state/spec.md:9>), [recovery context](</Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff/openspec/specs/live-operation-state/spec.md:316>), [конфигурация flow](</Users/leonidkim/.codex/parallel-workspaces/usw/20261110-92635ffc/run-handoff/openspec/specs/live-operation-state/spec.md:400>).

Файлы не изменялись.
```

## Development на merged primary

Предыдущие entries `dev-t08-01`–`dev-t08-05` относятся к source копии `d7c862…` и сохранены как stale. Проверки ниже фактически выполнены на primary после T01. Raw команды, timestamps, manifest, сохранность норм и ответ reader — `.usw/state/run-handoff/align-execution-recovery-owner/primary/`.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| dev-t08-primary-target | `t08-c1` | `usw-source-v1:9fe5eb19901face2f10bee93a1a805b0b9d6881375f141c548051aa1588a2d32` | `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_execution_recovery_contract.py -v` | passed (4 tests) | 2026-11-10T19:41:48.794206+00:00 |
| dev-t08-primary-full | `t08-c1` | `usw-source-v1:9fe5eb19901face2f10bee93a1a805b0b9d6881375f141c548051aa1588a2d32` | `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v` | passed (310 tests) | 2026-11-10T19:42:06.777037+00:00 |
| dev-t08-primary-validate | `t08-c1` | `usw-source-v1:9fe5eb19901face2f10bee93a1a805b0b9d6881375f141c548051aa1588a2d32` | `openspec validate align-execution-recovery-owner --strict` | passed | 2026-11-10T19:42:08.315176+00:00 |
| dev-t08-primary-diff | `t08-c1` | `usw-source-v1:9fe5eb19901face2f10bee93a1a805b0b9d6881375f141c548051aa1588a2d32` | `git diff --check` | passed | 2026-11-10T19:42:08.345437+00:00 |
| dev-t08-primary-reader | `t08-c1` | `usw-source-v1:9fe5eb19901face2f10bee93a1a805b0b9d6881375f141c548051aa1588a2d32` | ordinary reader: pause, replanning, generic flow | passed | 2026-11-10T19:42:09.152609+00:00 |
| dev-t08-primary-preservation | `t08-c1` | `usw-source-v1:9fe5eb19901face2f10bee93a1a805b0b9d6881375f141c548051aa1588a2d32` | freeze-check: 3 blocks, 7 requirements, 5 scenarios, LF, links, source, scope | passed | 2026-11-10T19:42:19.942138+00:00 |
| dev-t08-primary-v1 | `t08-c1` | `usw-source-v1:9fe5eb19901face2f10bee93a1a805b0b9d6881375f141c548051aa1588a2d32` | pending v1 task/link validation (архивный helper как дополнительная проверка) | passed | 2026-11-10T19:42:36.252500+00:00 |

Reader: свежий `/root/t08_ordinary_reader`, Terra/xhigh, отдельный контекст; ответ и хеши двух specs сохранены в `primary/ordinary-reader.md` и `primary/reader.json`. Наблюдение ограничено этим чтением. Приостановленные USW operations в этом задании не запускались.

Для совместимости проверочного helper две записи ниже ссылаются на те же фактические запуски target/full; повторного запуска не было.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| dev-t08-primary-target-canonical | `t08-c1` | `usw-source-v1:9fe5eb19901face2f10bee93a1a805b0b9d6881375f141c548051aa1588a2d32` | `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_execution_recovery_contract.py -v` | passed | 2026-11-10T19:41:48.794206+00:00 |
| dev-t08-primary-full-canonical | `t08-c1` | `usw-source-v1:9fe5eb19901face2f10bee93a1a805b0b9d6881375f141c548051aa1588a2d32` | `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v` | passed | 2026-11-10T19:42:06.777037+00:00 |
