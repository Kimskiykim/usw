# USW

USW — устанавливаемый самостоятельный workflow для Qwen Code, Codex и
Claude Code: именованные Markdown flow, которые модель исполняет как текст,
плюс локальное routed-состояние для передачи работы между сессиями.

Нормативный источник правил — спецификации в
[`openspec/specs/`](openspec/specs/). README — обзор: он говорит, что USW
делает и как его поставить, а точные обязательства и сценарии живут в спеках.
Skills в [`skills/`](skills/) — производные инструкции для исполнителя.

## Быстрый старт

```text
/usw-init
$usw-create-flow Создай flow plan-check из проверки плана.
$usw-run-flow plan-check "Проверь текущий план"
```

Первая команда инициализирует standalone USW в текущем проекте и сразу создаёт:

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
            ├── dev-test.md
            ├── plan-small-steps.md
            └── refine-intent.md
```

Инициализация аддитивна: существующие файлы не перезаписываются, небезопасные
или symlinked roots отклоняются до записи, lazy-каталоги (`.usw/flows/`,
`.usw/refinements/`, `.usw/handoffs/`, artifact roots) появляются при первом
использовании. `usw.yaml` версии 1 выбирает project-relative roots (по
умолчанию `usw`, `usw/flows`, `usw/reviews`) и optional top-level
`handoff: true|false`; отсутствие поля означает `true`. Для детерминированной
инициализации нужен Python 3.10+ (`python3`, затем `python`); без него skill
спрашивает разрешение на менее детерминированный LLM fallback с тем же
контрактом. Подробности: [project-initialization](openspec/specs/project-initialization/spec.md),
[workspace-configuration](openspec/specs/workspace-configuration/spec.md).

Четыре установленных примера — ненормативные заготовки в
`<flows.root>/examples/`, а не активные flow: скопируйте нужный в
`<flows.root>/<name>/FLOW.md` или `<flows.root>/<name>.md`, адаптируйте и
запускайте ([flow-examples](openspec/specs/flow-examples/spec.md)).

## Text-first execution

`$usw-run-flow` принимает kebab-case имя и input, ищет flow сначала в
`.usw/flows`, затем в shared `flows.root`, и поддерживает две формы entrypoint:

```text
usw/flows/
├── review/FLOW.md
└── review/scripts/check.py
```

Canonical layout — `<name>/FLOW.md`; `<name>.md` остаётся совместимым и не
мигрирует автоматически. Обе формы одного name в одном origin останавливают
resolution с `ambiguous_flow_layout`. Runner читает entrypoint ровно один раз
и передаёт модели exact Markdown, input и resolver-owned `flow_directory`;
package resources разрешаются только по явной ссылке из packaged `FLOW.md` и
возвращаются как immutable bytes. Flow text не предоставляет полномочий:
commit, push, deploy и другие внешние действия требуют обычных разрешений.
Правила: [text-flow-execution](openspec/specs/text-flow-execution/spec.md),
[local-custom-flows](openspec/specs/local-custom-flows/spec.md).

`$usw-create-flow` создаёт обычный Markdown по умолчанию; `--structured`
выбирает человекочитаемый `version-2` с маркерами `CALL`, `GATE`, `LOOP`,
`PARALLEL` — это авторская конвенция, а не machine DSL
([markdown-flow-composition](openspec/specs/markdown-flow-composition/spec.md)).
После сохранения skill проводит короткий design scan по каталогу из пятнадцати
рецептов и предлагает не более трёх применимых улучшений с вариантами
`применить`, `изменить`, `пропустить`; при проектировании от цели согласованные
блоки встраиваются в flow, а перегруженный черновик получает предупреждение о
сложности без блокировки записи
([guided-flow-authoring](openspec/specs/guided-flow-authoring/spec.md)).

`--experimental-structured` и внутренние команды снятого structured runtime
отклоняются до mutation; `.usw/FLOW.json` не читается и не изменяется. Снятый
parser и его тесты сохранены в `research/structured-runtime/` и не
устанавливаются. Ненормативный roadmap (compiler → machine flow → iterator)
появится только отдельным change с измеримой потребностью в machine
guarantees.

## Routed handoff

При включённом handoff каждый top-level запуск регистрирует уникальную
operation с собственным state-файлом; `.usw/HANDOFF.md` — validated router и
таблица текущих операций. Сохранение и восстановление:

```text
/usw-handoff
/usw-resume <operation-id>
```

Независимые запуски не блокируют друг друга, даже одинаковые flow/input
получают разные IDs, а Outcome и Save адресуют только exact операцию. USW не
обнаруживает конфликты в product files — независимость scope остаётся
заявлением пользователя. Очистка адресная:

```text
/usw-handoff finish <operation-id>
/usw-handoff cleanup
```

Finish удаляет одну route, cleanup — сразу все terminal operations, сохраняя
активные. Generic single-state HANDOFF мигрирует в router при первом
обращении; старый role-based HANDOFF читается только для recovery до explicit
Finish. Для rollback на старую версию завершите routed operations через
Finish и замените пустой router на generic idle HANDOFF. Полный контракт:
[live-operation-state](openspec/specs/live-operation-state/spec.md).

Named child flow, запущенный root executor-ом, использует identity родителя,
не получает собственную route и не пишет durable state; только root агрегирует
результаты и записывает Outcome
([nested-flow-execution](openspec/specs/nested-flow-execution/spec.md)).

Артефакты исполнения — `tasks.md` как единственный completion source,
task contracts, раздельное Development/Testing evidence, immutable review
receipts и `USW-SOURCE-V1` product source identity — определены в
[execution-artifacts](openspec/specs/execution-artifacts/spec.md).

## Оценка и поиск flow

```text
$usw-assess-flow [--local|-l|--shared] <flow-name> [<scenario-input>]
```

Явная команда `$usw-assess-flow` проверяет один существующий flow на
исполняемость, логические разрывы, зависимости и незавершающиеся циклы, ничего
не запуская и не изменяя. Отчёт содержит terminal paths, dependency ledger,
findings с evidence и один verdict: `executable`, `executable-with-risks`,
`not-executable` или `insufficient-data`. Это evidence-backed семантическая
оценка модели, не machine guarantee
([flow-assessment](openspec/specs/flow-assessment/spec.md)).

```text
/usw-find-flow "Проверь текущий план перед реализацией"
```

Finder по одному намерению ищет существующий runnable flow среди direct local
и shared entries и возвращает `match` с готовой командой `$usw-run-flow`,
`ambiguous` или `no-match`, ничего не создавая и не запуская
([flow-discovery](openspec/specs/flow-discovery/spec.md)).

Декомпозиция задачи и уточнение intent поставляются как обычные примеры
`plan-small-steps.md` и `refine-intent.md` — их копируют и запускают теми же
командами, без отдельных skills.

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

## Claude Code

Подключите marketplace и установите плагин:

```bash
claude plugin marketplace add Kimskiykim/usw
claude plugin install usw@usw
```

После установки откройте новую сессию и вызовите `/usw-init`. Команды
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
./install.sh claude
```

Без аргумента `./install.sh` установит command и skill для всех трёх агентов.
Установщик не перезаписывает существующие компоненты.

Чтобы явно обновить уже установленный skill из текущего checkout, выполните:

```bash
./install.sh codex --force
```

Для Qwen используйте `./install.sh qwen --force`, для Claude Code —
`./install.sh claude --force`, а для всех агентов сразу — `./install.sh --force`.
`./install.sh --force` также удаляет снятые компоненты прежних версий;
пользовательские артефакты не изменяются.

## Платформы

USW поддерживает Linux, macOS и Windows. Все возможности, включая routed handoff
и обе формы flow, доступны на каждой из них.

Доступ к файлам идёт через один общий safe-access boundary, у которого две
реализации, и защита у них не одинаковая. Там, где операционная система
предоставляет descriptor-relative доступ — на Linux и macOS — проверенный
компонент пути больше не адресуется по имени, поэтому подменить его после
проверки нельзя. На Windows такого механизма нет: boundary отвергает symlink,
junction и reparse point на каждом шаге и запрещает имена, выходящие за пределы
каталога, но обращается к записям по пути. Это сужает окно между проверкой и
использованием, но не закрывает его.

Практически это означает следующее. Обычные ошибки — ссылка, ведущая за пределы
проекта, неверный тип файла, выход за границы каталога — отвергаются одинаково
на всех платформах. А от процесса, который **целенаправленно подменяет** путь
ровно между проверкой и чтением, Windows не защищён. Такому процессу нужны права
записи в ваш проект; получив их, он может просто отредактировать сам `FLOW.md`.

Ещё два отличия Windows, выявленные прогоном на самой платформе. Файлы handoff
там не ограничены по правам доступа: POSIX-биты прав Windows не реализует, а на
Linux и macOS эти файлы создаются с режимом `0600`. И `install.sh` — POSIX-скрипт,
на Windows он не исполняется; ставьте USW через extension или plugin manager
своего агента, как описано выше.

## Разработка

```bash
python3 -m unittest discover -s tests -v
```

Поведенческие сценарии (opt-in, локальные, с настроенным runner) описаны в
[`evals/README.md`](evals/README.md).
