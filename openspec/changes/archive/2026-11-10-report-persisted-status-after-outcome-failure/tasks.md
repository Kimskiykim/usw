# Tasks

## 1. Достоверный отчёт после ошибки Outcome

- [x] 1.1 [Сообщать проверенное состояние точной операции](tasks/1.1-report-persisted-state/task.md). DoD `f05-c2`: сценарии delta реализованы в узких разделах run/manage `SKILL.md`; backend, manual activation, disabled boundary и stable tokens сохранены. Proof: три deterministic backend fault cases с actual bytes/status/exact readback, counter=1 и неизменной соседней операцией; независимое чтение и реальное исполнение текстового протокола обычными назначенными ролями по design §3. Адресные/полный unittest, strict validate и diff check успешны на конечном source. Общие harness/suites сохраняются; model/effort/availability, специальные CLI/API inference и before/after серии не являются gates. Полный контракт и проверки — в leaf task; статическое чтение не заменяет фактические действия.

Порядок: принятый planning `f05-c2` → сверить actual post-S10 checkout,
paused operation и прежний незавершённый patch → продолжить ограниченное
исправление и полезные локальные fixtures → независимо проверить состояние
и текстовый путь. S10 уже закрыт/закоммичен, его не открывать заново.
Прежние проверки `f05-c1` остаются историей со своей revision/source;
ничего не переименовывать в current. Смена критериев основана на явном
указании пользователя, не на объявлении прежних CLI попыток успешными.

Checkbox — единственный completion source coding task, не приёмка Testing
или Delivery. Модели ролей команды сохраняются по цели и не являются
требованием к USW. Новых model calls, probes и benchmarks не требуется.

## Workflow follow-up

- Критик проверяет `f05-c2`, fault proof, текстовый контракт и совместимость
  roots/task/evidence по design §5; отдельного runtime/реестра нет.
- Testing независимо читает инструкции, проверяет три случая, результат,
  exact ID, counter/соседнюю операцию и guards; пишет только собственное
  `testing-evidence.md`. Blocking finding открывает ту же task новой попыткой.
- После принятия кандидатуры назначенный писатель отдельно обновляет пакет.
  Новая рабочая сессия сверяет source/installed hashes и реально применяет USW
  в разрешённом temporary project. Не требуется специальный запуск модели.
- Перед final freeze выполнить main-spec sync и согласованные AUD-F05/index
  edits; уточнение цели также входит в source. Context/README не дублируют
  capability. После contract/source changes все обязательные проверки текущей
  revision/source выполняются заново; старые evidence/receipts сохраняются.
- Verify/sync/archive и коммит — по применимому workflow и отдельным
  назначениям после независимой приёмки. Другие changes и кандидаты не закрывать.
  Общая цель остаётся открытой.
