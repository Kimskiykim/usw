# Идея конфигурируемого USW и внешних SDD providers

Статус: built-in профиль частично принят. `/usw-init` создаёт базовую
OpenSpec-совместимую структуру и поставляет встроенные Markdown-шаблоны.
Конфигурируемые schema, CLI contract и внешние adapters остаются отложенной
гипотезой до появления второго consumer с несовместимой структурой SDD.

## Контекст

USW должен работать самостоятельно с базовыми шаблонами, но не должен
навязывать проекту собственный способ формирования feature specification.
Проект или внешний harness может уже использовать другую SDD-модель, структуру
каталогов, шаблоны, lifecycle и команды.

USW должен уметь встроиться в такой процесс, сохранив собственные функции:

- локальное восстановление состояния разработчика;
- журнал локального выполнения;
- передача task или feature между ролями;
- ссылки на canonical specification, design, tasks, review и evidence.

## Проблема

Если USW жёстко предполагает конкретные пути вроде `SPEC.md`, `DESIGN.md` и
`TASKS.md`, он становится ещё одним конкурирующим SDD harness. Интеграция с
чужим процессом тогда требует копирования документов или изменения core.

Если разрешить полностью произвольные шаблоны без стабильного контракта, разные
интеграции будут называться USW-совместимыми, но не смогут одинаково разрешать
артефакты, строить handoff и проверять состояние.

Нужна граница, при которой внешний harness управляет формированием feature, а
USW работает со стабильными семантическими ролями артефактов.

## Цель

Сделать USW конфигурируемым и встраиваемым, чтобы он мог:

1. использовать встроенный набор базовых шаблонов;
2. создавать feature workspace из внешнего template pack;
3. подключаться к уже существующим артефактам другого SDD harness;
4. при необходимости делегировать discovery, initialization и validation
   внешнему provider adapter;
5. формировать handoff без знания конкретных имён файлов и структуры Markdown.

## Не цели первой версии

- универсальный движок всех возможных SDD lifecycle;
- автоматическое преобразование одного формата specification в другой;
- разбор произвольного Markdown по эвристическим заголовкам;
- выполнение произвольных shell hooks из template pack;
- принятие merge, release или delivery решений;
- обязательная миграция существующих feature в формат USW;
- стабильный публичный plugin API до появления реального второго consumer.

## Основной принцип

USW знает **роль артефакта**, но не предполагает его путь или внутренний формат.

Примеры базовых ролей:

```text
feature_spec
design
tasks
handoff
review
evidence
```

Core должен обращаться к ним через resolver:

```text
resolve(feature_spec) -> specs/F-123/spec.md
resolve(tasks)        -> specs/F-123/tasks.md
resolve(handoff)      -> specs/F-123/handoff.md
```

Core не должен содержать предположений вида:

```text
feature_dir / "SPEC.md"
найти заголовок "## Requirements"
```

## Граница ответственности

```text
SDD provider или template pack
    -> создаёт и структурирует feature artifacts
    -> сообщает их semantic roles

USW artifact resolver
    -> отображает semantic roles на реальные пути
    -> проверяет доступность обязательных artifacts

USW task handoff
    -> передаёт ответственность между ролями
    -> ссылается на canonical artifacts

USW local state
    -> помогает конкретному разработчику продолжить работу
    -> не является командным источником истины
```

## Два scope состояния

Предлагается сохранить явное разделение:

### Developer-local scope

```text
.usw/
├── HANDOFF.md
└── journal/
    └── <session-id>.jsonl
```

Этот scope игнорируется Git и принадлежит конкретной рабочей копии.

### Shared task scope

Расположение выбирает SDD provider. Встроенный профиль может использовать:

```text
usw/
└── tasks/
    └── <task-id>/
        └── HANDOFF.md
```

Task handoff передаётся между аналитиком, разработчиком, ревьюером и тестером.
Он ссылается на specification и другие canonical artifacts, но не копирует их.

## Режимы интеграции

### 1. Built-in

USW использует собственный минимальный template pack и самостоятельно создаёт
feature workspace.

```yaml
schema_version: 1

sdd:
  mode: managed
  provider: builtin
  template_pack: usw-default
```

Этот режим даёт рабочий default без внешнего harness.

### 2. External template pack

USW создаёт feature workspace, но берёт структуру и шаблоны из внешнего pack.

```yaml
schema_version: 1

sdd:
  mode: managed
  provider: template-pack
  template_pack: ./harness/sdd-pack
```

Этот режим подходит, если различаются пути, имена, состав документов и их
Markdown-шаблоны, но не требуется отдельная исполняемая логика.

### 3. External SDD provider

Внешний harness владеет созданием feature и lifecycle. USW только обнаруживает
и использует существующие artifacts.

```yaml
schema_version: 1

sdd:
  mode: external
  provider: company-sdd
```

Если достаточно статического отображения путей, provider может быть полностью
декларативным:

```yaml
sdd:
  mode: external
  provider: artifact-map
  artifacts:
    feature_spec: specs/{feature_id}/spec.md
    design: specs/{feature_id}/plan.md
    tasks: specs/{feature_id}/tasks.md
    handoff: specs/{feature_id}/handoff.md
```

Исполняемый adapter нужен только для собственного discovery, lifecycle или
validation.

## Черновик template pack manifest

```yaml
schema_version: 1
id: company-sdd
version: 1

artifacts:
  feature_spec:
    template: templates/feature.md
    path: features/{feature_id}/proposal.md
    required: true

  design:
    template: templates/architecture.md
    path: features/{feature_id}/design.md
    required: false

  tasks:
    template: templates/plan.md
    path: features/{feature_id}/tasks.md
    required: true

  handoff:
    template: templates/handoff.md
    path: features/{feature_id}/handoff.md
    required: true
```

Template pack получает только нормализованный контекст:

```yaml
feature_id: F-123
title: Add authentication
created_at: 2026-07-17T12:00:00Z
owner: developer-id
```

Набор переменных должен быть версионированным и небольшим. Отсутствующая
обязательная переменная является ошибкой до записи файлов.

## Черновик provider contract

Конкретный язык API пока не фиксируется. Семантический контракт может включать:

```text
discover_feature(project, selector) -> FeatureRef | not_found
initialize_feature(project, request) -> FeatureRef
resolve_artifact(feature, role) -> ArtifactRef | not_available
get_stage(feature) -> StageRef | unknown
validate(feature) -> ValidationResult
```

Все операции должны возвращать структурированный результат. Core не должен
зависеть от порядка элементов или разбора человекочитаемого stdout.

Для language-neutral интеграции предпочтителен CLI JSON contract:

```text
provider discover --project ... --feature F-123 --json
provider resolve --feature F-123 --role tasks --json
provider validate --feature F-123 --json
```

Исполняемый provider API следует добавлять только после пилота декларативного
artifact map на реальном внешнем harness.

## Конфигурация USW

Предлагаемый минимальный project config:

```yaml
schema_version: 1
profile: standalone

paths:
  local_state: .usw

features:
  local_handoff: true
  local_journal: true
  task_handoff: true

local:
  handoff_file: HANDOFF.md
  journal_pattern: journal/{session_id}.jsonl

sdd:
  mode: managed
  provider: builtin
  template_pack: usw-default
```

Предлагаемый порядок разрешения значений:

```text
built-in defaults
    < selected profile
    < project config
    < local override
    < explicit CLI arguments
```

CLI не должен дублировать каждое поле config отдельным флагом. Для начала
достаточно:

```text
usw init --profile standalone
usw init --config path/to/usw.yaml
usw init --config path/to/usw.yaml --json
```

Точное имя и расположение project config требуют отдельного решения. Shared
config должен быть доступен команде, а local override должен оставаться под
игнорируемым developer-local scope.

## Связь с task handoff

Task handoff использует semantic artifact map и не знает provider-specific
структуру:

```markdown
## Canonical artifacts

- Feature specification: `specs/F-123/spec.md`
- Design: `specs/F-123/plan.md`
- Tasks: `specs/F-123/tasks.md`
```

Минимальные semantic fields самого handoff остаются стабильными независимо от
SDD provider:

```text
task_id
stage
from
to
status
canonical_artifacts
evidence
risks
next_responsibility
```

Provider может добавлять extension fields, но не должен переопределять смысл
базовых полей.

## Валидация и безопасность

Первая версия должна соблюдать следующие ограничения:

- `schema_version` обязателен для config и manifest;
- относительные пути разрешаются от документированного корня;
- `..` и неявный выход за project root запрещены;
- конфликт двух artifact roles на одном writable path является ошибкой;
- существующие файлы не перезаписываются без явной политики;
- local state нельзя случайно объявить shared или tracked;
- template pack в первой версии содержит только данные и шаблоны;
- произвольные shell hooks не выполняются;
- USW не извлекает смысл из чужого Markdown эвристиками;
- provider validation отделена от USW acceptance;
- handoff не предоставляет merge или release authorization.

## Совместимость и fallback

USW должен различать три ситуации:

```text
required artifact missing  -> ошибка контракта
optional artifact missing  -> допустимое состояние
provider capability absent -> операция недоступна, но не симулируется
```

USW не должен молча создавать собственный `SPEC.md`, если внешний provider не
нашёл specification. Такой fallback может породить второй источник истины.

Built-in template pack используется только при явно выбранном built-in режиме.

## Предлагаемая последовательность микро-шагов

1. Согласовать semantic artifact roles и их минимальную семантику.
2. Согласовать границу built-in, template-pack и external режимов.
3. Зафиксировать минимальный versioned project config.
4. Вынести встроенные шаблоны в собственный `usw-default` pack.
5. Добавить декларативный artifact resolver без executable adapters.
6. Провести пилот с одним существующим внешним SDD harness.
7. Проверить, достаточно ли path mapping и template manifest.
8. Только при доказанной необходимости определить provider CLI/API.
9. Добавить structured JSON result для встраивания в другие harnesses.
10. Проверить второй consumer до объявления extension contract стабильным.

## Критерии успешного пилота

- standalone-проект работает только со встроенными шаблонами;
- внешний проект не копирует specification в формат USW;
- USW разрешает canonical artifacts по semantic roles;
- task handoff содержит корректные ссылки на provider-owned документы;
- смена template pack не требует изменения core;
- отсутствие optional artifacts обрабатывается явно;
- отсутствие required artifacts приводит к понятной ошибке;
- local developer state не попадает в Git;
- внешний provider не получает неявной merge или release authority;
- конфигурация остаётся небольшой и объяснимой.

## Основные риски

### Избыточная параметризация

Если конфиг начнёт описывать каждый заголовок и каждый шаг workflow, USW станет
нестабильным meta-harness. Настраивать следует paths, capabilities и provider,
а не внутреннюю семантику базового handoff.

### Несовместимые значения одной роли

Разные harnesses могут по-разному понимать `design` или `tasks`. Для каждой
базовой роли нужна короткая нормативная семантика, а специфичные роли должны
использовать namespaced extension identifiers.

### Дублирование authority

USW не должен превращать handoff в копию specification. Canonical requirements,
design и acceptance остаются у provider-owned artifacts.

### Преждевременный plugin API

Абстрактный provider API легко спроектировать под несуществующие сценарии.
Сначала нужно проверить декларативный mapping на реальном consumer.

## Вопросы для обсуждения

1. Какой минимальный набор semantic artifact roles обязателен для USW?
2. Должен ли `handoff` всегда принадлежать USW или может полностью
   предоставляться SDD provider?
3. Где хранить shared project config и как назвать его?
4. Нужны ли наследуемые profiles в первой версии или достаточно одного config?
5. Должен ли template pack уметь только создавать файлы или также валидировать
   их структуру?
6. Какой внешний SDD harness выбрать первым пилотным consumer?
7. Нужен ли language-neutral provider CLI сразу или только после пилота mapping?
8. Какие extension roles разрешить без изменения базовой schema?

## Предлагаемое ближайшее решение

До изменения runtime согласовать только четыре вещи:

1. USW не владеет способом формирования feature specification;
2. core работает с semantic artifact roles через resolver;
3. поддерживаются built-in, external template pack и external artifact-map
   режимы;
4. executable provider API откладывается до подтверждения необходимости на
   реальном втором consumer.
