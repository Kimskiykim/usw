## ADDED Requirements

### Requirement: Refinement сохраняет общее состояние
USW SHALL хранить каждую task-refinement session под настроенным refinement root:
`session.md` является текущим состоянием, `decisions.md` — authority решений, а
`outcome.md` — синтезированным согласованным итогом при готовности.

#### Scenario: Начало нового refinement
- **WHEN** пользователь начинает уточнять неоднозначную задачу и подходящей
  session ещё нет
- **THEN** USW создаёт стабильный refinement ID и начальные session/decision
  artifacts, не изменяя target code или change artifacts

#### Scenario: Возобновление refinement
- **WHEN** последующий ход находит session с теми же ID и goal
- **THEN** USW продолжает её current open case без восстановления решений из
  истории разговора

### Requirement: Один decision case за пользовательский ход
Active refinement SHALL обсуждать ровно один current decision case, предлагать
два или три разных варианта и задавать один вопрос, необходимый для решения.

#### Scenario: Current case не решён
- **WHEN** refinement показывает варианты current case
- **THEN** следующий case не показывается, а recommendation не записывается как
  user decision

### Requirement: Решения требуют подтверждения и сохраняют superseded history
USW MUST записывать decision только после однозначного ответа пользователя.
Заменённые decisions MUST оставаться в `decisions.md` со статусом `superseded` и
ссылкой на replacement.

#### Scenario: Пользователь подтверждает вариант
- **WHEN** пользователь однозначно выбирает представленный option
- **THEN** USW записывает stable decision ID, basis и consequences, закрывает
  current case и выбирает следующий open case

#### Scenario: Пользователь пересматривает решение
- **WHEN** пользователь заменяет ранее accepted decision
- **THEN** старое решение сохраняется как superseded, а новое указывает, что оно
  заменяет

### Requirement: Ready outcome актуален и переиспользуем
Когда все значимые cases решены, USW SHALL создать или обновить `outcome.md` с
current goal, agreed model, constraints, remaining unknowns, decision references
и одним recommended next flow и SHALL отметить session как ready.

#### Scenario: Завершение refinement
- **WHEN** каждый значимый decision case закрыт
- **THEN** `outcome.md` содержит только текущий согласованный результат и может
  служить входом change planning без чтения истории разговора

### Requirement: Refinement не реализует target work
Refinement capability MUST NOT изменять product code или target change artifacts,
пока после refinement не начат отдельный явно разрешённый flow.

#### Scenario: Outcome стал ready
- **WHEN** refinement завершается recommended change-planning flow
- **THEN** он возвращает пути артефактов и останавливается до создания или
  применения change
