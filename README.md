# USW

USW — устанавливаемый самостоятельный workflow для Qwen Code и Codex.
OpenSpec поддерживается как явно выбранный compatibility provider, но не нужен
для стандартной установки и работы.

Первая команда харнеса инициализирует USW в текущем проекте и создаёт:

```text
<project>/
├── .usw/
│   ├── .gitignore
│   ├── HANDOFF.md
│   ├── flows/        # создаётся для local custom flows
│   └── refinements/  # создаётся при первом уточнении намерения
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
    │   ├── flow-scenario-analysis.md
    │   ├── flow-scenario-development.md
    │   └── flow-scenario-testing.md
    └── reviews/
```

`.usw/HANDOFF.md` создаётся как локальная точка входа разработчика для
возобновления работы и изначально сообщает, что активной работы нет. Содержимое
`.usw/` игнорируется Git и не становится общим артефактом команды или
репозитория. Личные и экспериментальные custom flows можно явно хранить в
`.usw/flows/`; стандартные role flows остаются только в shared `flows.root`.

`usw.yaml` версии 1 выбирает provider и project-relative roots. По умолчанию
используются `standalone`, `usw`, `usw/flows` и `usw/reviews`.
Инициализация аддитивна: существующие файлы не
перезаписываются. Небезопасные, пересекающиеся или symlinked roots отклоняются
до записи.

Legacy-ключ `refinement.root` принимается только для точной диагностики и не
управляет новыми сессиями. Существующие shared refinements сохраняются без
автоматического переноса; их импорт требует отдельного явного решения.

В standalone-режиме `/usw-init` также материализует недостающие шаблоны
change, task, evidence и review-артефактов в `<artifacts.root>/templates/`.
Повторная инициализация не перезаписывает изменённые проектные шаблоны. В режиме
OpenSpec эти шаблоны не копируются в provider-owned `openspec/`.

Для детерминированной инициализации skill сначала ищет Python 3.10+ под именем
`python3`, затем `python`. Если совместимого интерпретатора нет, он спрашивает
разрешение на ограниченный LLM fallback для default standalone-layout. Ошибка
уже найденного Python-скрипта fallback не включает и всегда сообщается как есть.

Если рядом уже есть `openspec/`, USW только сообщает об этом и сохраняет его
byte-for-byte. Явный opt-in выглядит так:

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

Три project-owned scenario образуют lifecycle
`Analysis → Development → Testing → Delivery`. Review — human gate, а не
четвёртый flow. Internal review сохраняет owner role без передачи
ответственности; transition review принадлежит принимающей стороне и записывает
sender/receiver. Rejection возвращается владельцу затронутого артефакта.

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

`usw-run-flow` валидирует выбранный project scenario, требует явный scope при
неоднозначности и проверяет write authority до mutation. После preflight он
сохраняет в HANDOFF `in_progress`, читает запись обратно и только затем вызывает
один executor. Outcome записывается до выбора следующего шага. Недоступная
capability, blocker, user decision, permission boundary, write mismatch или
local-state boundary останавливают flow наблюдаемо.

Помимо стандартных role scenarios можно создать линейный custom flow в
`<flows.root>/<name>.md`. Skill `$usw-create-flow` собирает и валидирует такой
документ, а `$usw-run-flow <name>` исполняет его. Исполняемая часть остаётся
обычным Markdown:

```markdown
## Контракт

- Версия: `1`

## Порядок действий

1. Скилл: `usw-plan-small-steps`
2. Скрипт: `scripts/check_plan`
   - Аргументы: `--strict`
```

Runner проверяет весь документ до первого шага, выполняет один skill или script
за раз, берёт write-contract skill из executor, не использует shell-строки и
продвигает HANDOFF cursor только после `completed`. Старая форма с `Пишет` и
разделом полномочий записи также поддерживается. Другой status сохраняет outcome
на том же шаге и останавливает цепочку. Другой flow/scope блокируется до resume
либо `/usw-handoff finish`. Legacy `.usw/FLOW.json` не объединяется и не
удаляется автоматически. Custom flows не поддерживают branches и циклы;
стандартные role flows не меняются.

Создание и первый запуск custom flow:

```text
$usw-create-flow Создай flow plan-check из проверки плана и локального скрипта.
$usw-run-flow plan-check
```

Флаги `--local` и `-l` явно выбирают developer-local root `.usw/flows` для
обеих операций. Без флага сохраняется shared `flows.root`; автоматического
поиска или shadowing между roots нет:

```text
$usw-create-flow --local Создай flow personal-check из проверки плана.
$usw-run-flow -l personal-check
```

Live operation state реализован только Markdown-контрактами skills, templates и
commands: отдельный Python runtime, dependency или второй state-файл не добавлен.

Сквозной сценарий одного flow выглядит так:

```text
preflight → HANDOFF op-001/in_progress → executor
interruption → /usw-resume → explicit reconciliation (без retry)
outcome/completed → HANDOFF cursor на следующий step
последний outcome → /usw-handoff finish → idle
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
