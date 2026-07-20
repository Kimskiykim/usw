## ADDED Requirements

### Requirement: Один владелец для каждого вида состояния исполнения
USW SHALL хранить завершение change-задач только в `tasks.md`, scope и
definition of done задачи — в `task.md`, прогресс шагов — в `plan.md`, факты
выполненной verification — в `evidence.md`, решения human review — в
неизменяемых review receipts, необязательную общую передачу — в task
`handoff.md`, а личную точку возобновления — в `.usw/HANDOFF.md`.

#### Scenario: Запись завершения шага plan
- **WHEN** шаг plan удовлетворяет своему условию завершения
- **THEN** изменяется только статус шага в `plan.md`, а checkbox change-задачи
  не отмечается автоматически

#### Scenario: Запись выполненной проверки
- **WHEN** verification command действительно выполнена
- **THEN** её command, source context, result и freshness записываются в
  `evidence.md`, а не выводятся из запланированной работы

### Requirement: Granular tasks имеют устойчивые контракты
Каждая исполнимая change-задача MUST иметь уникальный внутри change стабильный
ID, ссылку на `task.md`, явные scope и non-scope, dependencies, definition of
done и verification с ожидаемым наблюдением. Completion checkboxes MUST
находиться только в change `tasks.md`.

#### Scenario: Создание исполнимой задачи
- **WHEN** planning добавляет leaf task в `tasks.md`
- **THEN** запись ссылается на task directory, чей `task.md` содержит все
  обязательные поля контракта и не дублирует completion status

### Requirement: Завершение coding task ограничено ответственностью Development
Development MUST отмечать change-задачу выполненной только после выполнения её
definition of done, завершения `plan.md` и наличия актуального успешного
evidence для всех обязательных local checks. Checkbox MUST NOT означать
принятие human reviewer, Testing или Delivery.

#### Scenario: Проверка запланирована, но не выполнена
- **WHEN** implementation выглядит завершённой, но обязательная local
  verification не имеет выполненного результата
- **THEN** coding task остаётся незавершённой, а evidence показывает, что
  verification не запускалась

#### Scenario: Development завершён до Testing
- **WHEN** coding task удовлетворяет своему контракту и обязательным local checks
- **THEN** Development отмечает её выполненной, но работа всё ещё требует
  применимых human review, Testing и Delivery gates

### Requirement: Blocking finding повторно открывает исходную coding task
Если human review или Testing показывает, что отмеченная coding task не
удовлетворяет исходным scope, result или definition of done, Development MUST
изменить её checkbox с `[x]` на `[ ]`, выполнить repair и verification и только
затем отметить задачу снова. Независимый новый scope MUST стать новой задачей
только после подтверждения пользователя.

#### Scenario: Finding входит в исходный контракт
- **WHEN** reviewer фиксирует blocking finding против исходного `task.md`
- **THEN** та же coding task повторно открывается и получает repair без создания
  искусственной новой задачи

#### Scenario: Finding предлагает независимое улучшение
- **WHEN** предложение не требуется исходным контрактом задачи
- **THEN** текущая task не открывается повторно, а новый scope сначала
  предлагается пользователю

### Requirement: Replanning сохраняет факты
Replanning SHALL сохранять историю завершённых шагов и записанное evidence. Оно
MAY заменять pending steps и MUST помечать затронутое evidence как stale вместо
его удаления или переписывания при изменении source либо definition of done.

#### Scenario: Новый plan после частичного выполнения
- **WHEN** новый plan требуется после завершения части шагов
- **THEN** completed steps остаются записанными, pending steps могут быть
  заменены, а новый plan указывает, какое прежнее evidence остаётся актуальным

#### Scenario: Source изменился после успешной проверки
- **WHEN** изменение source инвалидирует ранее успешную verification
- **THEN** старый факт сохраняется со статусом stale, а task не может быть снова
  завершена до успешной проверки актуального source

### Requirement: Каждая попытка human review имеет неизменяемый receipt
USW MUST создавать новый reviewer-owned receipt для каждой попытки internal или
transition review под настроенным provider-neutral review root, по умолчанию
`usw/reviews/<subject-id>/<review-id>.md`. Receipt MUST содержать gate, reviewed
scope и identity, reviewer, verdict, timestamp и ссылки на findings и evidence,
не копируя каноническое содержимое.

#### Scenario: Reviewer принимает handoff
- **WHEN** reviewer принимает кандидата для следующей ответственности
- **THEN** создаётся новый accepted receipt, а handoff ссылается на него

#### Scenario: Кандидат изменился после review
- **WHEN** source или reviewed artifact identity изменились после accepted receipt
- **THEN** прежний receipt остаётся неизменным, но не разрешает новый handoff, и
  применимый gate выполняется новой попыткой

### Requirement: Personal и shared handoffs различаются
Task `handoff.md` MAY передавать общий task context и ссылку на применимый review
receipt, а `.usw/HANDOFF.md` SHALL содержать только developer-local resume state.
Ни один handoff MUST NOT дублировать specification, plan, evidence или review
content.

#### Scenario: Сохранение личной контрольной точки
- **WHEN** developer приостанавливает активную работу
- **THEN** `.usw/HANDOFF.md` ссылается на канонические общие артефакты и
  записывает одно следующее действие без копирования их содержимого
