## Контекст

USW уже поставляет команды и атомарные skills для инициализации, личного
handoff, поиска решений, планирования, объяснения и уточнения задач. Однако
инициализация создаёт общий workspace в форме OpenSpec, поэтому текущее
поведение противоречит продуктовой границе: standalone USW должен полностью
работать без OpenSpec, а OpenSpec должен оставаться явно выбранным provider
совместимости.

У общего workflow также нет единого runtime-контракта. Существуют templates для
части change- и task-артефактов, но отсутствуют общая конфигурация, orchestrator,
контракт flow scenario, устойчивый task contract и детерминированные правила
владения текущими операциями, evidence, review и Delivery. Решение должно работать через
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
- Сделать task attempts, текущие операции, evidence, review, completion и Delivery
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

`artifacts.root` является namespace root для planning-артефактов. При provider
`standalone` только `refinement.root`, `flows.root` и `reviews.root` могут быть
его proper descendants; такое ожидаемое containment не является конфликтом.
Эти три специализированных root должны быть различными и не могут совпадать,
содержать друг друга или находиться друг внутри друга. Любое другое равенство
либо ancestor/descendant overlap между managed roots является конфликтом.
Ни один managed root не может совпадать с project root, `.git` или локальным
`.usw` либо содержать эти области.

Defaults не зависят от наличия каталогов на диске. Для `standalone` используются
literal roots из примера выше. Для явно выбранного `openspec` default
`artifacts.root` равен `openspec`, а `refinement.root`, `flows.root` и
`reviews.root` остаются USW-owned путями `usw/refinements`, `usw/flows` и
`usw/reviews`. Изменение одного root не переназначает молча остальные
отсутствующие поля.

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
│   └── <subject-type>/<subject-path>/
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
            ├── development-evidence.md
            └── testing-evidence.md
```

У каждого вида состояния один authoritative artifact:

- `tasks.md` — текущее завершение coding tasks внутри change;
- `task.md` — стабильный contract revision и краткий Milestone log попыток;
- `development-evidence.md` — факты локальных проверок Development;
- `testing-evidence.md` — независимые проверки и findings Testing;
- `reviews/<subject-type>/<subject-path>/<review-id>.md` — неизменяемое решение одной попытки
  human review и общая запись перехода между ответственностями;
- `.usw/HANDOFF.md` — текущая личная точка возобновления и ограниченный
  табличный журнал сессии.

Каждый `task.md` явно объявляет `Artifact model: legacy|v1`. Все tasks,
существующие до завершения 2.1, получают метку `legacy` и сохраняют прежний
контракт без backfill evidence. Template после 2.1 создаёт только `v1` tasks.
Их `task.md` содержит sections Result, Scope, Non-scope, References,
Dependencies, Definition of done, Verification, Contract revision и Milestone
log. Contract identity не включает изменяемый Milestone log. В нём фиксируются
только границы attempt и значимые переходы таблицей
`Attempt | Trigger | Contract | Source | Outcome | References`. `tasks.md`
содержит activation task ID и исчерпывающий legacy allowlist. После завершения
2.1 allowlist immutable; любая новая task вне списка обязана быть v1. Validators
не выводят модель из отсутствующих файлов или Git history.

`.usw/HANDOFF.md` содержит metadata table
`Subject | Role | Attempt | Current operation | Status | Updated`, bounded Session journal
`Event | Operation | Status | Fact | Changed areas`, Verification, одно Next
action, References и trusted source snapshot с freshness. Operation означает
смысловую единицу текущей работы, а не каждую команду. Файл остаётся локальным,
перезаписываемым checkpoint и не является долговечной общей историей.
`Subject` является typed reference на refinement, change или task, поэтому
Analysis может сохранять checkpoint до появления granular task. `Role` называет
текущий flow и определяет применимые write authority и completion criteria.

Development и Testing пишут только свои evidence-файлы. Evidence entries имеют
стабильные IDs и связываются с contract revision и точной source identity.
Freshness не переписывается в role-owned evidence: consumer вычисляет current
или stale сравнением сохранённых identities с текущими. Поэтому смена source
может инвалидировать Testing evidence, не предоставляя Development право его
редактировать.

Source identity v1 является SHA-256 digest canonical manifest полного конечного
product tree в worktree и не содержит commit OID. Candidate включает текущее
состояние всех tracked product files после staged/unstaged changes и Git-visible
untracked files; deleted files отсутствуют. Поэтому workflow-only commit не
меняет identity.

Manifest начинается с ASCII `USW-SOURCE-V1\0`. Для каждого file path,
нормализованного в project-relative UTF-8 NFC с `/`, записываются
`uint32be(path length)`, path bytes, kind byte (`f`, `x` или `l`),
`uint64be(payload length)` и 32 raw bytes SHA-256 payload. Regular payload — raw
file bytes без line-ending normalization; symlink payload — raw link target.
Entries сортируются по unsigned path bytes, а normalization collision или
небезопасный path отклоняется. Source ID имеет форму
`usw-source-v1:<lowercase-hex-sha256(manifest-bytes)>`.
`.git`, `.usw` и все configured workflow artifact roots исключаются, поэтому
запись evidence, receipt или checkpoint не меняет product identity. Любое
изменение включённого product state создаёт новый digest, даже если оно не
связано с текущей задачей.

Receipt использует общие обязательные поля gate, owner role, reviewer, scope,
subject identity, reviewed artifact identities, previous attempt, verdict и
timestamp. Reviewed artifact identity — sorted project-relative path и SHA-256
raw bytes канонического planning artifact; изменение proposal, spec, design,
task или evidence делает прежний receipt неприменимым независимо от product
source identity.

Для v1 task receipt дополнительно обязательны artifact model, contract revision,
product source identity и evidence IDs. Для legacy task receipt обязательны
`Artifact model: legacy`, digest `task.md` как contract identity и ссылки на
фактически наблюдавшуюся verification; v1 Contract revision и evidence IDs не
требуются и не backfill-ятся. Для non-task review task-specific поля требуются
только когда применимы к reviewed scope.

`sender` и `receiver` обязательны только при `gate: transition`; internal review
не содержит их и не моделируется как передача ответственности. Transition
receipt является единственной общей записью перехода после отказа от task-level
`handoff.md`.

Subject key для review receipts является typed namespace: refinement использует
`refinement/<refinement-id>`, change — `change/<change-id>`, а task —
`task/<change-id>/<task-id>`. Эти segments образуют `subject-type/subject-path`
под review root и не могут конфликтовать между видами subject. Receipt ссылается
на канонические артефакты и не копирует их содержимое.

### Оркестрация только через явные flow scenarios

`usw-run-flow` читает выбранный `flow-scenario-*.md`. Каждый scenario объявляет
Purpose, Inputs, Ordered actions, Branches, Write authority, Stop conditions и
Outputs. Одно action вызывает один атомарный skill либо выполняет один переход
состояния артефакта. Порядок и ветвление определяет scenario, а не атомарный
skill.

Нормативные scenario templates поставляются package, но исполнимым источником
являются project-owned files под настроенным `flows.root`. После появления трёх
initial scenarios initializer аддитивно создаёт каждый отсутствующий scenario в
этом root и никогда не перезаписывает существующий файл. Повторная initialization
может добавить отсутствующий standard scenario, сохранив остальные byte-for-byte.
Orchestrator не использует package asset как скрытый runtime fallback: missing
project scenario является наблюдаемым invalid artifact state.

Orchestrator вызывает atomic capabilities через общий action-executor contract.
До вызова он проверяет наличие action и разрешённые artifact roles. После одного
вызова executor возвращает структурированный outcome: status, фактически
затронутые artifact roles, output references и, если применимо, blocker,
отсутствующее решение или permission boundary. Затем управление всегда
возвращается orchestrator. Недоступный action останавливает flow до mutation.

Задача orchestrator определяет этот interface и проверяет sequencing, branches,
authority и review orchestration на stub actions. Конкретные provider-aware
artifact/receipt, bounded execution и independent verification capabilities
реализуются следующим слоем и проходят отдельную integration-проверку против
того же contract. Orchestrator не создаёт receipts и не выполняет внутреннюю
логику atomic capability самостоятельно.

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

Все три группы реализуют action-executor contract `usw-run-flow`. До их
подключения orchestrator может быть проверен только на stub actions; это не
считается доступностью реальной lifecycle capability.

Provider-aware artifact capability сначала определяет единый adapter interface,
реализует standalone planning artifacts и provider-neutral immutable receipt
storage. Если выбран provider без подключённого adapter, capability возвращает
structured `unsupported_provider_operation` до записи и не создаёт standalone
fallback. OpenSpec compatibility task затем добавляет OpenSpec CLI adapter в тот
же interface; она не реализует второй receipt store и использует общий USW-owned
review root.

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
- не изменяет technical design, tasks, локальные операции, code, tests, evidence
  или Delivery;
- после internal review предлагает handoff, который принимает Development.

**Development:**

- начинает с канонических specs, готовности Analysis и выбранного пользователем
  scope;
- владеет technical `design.md`, `tasks.md`, granular `task.md`, текущими
  локальными operations, implementation changes, implementation-adjacent tests
  и `development-evidence.md`;
- не изменяет product proposal/specs и независимые Testing artifacts;
- отмечает coding task выполненной после её definition of done, завершённых
  применимых операций и успешных обязательных local checks;
- после internal review предлагает handoff, который принимает Testing.

**Testing:**

- начинает с нормативного product contract, выбранного scope, точной identity
  проверяемого source, готовности и evidence Development;
- владеет созданными им acceptance, integration, end-to-end и regression tests,
  своими findings и `testing-evidence.md`;
- может исправить ошибочный независимый check, не ослабляя requirement;
- не исправляет inspected implementation, product contract или Development
  artifacts;
- после internal review предлагает handoff, который принимает delivery owner.

Finding возвращается напрямую flow, владеющему затронутым артефактом:
specification finding — в Analysis, implementation или task-contract finding — в
Development, test-evidence finding — в Testing.

### OpenSpec frontier следует владению ролей

При provider `openspec` завершение роли не равно aggregate completion change.
Analysis создаёт `proposal` и capability `specs`, после чего может предложить
handoff, пока OpenSpec всё ещё сообщает незавершённый change: status артефакта
`design` равен `ready` (его разрешено создать, но `design.md` ещё отсутствует),
а status `tasks` равен `blocked`.

После принятия handoff Development отдельно запрашивает instructions для
`design`, создаёт technical `design.md` и повторно читает status. Нативный
artifact graph переводит `tasks` в `ready`; Development затем отдельно
запрашивает instructions и создаёт `tasks.md`. Role-oriented scenarios не
вызывают bundled `openspec-propose` через границу Analysis–Development.

Отклонённые альтернативы: provisional design от Analysis и custom OpenSpec
schema с role gates. Первая создаёт двух владельцев design, вторая преждевременно
расширяет пилот.

### Human review создаёт reviewer-owned receipt

Каждый internal review и transition review выполняется человеком. Internal
review проверяет результат внутри текущей ответственности. Transition review
принадлежит принимающей ответственности: Development принимает Analysis,
Testing принимает Development, а delivery owner принимает Testing.

Каждая попытка review создаёт новый неизменяемый
`reviews/<subject-type>/<subject-path>/<review-id>.md` со следующей информацией:

- тип gate и reviewed scope;
- subject identity и sorted identities всех reviewed artifacts;
- owner role;
- reviewer и его ответственность;
- verdict;
- ссылки на findings, applicable evidence либо legacy verification;
- applicable artifact model, contract/source identities, previous attempt или receipt;
- timestamp.

При transition review receipt дополнительно содержит sender и receiver. При
internal review эти поля отсутствуют; validator выбирает conditional rules по
gate.

Повторная проверка создаёт новый receipt. Старый receipt не переписывается и не
удаляется. Receipt является общей записью перехода и фиксирует human decision,
но не заменяет verification evidence и не превращает Review в отдельную роль
или автоматическую status machine.

При отклонении receiver не исправляет артефакты sender. Findings возвращаются
владельцу, тот выполняет repair и internal review, после чего создаётся новая
попытка transition review.

### Replanning сохраняет факты и консервативно инвалидирует evidence задачи

Replanning может заменить неподтверждённые или pending operations текущей
сессии, но не стирает task Milestone log, ранее выполненное evidence или
receipts. Изменение порядка локальных операций не меняет contract revision. Если
stable task contract, task source identity либо definition of done изменились,
всё Development и Testing evidence этой задачи остаётся записанным, но считается
stale. Все обязательные checks выполняются заново против актуальных contract
revision и source identity. В v1 не вычисляются частичные зависимости отдельных
evidence entries.

Если human review показывает, что уже отмеченная coding task не удовлетворяет
исходному `task.md`, Development меняет `[x]` обратно на `[ ]`, начинает новую
attempt, исправляет задачу, повторяет обязательные checks и снова отмечает её
выполненной. Старые evidence и receipts сохраняются, а Milestone log связывает
границы попыток; отдельный reopen status не добавляется. Независимый новый scope
становится новой задачей только после подтверждения пользователя.

После repair lifecycle возобновляется с самого раннего gate, чей контракт,
source identity или evidence стали неактуальны. Изменение task source identity
инвалидирует всё Development и Testing evidence задачи, поэтому обязательные
local checks, Testing и последующий transition review повторяются полностью.

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

Первый release-blocking target — точная версия OpenSpec `1.6.0`. Отдельная job
проверяет latest и показывает incompatibility, но не блокирует USW release.
Закреплённая версия меняется только намеренно вместе с успешным compatibility
evidence.

V1 содержит закрытый набор из двух встроенных adapters: `standalone` и
`openspec`. Общий adapter interface является внутренней границей реализации, а
не public extension API. Declarative path mapping и executable provider/plugin
API не входят в v1. Неизвестное config value отклоняется config validator с
`unsupported_provider`; валидный встроенный provider с отсутствующим adapter или
operation возвращает `unsupported_provider_operation` до записи без standalone
fallback. Расширение рассматривается отдельным change только после появления
второго реального внешнего provider consumer.

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
   validation прав записи. Явно пометить существующие leaf tasks active change
   как `legacy`, записать исчерпывающий allowlist в `tasks.md` и не создавать для
   них backfilled evidence. После завершения 2.1 allowlist не расширяется, а
   новые templates создают только `artifact model: v1` tasks.
3. Добавить три role scenarios и их structural validation.
4. Добавить `usw-run-flow`, provider-aware artifact capability, bounded
   execution и independent verification/evidence.
5. Согласовать существующие atomic skills с authority boundaries и упаковать
   refinement skill.
6. Добавить встроенный OpenSpec adapter и реальные pinned/latest compatibility jobs.
7. Обновить документацию и packaging после прохождения standalone и OpenSpec
   acceptance suites.

Rollback выполняется откатом новых commands, skills и default templates.
Созданные `usw/` artifacts и `usw.yaml` остаются обычными tracked files и не
удаляются автоматически; существующий `openspec/` не изменяется миграцией.

## Открытые вопросы

Нет открытых вопросов в текущем scope. Ретроактивная migration legacy tasks,
частичная dependency-aware invalidation evidence и внешний provider extension
contract намеренно отложены за пределы v1.
