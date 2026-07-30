# USW

USW — устанавливаемый самостоятельный workflow для Qwen Code и Codex.

Первая команда харнеса инициализирует standalone USW в текущем проекте и сразу
создаёт:

```text
<project>/
├── .usw/
│   ├── .gitignore
│   └── HANDOFF.md
├── usw.yaml
└── usw/
    └── flows/
        └── examples/
            ├── chat-review.md
            └── dev-test.md
```

При effective `handoff: true` `.usw/HANDOFF.md` создаётся как локальная точка
входа разработчика для возобновления работы и изначально сообщает, что активной
работы нет. При `handoff: false` initializer и runtime не читают, не проверяют
и не изменяют этот файл.
`.usw/.gitignore` с `*` — удобный local default, а решение о tracking остаётся
за пользователем и не проверяется initializer-ом. `.usw/flows/` создаётся только
при первом local custom flow, а `.usw/refinements/` — при первом уточнении
намерения; `/usw-init` эти lazy directories не материализует. Два flow
examples создаются только в shared `<flows.root>/examples/`.

`usw.yaml` версии 1 выбирает project-relative roots и optional top-level
`handoff: true|false`. Отсутствующее поле означает `true`. По умолчанию
используются `usw`, `usw/flows` и `usw/reviews`.
Инициализация аддитивна: существующие файлы не
перезаписываются. Небезопасные, пересекающиеся или symlinked roots отклоняются
до записи. Если поздняя I/O-ошибка оставила partial workspace, устраните причину
и повторите `/usw-init`: существующие bytes сохранятся, а отсутствующие
артефакты будут достроены.

`/usw-init` не создаёт `changes/`, `reviews/` и `templates/` заранее. Точный
artifact destination создаёт использующий его flow только при необходимости.

Для детерминированной инициализации skill сначала ищет Python 3.10+ под именем
`python3`, затем `python`. Если совместимого интерпретатора нет, он спрашивает
разрешение на менее детерминированный LLM fallback с тем же функциональным v1
contract, включая safe custom roots. Ошибка уже найденного
Python-скрипта fallback не включает и всегда сообщается как есть.

## Lifecycle и артефакты

Инициализированные `chat-review` и `dev-test` — ненормативные примеры, а не
автоматически активные flow. Runner не исполняет их на месте. Скопируйте нужный
файл из `<flows.root>/examples/` в `<flows.root>/<name>.md`, адаптируйте под
проект и только затем запускайте. Конкретные gates, writes и артефакты
определяет скопированный project-owned flow.

`tasks.md` — единственный completion source, `task.md` хранит task contract и
milestones, `development-evidence.md` и `testing-evidence.md` имеют разных
writers, а каждый review attempt создаёт новый immutable receipt. Новые tasks
используют `Artifact model: v1`; явно зарегистрированные ранние tasks остаются
`legacy` без выдуманного evidence.

Product source identity — canonical `USW-SOURCE-V1` digest полного конечного
tracked/Git-visible untracked tree. `.git`, `.usw` и configured workflow roots
исключены: workflow-only запись или commit не инвалидирует evidence, изменение
product file инвалидирует.

При включённом handoff перед паузой сохраните только актуальное состояние:

```text
/usw-handoff
```

Команда сохраняет flow, origin, identity, input digest, status, выполненное,
narrative current position, blocker, проверки, references и ровно одно следующее
действие. Это компактная локальная summary, а не machine cursor, shared history
или лог tool calls. Чтобы очистить завершённую работу, вызовите:

```text
/usw-handoff finish
```

В новой сессии восстановите контекст:

```text
/usw-resume
```

`in_progress` означает возможное прерывание и никогда не запускается повторно
автоматически. `in_progress`, `paused`, `blocked` и `decision_required`
блокируют новый flow до explicit finish. `completed` и `failed` остаются
доступны для inspect, но следующий Begin атомарно заменяет их новой operation,
поэтому ручной finish между завершёнными flow не нужен. Каждый Begin добавляет
уникальный invocation token, поэтому даже одинаковые flow/input получают разные
operation ID. Outcome обязан предъявить exact ID, возвращённый Begin; stale
writer не может перезаписать более новую operation. Handoff transitions
сериализуются без отдельного state-файла.
Старый role-based HANDOFF можно прочитать для recovery или очистить через
finish; он не мигрируется и не получает generic Outcome.

## Text-first execution

`usw-run-flow` принимает input и имя flow, ищет `<name>.md` сначала в
`.usw/flows`, затем в shared `flows.root`, читает документ ровно один раз и
передаёт модели exact Markdown вместе с исходным input. Identity вычисляется из
тех же bytes. Версия, DSL, action names, bindings и normalized plan не
требуются. Metadata внутри файла никогда не переключает execution mode.

`$usw-create-flow` создаёт ordinary Markdown по умолчанию. Формат может быть
любым понятным человеку:

```markdown
# Проверка плана

1. Разбей задачу на небольшие шаги.
2. Проверь, что каждый шаг можно подтвердить отдельным тестом.
3. Покажи результат человеку.
```

`$usw-create-flow --structured` создаёт человекочитаемый `version-2`.
`CALL`, `GATE`, `LOOP` и `PARALLEL` помогают описать процесс, но не включают
parser и не обещают deterministic transitions, atomic parallelism или durable
cursor. При существенной неоднозначности модель возвращает
`decision_required`.

Flow text не предоставляет полномочия. Commit, push, PR, deploy, release,
destructive и другие внешние действия используют обычные permission boundaries.

Создание и запуск custom flow:

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

Structured authoring запускается тем же обычным путём:

```text
$usw-create-flow --structured Создай flow review-gate.
$usw-run-flow review-gate "Проверь изменение"
```

`--experimental-structured` и внутренние команды `validate`, `run-script`,
`checkpoint-save`, `checkpoint-resume` сняты. Старый вызов останавливается до
mutation и предлагает повторить run без flag.

Existing `.usw/FLOW.json` не читается, не изменяется и не удаляется. При его
наличии показывается одно предупреждение за invocation, после чего text flow
может продолжиться.

```text
resolve exact Markdown bytes → optional HANDOFF/in_progress → model
pause or decision → generic HANDOFF outcome (без automatic retry)
completed → HANDOFF/completed
/usw-handoff finish → idle
```

Снятый parser, typed runtime, JSON checkpoints, специализированные тесты и два
superseded change-пакета сохранены в `research/structured-runtime/`. Они не
устанавливаются и не входят в normative specs или основной test discovery.

Ненормативный roadmap:

```text
text flow → compiler → derived machine flow → durable state → iterator
```

Compiler и iterator появятся только в отдельном change с измеримой потребностью
в machine guarantees.

## Разовая маршрутизация задачи

`usw-route-task` — явный opt-in для одной задачи. Skill оценивает, нужен ли
отдельный процесс, ищет подходящий local/shared flow и packaged examples, а при
необходимости готовит новый или адаптированный flow:

```text
$usw-route-task "Разбери сложный flaky test и подготовь исправление"
```

Для простой задачи skill только рекомендует прямое выполнение и
останавливается. Для сложной задачи он показывает полный flow, обоснование,
origin и будущий путь, затем ждёт подтверждения. До подтверждения flow и
HANDOFF не изменяются.

После подтверждения exact match запускается через `usw-run-flow`. Новый или
адаптированный flow сначала сохраняется через `usw-create-flow`, затем
запускается с исходной задачей. Project-specific flow сохраняется в shared
root, личный, экспериментальный или неоднозначный — в `.usw/flows`.

Маршрутизация не ищет flow в интернете или других проектах, не включается
неявно и не действует на следующие задачи. Подтверждение flow не предоставляет
дополнительных полномочий на commit, push, PR, deploy, release или destructive
actions.

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
backlog, planning change, planning artifacts или executable tasks:

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
сессиями. Для жёсткого read-only ревью LLM-кода доступна команда
`/usw-reviewer-llm-critic [scope]`:

```text
/usw-init
/usw-reviewer-llm-critic Scope: текущий diff
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
`/usw-handoff`, `/usw-resume` и `/usw-reviewer-llm-critic` станут доступны
после того же перезапуска:

```text
/usw-init
/usw-reviewer-llm-critic Scope: текущий diff
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

```bash
python3 -m unittest discover -s tests -v
```
