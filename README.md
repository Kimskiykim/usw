# USW

USW — устанавливаемый самостоятельный workflow для Qwen Code и Codex.
OpenSpec поддерживается как явно выбранный compatibility provider, но не нужен
для стандартной установки и работы.

Первая команда харнеса инициализирует standalone USW в текущем проекте и сразу
создаёт:

```text
<project>/
├── .usw/
│   ├── .gitignore
│   └── HANDOFF.md
├── usw.yaml
└── usw/
    ├── changes/
    ├── templates/
    │   ├── change/
    │   │   ├── proposal.md
    │   │   ├── design.md
    │   │   ├── spec.md
    │   │   └── tasks.md
    │   ├── task/
    │   │   ├── task.md
    │   │   ├── development-evidence.md
    │   │   └── testing-evidence.md
    │   └── review/
    │       └── receipt.md
    ├── flows/
    │   └── examples/
    │       ├── analysis.md
    │       ├── development.md
    │       ├── testing.md
    │       ├── chat-review.md
    │       └── dev-test.md
    └── reviews/
```

`.usw/HANDOFF.md` создаётся как локальная точка входа разработчика для
возобновления работы и изначально сообщает, что активной работы нет.
`.usw/.gitignore` с `*` — удобный local default, а решение о tracking остаётся
за пользователем и не проверяется initializer-ом. `.usw/flows/` создаётся только
при первом local custom flow, а `.usw/refinements/` — при первом уточнении
намерения; `/usw-init` эти lazy directories не материализует. Пять flow
examples создаются только в shared `<flows.root>/examples/`.

`usw.yaml` версии 1 выбирает provider и project-relative roots. По умолчанию
используются `standalone`, `usw`, `usw/flows` и `usw/reviews`.
Инициализация аддитивна: существующие файлы не
перезаписываются. Небезопасные, пересекающиеся или symlinked roots отклоняются
до записи. Если поздняя I/O-ошибка оставила partial workspace, устраните причину
и повторите `/usw-init`: существующие bytes сохранятся, а отсутствующие
артефакты будут достроены.

В standalone-режиме `/usw-init` также материализует недостающие шаблоны
change, task, evidence и review-артефактов в `<artifacts.root>/templates/`.
Повторная инициализация не перезаписывает изменённые проектные шаблоны. В режиме
OpenSpec эти шаблоны не копируются в provider-owned `openspec/`.
При явно выбранном OpenSpec provider initializer создаёт только configured
flow/review roots, пять flow examples, `.usw/.gitignore` и
`.usw/HANDOFF.md`; `openspec/**` он не создаёт и не изменяет.

Для детерминированной инициализации skill сначала ищет Python 3.10+ под именем
`python3`, затем `python`. Если совместимого интерпретатора нет, он спрашивает
разрешение на менее детерминированный LLM fallback с тем же функциональным v1
contract, включая safe custom roots и оба provider. Ошибка уже найденного
Python-скрипта fallback не включает и всегда сообщается как есть.

Если рядом уже есть real `openspec/` directory, USW использует его только как
hint и не начинает writes только из-за detection. Явно заданный standalone
custom root под `openspec/**` остаётся пользовательским writable root; при
OpenSpec provider его provider-owned artifacts сохраняются byte-for-byte. Для
standalone USW показывает explicit opt-in; при уже выбранном OpenSpec provider
только подтверждает активный provider. Opt-in выглядит так:

```yaml
schema_version: 1
artifacts:
  provider: openspec
  root: openspec
```

OpenSpec adapter использует native artifact graph: Analysis владеет
`proposal/specs`, Development — `design/tasks`. Review receipts при любом
provider остаются в USW-owned `reviews.root` и только ссылаются на planning
artifacts.

## Lifecycle и артефакты

Инициализированные `analysis`, `development`, `testing`, `chat-review` и
`dev-test` — ненормативные примеры, а не автоматически активные flow. Runner не
исполняет их на месте. Скопируйте нужный файл из `<flows.root>/examples/` в
`<flows.root>/<name>.md`, адаптируйте под проект и только затем запускайте.
Analysis, Development и Testing показывают один возможный lifecycle
`Analysis → Development → Testing → Delivery`; конкретные gates, writes и
артефакты определяет скопированный project-owned flow.

`tasks.md` — единственный completion source, `task.md` хранит task contract и
milestones, `development-evidence.md` и `testing-evidence.md` имеют разных
writers, а каждый review attempt создаёт новый immutable receipt. Новые tasks
используют `Artifact model: v1`; явно зарегистрированные ранние tasks остаются
`legacy` без выдуманного evidence.

Product source identity — canonical `USW-SOURCE-V1` digest полного конечного
tracked/Git-visible untracked tree. `.git`, `.usw` и configured workflow roots
исключены: workflow-only запись или commit не инвалидирует evidence, изменение
product file инвалидирует.

Перед паузой сохраните только актуальное состояние работы:

```text
/usw-handoff
```

Команда сохраняет typed Subject, текущую Role/Attempt/Operation, actor, exact
executor, flow cursor, intent, declared writes, result, actual areas,
verification и ровно одно следующее действие. Это компактная локальная summary,
а не shared history или лог tool calls. Чтобы очистить завершённую работу,
вызовите:

```text
/usw-handoff finish
```

В новой сессии восстановите контекст и продолжите со следующего действия:

```text
/usw-resume
```

Resume сначала читает только summary. `in_progress` без result означает
возможное прерывание внутри executor и никогда не запускается повторно
автоматически. References открываются только при stale/unknown source,
failed/blocked outcome или явном запросе. Developer handoff не заменяет shared
task, evidence или review artifacts.

## Orchestration и Delivery

По умолчанию `usw-run-flow` принимает задачу и имя flow, ищет обычный
`<name>.md` сначала в `.usw/flows`, затем в shared `flows.root`, читает документ
целиком и следует описанному процессу. Версия, DSL, постоянные action names,
input map и normalized plan не требуются. Весь такой запуск является одной
HANDOFF begin/outcome boundary; неоднозначность возвращает
`decision_required`, а внешние действия сохраняют отдельные permissions.

`$usw-create-flow` также создаёт ordinary Markdown по умолчанию. Формат может
быть любым понятным человеку:

```markdown
# Проверка плана

1. Разбей задачу на небольшие шаги.
2. Проверь, что каждый шаг можно подтвердить отдельным тестом.
3. Покажи результат человеку.
```

Строгие версии `1` и `version-2` сохранены как эксперимент. Только явный
`--experimental-structured` включает parser, typed executors, gates, bounded
loops, parallel blocks и per-action cursor/checkpoint. Metadata внутри файла
сама по себе этот режим не включает. Action-specific binding в experiment
необязателен: общей задачи достаточно для старта.

В обоих режимах сохраняются безопасное разрешение путей, capability contracts,
HANDOFF и отдельные разрешения на commit, push, PR, deploy и release. Legacy
`.usw/FLOW.json` не объединяется и не удаляется автоматически.

Создание и первый запуск custom flow:

```text
$usw-create-flow Создай flow plan-check из проверки плана.
$usw-run-flow plan-check "Проверь текущий план"
```

Для создания `--local`/`-l` явно выбирает developer-local root. Для запуска без
origin selector local flow имеет приоритет над shared; `--local` и `--shared`
ограничивают поиск одним root:

```text
$usw-create-flow --local Создай flow personal-check из проверки плана.
$usw-run-flow personal-check "Проверь мой план"
```

Экспериментальный strict-запуск включается отдельно:

```text
$usw-create-flow --structured Создай flow review-gate.
$usw-run-flow --experimental-structured review-gate "Проверь изменение"
```

Live operation state реализован только Markdown-контрактами skills, templates и
commands: отдельный Python runtime, dependency или второй state-файл не добавлен.

Сквозной сценарий одного flow выглядит так:

```text
resolve Markdown → HANDOFF op-001/in_progress → executor
interruption → /usw-resume → explicit reconciliation (без retry)
outcome/completed → HANDOFF terminal outcome
/usw-handoff finish → idle
```

Delivery — терминальный контракт одного запуска: scope, tested source identity,
current evidence, unresolved non-blocking observations и delivery owner
(пользователь по умолчанию). Принятие Delivery не разрешает автоматически
commit, push, pull request, deployment или release — каждое внешнее действие
требует отдельного явного разрешения.

## Структурный брейншторм

Skill `usw-brainstorm-solutions` помогает разбирать запросы вида «как решить
эту задачу?». Для простых вопросов он использует короткий формат: задача,
проблема, предполагаемая причина, пути решения и первый шаг. Для сложных задач
добавляет контекст, ограничения и обоснованную рекомендацию. Он может
срабатывать автоматически или быть вызван явно:

```text
$usw-brainstorm-solutions Как сократить время ревью pull request?
```

## Декомпозиция на микротаски

Skill `usw-plan-small-steps` превращает большую спецификацию или выбранный
подход в небольшие исполняемые задачи. У каждой заранее есть результат,
критерий готовности и проверка с ожидаемым наблюдением. Skill не выполняет
задачи и не выбирает следующий scope: результат возвращается orchestrator.

```text
$usw-plan-small-steps Разбей миграцию API на микротаски.
```

## Итеративное уточнение намерения

Skill `usw-refine-intent` ведёт обсуждение в режиме опросника: разбирает один
decision case за ход, фиксирует подтверждённое решение и только затем переходит
к следующему. Локальная ненормативная сессия, журнал решений и необязательный
итог сохраняются в `.usw/refinements/<refinement-id>/`. Skill не создаёт
backlog, OpenSpec change, planning artifacts или executable tasks:

```text
$usw-refine-intent Давай по одному решению уточним идею этой задачи.
```

Это breaking rename без alias: установленный `usw-refine-task` удаляется при
`./install.sh --force`. Исторические `usw/refinements/` остаются нетронутыми.

## Перевод предложений агента

Skill `usw-explain-me` переводит план, рекомендацию, дифф, ошибку
или статус кодингового агента на выбранный уровень подробности: от «как для
хлебушка» до экспертного разбора. По умолчанию он подстраивается под запрос и
не начинает менять код:

```text
$usw-explain-me Объясни это как для хлебушка: <вставьте ответ агента>
```

## Qwen Code

Установите USW как Qwen extension:

```bash
qwen extensions install https://github.com/Kimskiykim/usw
```

После установки выполните в Qwen Code `/usw-init`, а затем используйте
`/usw-handoff` и `/usw-resume` для передачи состояния между локальными
сессиями:

```text
/usw-init
```

Для локальной разработки подключите текущий checkout:

```bash
qwen extensions link .
```

## Codex

Подключите marketplace и установите плагин:

```bash
codex plugin marketplace add Kimskiykim/usw
codex plugin add usw@usw
```

После установки откройте новую задачу и вызовите `/usw-init`. Команды
`/usw-handoff` и `/usw-resume` станут доступны после того же перезапуска:

```text
/usw-init
```

## Прямая установка

Для установки без extension/plugin manager клонируйте репозиторий и выполните:

```bash
./install.sh qwen
./install.sh codex
```

Без аргумента `./install.sh` установит command и skill для обоих агентов.
Установщик не перезаписывает существующие компоненты.

Чтобы явно обновить уже установленный skill из текущего checkout, выполните:

```bash
./install.sh codex --force
```

Для Qwen используйте `./install.sh qwen --force`, а для обоих агентов —
`./install.sh --force`.

## Разработка

Standalone suite не требует OpenSpec:

```bash
python3 -m unittest discover -s tests -v
```

Реальная compatibility suite устанавливает OpenSpec изолированно. Pinned
`1.6.0` блокирует release readiness; latest probe видим, но не блокирует:

```bash
./tests/run_openspec_compatibility.sh pinned
./tests/run_openspec_compatibility.sh latest
```
