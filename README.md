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

При effective `handoff: true` `.usw/HANDOFF.md` создаётся как пустой
детерминированный router локальных операций. Mutable recovery state появляется
лениво в `.usw/handoffs/<operation-id-hex>.md` при первом Begin. При
`handoff: false` initializer и runtime не читают, не проверяют и не изменяют
router, operation directory или operation-scoped candidates.
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

### Routed handoff

При включённом handoff каждый top-level запуск получает уникальный
`usw-operation:<hex>` и собственный state-файл. `.usw/HANDOFF.md` хранит только
маршруты от exact operation ID к этим файлам; status, проверки и recovery
context живут в operation document.

Перед паузой активного запуска сохраните только его актуальное состояние:

```text
/usw-handoff
```

Команда адресует exact ID, возвращённый Begin, и сохраняет flow, origin,
identity, input digest, status, выполненное, narrative current position,
blocker, проверки, references и ровно одно следующее действие. Это компактная
локальная summary, а не machine cursor, shared history или лог tool calls.

В новой сессии восстановите конкретный контекст:

```text
/usw-resume <operation-id>
```

Без ID пустой router сообщает, что продолжать нечего, единственная route
выбирается автоматически, а несколько routes показываются списком без
автоматического продолжения. `in_progress` означает возможное прерывание и
никогда не запускается повторно автоматически. `paused`, `blocked` и
`decision_required` требуют явного решения.

Два независимых чата могут работать одновременно:

```text
чат UI:      Begin → usw-operation:<ui-hex>  → handoffs/<ui-hex>.md
чат backend: Begin → usw-operation:<api-hex> → handoffs/<api-hex>.md
```

Их короткие router/state transitions сериализуются, но сами flow не
сериализуются. Это заявление пользователя о независимости: USW не обнаруживает
и не разрешает конфликты в product files, поэтому UI и backend scope должны
быть действительно разделены либо координироваться обычными средствами Git.
Даже одинаковые flow/input получают разные IDs, а Outcome или Save могут
изменить только exact зарегистрированную operation.

`completed` и `failed` остаются доступными для inspect и не заменяются
следующим Begin. Очистка всегда адресная:

```text
/usw-handoff finish <operation-id>
```

Без ID Finish использует те же zero/one/many rules. Он удаляет только выбранную
route и её operation files; остальные запуски остаются зарегистрированы.

Текущий generic single-state HANDOFF при первом обращении мигрирует в router
без потери recovery content. Старый role-based HANDOFF остаётся read-only до
explicit Finish. Для rollback на USW, который понимает только single-state
HANDOFF, сначала завершите через Finish все routed operations, затем замените
пустой router на generic idle HANDOFF старой версии. Product files и flow
менять для rollback не требуется.

### Nested flows

Named child flow, запущенный root executor-ом, использует execution identity
родителя и не получает собственную route. Перед child model execution
проверяется exact recoverable parent; child не вызывает Begin, Outcome, Save
или Finish и возвращает root-у фактический status/result. Только root агрегирует
результаты детей и записывает свой Outcome. Независимые children могут
исполняться параллельно, но USW не создаёт scheduler, durable child registry,
automatic retry или conflict detection.

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

После успешного сохранения `usw-create-flow` автоматически показывает до трёх
применимых design suggestions: verification, human decision, approval внешнего
действия, error handling, bounded refinement, независимые проверки или reuse
явно названного skill из текущего списка доступных skills. Каждая подсказка
объясняет конкретный риск и содержит готовый Markdown. Flow изменяется только
после выбора `применить`; `изменить` сначала показывает новый preview без
записи, а `пропустить` сохраняет уже записанный файл без revision.

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
resolve exact Markdown bytes → optional Begin/root operation → root model
nested child → assert-current(root) → child result → root aggregation
root natural stop → Outcome(exact root ID, без automatic retry)
/usw-handoff finish <operation-id> → remove exact route
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

## Оценка flow

Явная команда `$usw-assess-flow` проверяет один существующий flow на
исполняемость, логические разрывы, зависимости и потенциально бесконечные
циклы, но не запускает flow и ничего не изменяет:

```text
$usw-assess-flow [--local|-l|--shared] <flow-name> [<scenario-input>]
```

Без origin selector используется local-first resolution. Необязательный
scenario input добавляет трассу одного пути, но не скрывает проблемы других
веток. Отчёт содержит terminal paths, dependency ledger, findings с evidence и
один verdict: `executable`, `executable-with-risks`, `not-executable` или
`insufficient-data`.

Это evidence-backed семантическая оценка модели: она не является machine guarantee,
parser-backed proof или recursive validation вызываемых flow.
Assessment не читает HANDOFF, не создаёт runtime state и не применяет
предложенные исправления.

## Поиск flow

Команда `/usw-find-flow` по одному явному намерению ищет подходящий уже
существующий runnable flow среди direct local и shared Markdown entries:

```text
/usw-find-flow "Проверь текущий план перед реализацией"
```

При однозначном совпадении finder возвращает name, origin, path, краткое
основание и готовую команду `$usw-run-flow` с исходным намерением. При
равноценных вариантах он показывает `ambiguous`, а при отсутствии подходящего
flow — `no-match`.

Finder ничего не создаёт и не запускает, не читает HANDOFF и не ищет packaged
examples, внешние каталоги или другие проекты. Для нового процесса отдельно
используйте `$usw-create-flow`, для выбранного существующего —
`$usw-run-flow`.

## Декомпозиция на микротаски

Команда `/usw-plan-small-steps` через backend skill превращает большую спецификацию или выбранный
подход в небольшие исполняемые задачи. У каждой заранее есть результат,
критерий готовности и проверка с ожидаемым наблюдением. Skill не выполняет
задачи и не выбирает следующий scope: результат возвращается orchestrator.

```text
/usw-plan-small-steps Разбей миграцию API на микротаски.
```

## Итеративное уточнение намерения

Команда `/usw-refine-intent` через backend skill ведёт обсуждение в режиме опросника: разбирает один
decision case за ход, фиксирует подтверждённое решение и только затем переходит
к следующему. Локальная ненормативная сессия, журнал решений и необязательный
итог сохраняются в `.usw/refinements/<refinement-id>/`. Skill не создаёт
backlog, planning change, planning artifacts или executable tasks:

```text
/usw-refine-intent Давай по одному решению уточним идею этой задачи.
```

Это breaking rename без alias: установленный `usw-refine-task` удаляется при
`./install.sh --force`. Исторические `usw/refinements/` остаются нетронутыми.

## Перевод предложений агента

Команда `/usw-explain-me` через backend skill переводит план, рекомендацию, дифф, ошибку
или статус кодингового агента на выбранный уровень подробности: от «как для
хлебушка» до экспертного разбора. По умолчанию он подстраивается под запрос и
не начинает менять код:

```text
/usw-explain-me Объясни это как для хлебушка: <вставьте ответ агента>
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
