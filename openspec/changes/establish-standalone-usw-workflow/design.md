## Контекст

USW уже поставляет команды и атомарные skills для инициализации, личного
handoff, поиска решений, планирования, объяснения и уточнения задач. Однако
инициализация создаёт общий workspace в форме OpenSpec, поэтому текущее
поведение противоречит продуктовой границе: standalone USW должен полностью
работать без OpenSpec, а OpenSpec должен оставаться явно выбранным provider
совместимости.

У общего workflow также нет единого runtime-контракта. Существуют templates для
части change- и task-артефактов, но отсутствуют общая конфигурация, orchestrator,
контракт flow scenario, единый step plan и детерминированные правила владения
состоянием, evidence, review и Delivery. Решение должно работать через
model-led skills и простые Python scripts без отдельного USW service или базы
данных.

## Цели / Не-цели

**Цели:**

- Сделать standalone USW безопасным версионированным режимом по умолчанию.
- Хранить общие workflow-артефакты под настроенными project-relative roots, а
  личное состояние возобновления — в игнорируемом `.usw/`.
- Сделать оркестрацию явной и проверяемой, не передавая атомарным skills скрытые
  полномочия выбирать следующий skill.
- Разделить ответственность Analysis, Development и Testing, сохранив общий
  lifecycle, канонические артефакты и human review gates.
- Сделать task progress, evidence, review, completion, handoff и Delivery
  однозначными и возобновляемыми.
- Поддерживать OpenSpec как явно выбранный provider и проверять совместимость с
  реальной установкой.

**Не-цели:**

- Публичный plugin API или произвольные сторонние provider adapters.
- Произвольные template packs, эвристический разбор чужого Markdown и
  преобразование форматов артефактов.
- Параллельное владение одной ролью несколькими разработчиками и автоматическая
  координация параллельных агентов.
- Постоянная организационная Delivery policy, deployment или release automation.
- Автоматическая миграция или перезапись существующего OpenSpec workspace.

## Решения

### Небольшая версионированная общая конфигурация

В корне проекта используется `usw.yaml` с контрактом v1:

```yaml
schema_version: 1
artifacts:
  provider: standalone
  root: usw
refinement:
  root: usw/refinements
flows:
  root: usw/flows
reviews:
  root: usw/reviews
```

Все roots являются project-relative путями через реальные каталоги. Absolute
paths, `..`, переход через symlink, неподдерживаемая версия схемы и конфликтующие
writable roots отклоняются до записи любого managed file. Отсутствующие
необязательные roots выводятся из defaults выбранного provider. Неизвестные
поля сохраняются model-led consumers, но не меняют смысл полей v1.

Review root является provider-neutral общей областью. Он остаётся USW-owned
даже при `artifacts.provider: openspec`, поэтому review receipts могут ссылаться
на OpenSpec-артефакты, не изменяя и не дублируя их.

Отклонённая альтернатива: выводить provider из наличия `openspec/`. Появление
каталога тогда молча меняло бы поведение проекта.

### Standalone-инициализация без неявного принятия OpenSpec

`/usw-init` создаёт отсутствующие standalone-конфигурацию и общие каталоги, а
также игнорируемый `.usw/HANDOFF.md`. Операция остаётся additive и отклоняет
небезопасные пути или tracked personal state. Если `openspec/` уже существует,
инициализация сообщает о нём и объясняет явный opt-in, но не изменяет его и не
выбирает OpenSpec provider.

Отклонённая альтернатива: оставить OpenSpec режимом по умолчанию ради обратной
совместимости. Это сохраняло бы необъявленную runtime dependency.

### Детерминированный standalone layout

Общие standalone-артефакты используют следующую структуру:

```text
usw/
├── flows/
│   ├── flow-scenario-analysis.md
│   ├── flow-scenario-development.md
│   └── flow-scenario-testing.md
├── reviews/
│   └── <subject-id>/
│       └── <review-id>.md
├── refinements/
│   └── <refinement-id>/...
└── changes/
    └── <change-id>/
        ├── proposal.md
        ├── design.md
        ├── specs/<capability>/spec.md
        ├── tasks.md
        └── tasks/<task-id>-<slug>/
            ├── task.md
            ├── plan.md
            ├── evidence.md
            └── handoff.md
```

У каждого вида состояния один authoritative artifact:

- `tasks.md` — текущее завершение coding tasks внутри change;
- `task.md` — scope, non-scope, dependencies и definition of done задачи;
- `plan.md` — прогресс исполнимых шагов;
- `evidence.md` — факты выполненных проверок и их актуальность;
- `reviews/<subject-id>/<review-id>.md` — неизменяемое решение одной попытки
  human review;
- task `handoff.md` — необязательная общая передача контекста и ссылки;
- `.usw/HANDOFF.md` — личная локальная точка возобновления.

Subject IDs для review receipts должны быть стабильными и не конфликтовать
между refinement, change и task. Receipt ссылается на канонические артефакты и
не копирует их содержимое.

### Оркестрация только через явные flow scenarios

`usw-run-flow` читает выбранный `flow-scenario-*.md`. Каждый scenario объявляет
Purpose, Inputs, Ordered actions, Branches, Write authority, Stop conditions и
Outputs. Одно action вызывает один атомарный skill либо выполняет один переход
состояния артефакта. Порядок и ветвление определяет scenario, а не атомарный
skill.

Начальный набор содержит ровно три role scenarios: Analysis, Development и
Testing. Review не является четвёртым flow; internal review и transition review
являются gate actions внутри scenarios. Delivery является терминальным
переходом.

На уровне всего work item действует macro lifecycle:

```text
Analysis → Development → Testing → Delivery
```

Каждый role scenario использует общий управляющий shell: проверить входы,
восстановить контекст, подтвердить scope, выполнить разрешённые role actions,
провести internal review, предложить handoff, пройти transition review
принимающей стороны либо вернуть findings владельцу артефакта.

Если запрос на продолжение не указывает step, task или change, orchestrator
показывает все допустимые scopes и ждёт выбора пользователя. Рекомендуемый scope
не считается автоматически разрешённым.

Отклонённая альтернатива: позволить skills самостоятельно вызывать следующий
skill. Это скрывает полномочия и создаёт циклическую связанность.

### Capability-oriented набор skills

Orchestrator переиспользует существующие атомарные capabilities:

- `usw-brainstorm-solutions`;
- `usw-refine-task`;
- `usw-plan-small-steps`;
- `usw-manage-handoff`.

Добавляются только три отсутствующие атомарные capability-группы:

- provider-aware создание и обновление разрешённых planning artifacts;
- bounded execution выбранного scope с локальной проверкой;
- независимая verification с findings и evidence.

`usw-initialize-project` и `usw-explain-me` остаются utility entrypoints вне
role lifecycle. Отдельный lifecycle stage получает собственный skill только
если практическая реализация доказывает, что это независимо переиспользуемая
capability.

### Роли — границы ответственности, а не личности агентов

Один человек или агент может последовательно выполнять разные role flows, но
при переключении меняются разрешённые writes, owned artifacts, входной контракт
и критерии завершения.

**Analysis:**

- принимает raw intent или возврат с каноническими ссылками и findings;
- владеет feature backlog, refinement state, `proposal.md` и нормативными
  capability specs;
- уточняет intent и done criteria, собирает project context, выбирает подход,
  оценивает сложность спецификации и предлагает декомпозицию;
- не изменяет technical design, tasks, plans, code, tests, evidence или Delivery;
- после internal review предлагает handoff, который принимает Development.

**Development:**

- начинает с канонических specs, готовности Analysis и выбранного пользователем
  scope;
- владеет technical `design.md`, `tasks.md`, granular `task.md`, `plan.md`,
  implementation changes, implementation-adjacent tests, своими evidence entries
  и development handoff;
- не изменяет product proposal/specs и независимые Testing artifacts;
- отмечает coding task выполненной после её definition of done, завершённого
  plan и успешных обязательных local checks;
- после internal review предлагает handoff, который принимает Testing.

**Testing:**

- начинает с нормативного product contract, выбранного scope, точной identity
  проверяемого source, готовности и evidence Development;
- владеет созданными им acceptance, integration, end-to-end и regression tests,
  своими findings, evidence и handoff;
- может исправить ошибочный независимый check, не ослабляя requirement;
- не исправляет inspected implementation, product contract или Development
  artifacts;
- после internal review предлагает handoff, который принимает delivery owner.

Finding возвращается напрямую flow, владеющему затронутым артефактом:
specification finding — в Analysis, implementation или plan finding — в
Development, test-evidence finding — в Testing.

### OpenSpec frontier следует владению ролей

При provider `openspec` завершение роли не равно aggregate completion change.
Analysis создаёт `proposal` и capability `specs`, после чего может предложить
handoff, пока OpenSpec всё ещё сообщает незавершённый change, `design` готов к
созданию, а `tasks` заблокирован.

После принятия handoff Development создаёт technical `design`; нативный
artifact graph затем разблокирует `tasks`, которые также создаёт Development.
Role-oriented scenarios запрашивают OpenSpec instructions по одному artifact и
не вызывают bundled `openspec-propose` через границу Analysis–Development.

Отклонённые альтернативы: provisional design от Analysis и custom OpenSpec
schema с role gates. Первая создаёт двух владельцев design, вторая преждевременно
расширяет пилот.

### Human review создаёт reviewer-owned receipt

Каждый internal review и transition review выполняется человеком. Internal
review проверяет результат внутри текущей ответственности. Transition review
принадлежит принимающей ответственности: Development принимает Analysis,
Testing принимает Development, а delivery owner принимает Testing.

Каждая попытка review создаёт новый неизменяемый
`reviews/<subject-id>/<review-id>.md` со следующей информацией:

- тип gate и reviewed scope;
- точная identity source или артефактов;
- reviewer и его ответственность;
- verdict;
- ссылки на findings и актуальное evidence;
- timestamp.

Повторная проверка создаёт новый receipt. Старый receipt не переписывается и не
удаляется. Handoff ссылается на применимый accepted receipt. Receipt фиксирует
human decision, но не заменяет verification evidence и не превращает Review в
отдельную роль или автоматическую status machine.

При отклонении receiver не исправляет артефакты sender. Findings возвращаются
владельцу, тот выполняет repair и internal review, после чего создаётся новая
попытка transition review.

### Replanning сохраняет факты и инвалидирует только затронутые claims

Replanning может заменить pending steps и добавить новые, но не стирает историю
completed steps или ранее выполненное evidence. Если source либо definition of
done изменились, затронутое evidence остаётся записанным со статусом stale, а в
plan добавляется новая обязательная verification.

Если human review показывает, что уже отмеченная coding task не удовлетворяет
исходному `task.md`, Development меняет `[x]` обратно на `[ ]`, исправляет
задачу, повторяет обязательные checks и снова отмечает её выполненной. Git
history и review receipts сохраняют хронологию; отдельный reopen status не
добавляется. Независимый новый scope становится новой задачей только после
подтверждения пользователя.

После repair lifecycle возобновляется с самого раннего gate, чей контракт,
source identity или evidence стали неактуальны. Изменение code обычно требует
повторного Testing и последующего transition review; незатронутое evidence
остаётся актуальным.

### Delivery использует per-run контракт

Перед терминальным переходом flow фиксирует в текущем контексте:

- выбранный delivery scope;
- точную identity протестированного source;
- актуальное evidence;
- нерешённые non-blocking observations;
- delivery owner данного запуска.

Пользователь является delivery owner по умолчанию и может явно делегировать эту
ответственность. Принятие Testing handoff подтверждает только названного
кандидата и передачу ответственности. Оно не разрешает commit, push, pull
request, deployment, release или другое внешнее действие — каждое требует
отдельной явной авторизации.

Testing success без принятого terminal handoff не означает Delivery. Flow
останавливается с готовыми candidate и evidence для названного owner.

### OpenSpec остаётся опциональным и проверяется воспроизводимо

`artifacts.provider: openspec` выбирается явно. Compatibility layer сопоставляет
семантические роли USW с реальным OpenSpec workspace и сообщает об отсутствующей
required capability вместо создания standalone-дубликатов. OpenSpec
устанавливается только в development и CI compatibility environments.

Одна явно записанная версия OpenSpec является release-blocking. Отдельная job
проверяет latest и показывает incompatibility, но не блокирует USW release.
Закреплённая версия меняется только намеренно вместе с успешным compatibility
evidence.

## Риски / Компромиссы

- [Новый standalone default удивит существующих пользователей] → Обнаруживать
  `openspec/`, сохранять его byte-for-byte, показывать migration hint и требовать
  явный provider opt-in.
- [YAML превратится в общий configuration framework] → Ограничить v1 и
  отклонять неподдерживаемую семантику вместо generic hooks.
- [Flow Markdown останется неоднозначным] → Требовать нормативные sections и
  валидировать структуру scenario до запуска actions.
- [Права на артефакты будут только декларативными] → Проверять write authority
  перед каждой записью и покрыть ownership contract tests.
- [Review receipts начнут копировать evidence или requirements] → Разрешить в
  receipts только identity, verdict и ссылки на канонические источники.
- [Accepted receipt применят к изменённому кандидату] → Связывать receipt с
  точной source/artifact identity и повторять gate после инвалидирующего change.
- [Delivery воспримут как разрешение публикации] → Явно отделить terminal
  acceptance от commit, push, PR, deployment и release authority.
- [Latest OpenSpec failures будут игнорироваться] → Оставить job видимой,
  сохранять tested version и требовать triage при обновлении pinned version.
- [Change слишком широк] → Реализовывать dependency-ordered granular tasks с
  собственными definition of done и verification evidence.

## План миграции

1. Добавить v1 configuration contract и additive standalone initializer,
   сохранив существующие OpenSpec directories.
2. Добавить standalone templates, provider-neutral review collection и
   validation прав записи.
3. Добавить три role scenarios и их structural validation.
4. Добавить `usw-run-flow`, provider-aware artifact capability, bounded
   execution и independent verification/evidence.
5. Согласовать существующие atomic skills с authority boundaries и упаковать
   refinement skill.
6. Добавить явное OpenSpec mapping и реальные pinned/latest compatibility jobs.
7. Обновить документацию и packaging после прохождения standalone и OpenSpec
   acceptance suites.

Rollback выполняется откатом новых commands, skills и default templates.
Созданные `usw/` artifacts и `usw.yaml` остаются обычными tracked files и не
удаляются автоматически; существующий `openspec/` не изменяется миграцией.

## Открытые вопросы

- Какая конкретная версия OpenSpec станет первым pinned compatibility target;
  она выбирается в задаче реализации test fixture и записывается в test config.
- Точная нормативная Markdown-форма flow scenario и review receipt при
  сохранении уже принятых обязательных полей.
- Точный алгоритм определения stale evidence при сложных изменениях source или
  definition of done.
- Нужен ли в будущем внешний declarative path mapping или executable adapter;
  решение отложено до появления второго реального consumer.
