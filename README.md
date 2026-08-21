# USW

USW — устанавливаемый workflow для Qwen Code, Codex, Claude Code и GigaCode.
Вы описываете рабочий процесс (flow) обычным Markdown-файлом, а модель
исполняет его как текст — без DSL и отдельного рантайма. Плюс к этому USW
умеет сохранять состояние работы между сессиями (handoff).

README — обзор. Точные правила и сценарии живут в спецификациях
([`openspec/specs/`](openspec/specs/)), а [`skills/`](skills/) — производные
от них инструкции для исполнителя.

## Установка

### Claude Code

```bash
claude plugin marketplace add Kimskiykim/usw
claude plugin install usw@usw
```

### Codex

```bash
codex plugin marketplace add Kimskiykim/usw
codex plugin add usw@usw
```

### Qwen Code

```bash
qwen extensions install https://github.com/Kimskiykim/usw
```

Для локальной разработки в Qwen: `qwen extensions link .`

### GigaCode

```bash
gigacode extensions install https://github.com/Kimskiykim/usw
```

Формат расширения тот же, что у Qwen ([gigacode-extension.json](gigacode-extension.json)).

### Без менеджера плагинов

Клонируйте репозиторий и запустите установщик (Linux/macOS):

```bash
./install.sh          # все три агента
./install.sh claude   # или qwen / codex — только один
```

Установщик не перезаписывает уже установленные компоненты. Чтобы обновить
их из текущего checkout, добавьте `--force` — он же удалит компоненты
прежних версий, не трогая ваши файлы.

После любой установки откройте новую сессию — команды `/usw-init`,
`/usw-handoff`, `/usw-resume` и `/usw-reviewer-llm-critic` появятся в ней.

## Быстрый старт

```text
/usw-init
$usw-create-flow Создай flow plan-check из проверки плана.
$usw-run-flow plan-check "Проверь текущий план"
```

`/usw-init` инициализирует USW в текущем проекте:

```text
<project>/
├── .usw/                  # локальное состояние разработчика (в .gitignore)
│   ├── .gitignore
│   └── HANDOFF.md
├── usw.yaml               # конфигурация workspace
└── usw/
    └── flows/
        └── examples/      # четыре примера-заготовки
            ├── chat-review.md
            ├── dev-test.md
            ├── plan-small-steps.md
            └── refine-intent.md
```

Инициализация ничего не перезаписывает: существующие файлы остаются как
есть, небезопасные пути и symlink-корни отклоняются, а редко нужные
каталоги создаются при первом использовании. Для детерминированной
инициализации нужен Python 3.10+; без него skill спросит разрешение на
LLM-fallback с тем же результатом.

В `usw.yaml` задаются корневые каталоги (по умолчанию `usw`, `usw/flows`,
`usw/reviews`) и флаг `handoff: true|false`; отсутствие флага означает
`true`.

Примеры в `examples/` — заготовки, а не активные flow: скопируйте нужный в
`usw/flows/<name>/FLOW.md` (или `<name>.md`), адаптируйте и запускайте.

Подробнее: [project-initialization](openspec/specs/project-initialization/spec.md),
[workspace-configuration](openspec/specs/workspace-configuration/spec.md),
[flow-examples](openspec/specs/flow-examples/spec.md).

## Команды

| Команда | Что делает |
|---|---|
| `/usw-init` | Инициализировать USW в проекте |
| `$usw-create-flow <описание>` | Создать или обновить flow |
| `$usw-run-flow <name> "<input>"` | Выполнить flow |
| `$usw-assess-flow <name>` | Оценить flow без запуска |
| `/usw-find-flow "<намерение>"` | Найти подходящий существующий flow |
| `/usw-handoff` | Сохранить состояние текущей работы |
| `/usw-resume <operation-id>` | Восстановить сохранённую работу |
| `/usw-reviewer-llm-critic [scope]` | Жёсткое read-only ревью LLM-кода |

## Как устроены flow

Flow — это Markdown-файл. Runner читает его один раз и передаёт модели
точный текст, input и каталог flow (`flow_directory`). Две поддерживаемые
формы:

```text
usw/flows/
├── review/FLOW.md            # каноничная: каталог с FLOW.md и ресурсами рядом
├── review/scripts/check.py   # ресурсы flow лежат в его каталоге
└── plan-check.md             # совместимая: одиночный файл `<name>.md`
```

`$usw-run-flow` ищет flow сначала в локальном `.usw/flows`, затем в общем
`usw/flows`. Если в одном месте существуют обе формы с одним именем,
запуск останавливается с ошибкой `ambiguous_flow_layout`.

Важно: текст flow не даёт полномочий. Commit, push, deploy и другие
внешние действия по-прежнему требуют обычных разрешений.

`$usw-create-flow` по умолчанию пишет обычный Markdown. Флаг `--structured`
добавляет человекочитаемые маркеры `CALL`, `GATE`, `LOOP`, `PARALLEL` —
это авторская конвенция, а не машинный формат. После сохранения skill
проверяет черновик по каталогу рецептов и предлагает до трёх улучшений на
выбор: применить, изменить или пропустить.

Подробнее: [text-flow-execution](openspec/specs/text-flow-execution/spec.md),
[local-custom-flows](openspec/specs/local-custom-flows/spec.md),
[markdown-flow-composition](openspec/specs/markdown-flow-composition/spec.md),
[guided-flow-authoring](openspec/specs/guided-flow-authoring/spec.md).

## Оценка и поиск flow

```text
$usw-assess-flow [--local|-l|--shared] <flow-name> [<scenario-input>]
```

Команда проверяет существующий flow, ничего не запуская:
исполним ли он, где логические разрывы, какие у него зависимости, нет ли
незавершающихся циклов. Итог — отчёт с одним вердиктом: `executable`,
`executable-with-risks`, `not-executable` или `insufficient-data`. Это
семантическая оценка модели с доказательствами, а не машинная гарантия.

`/usw-find-flow "<намерение>"` ищет среди существующих flow подходящий под
одно намерение и возвращает готовую команду запуска (`match`), либо
`ambiguous` / `no-match` — ничего не создавая и не запуская.

Подробнее: [flow-assessment](openspec/specs/flow-assessment/spec.md),
[flow-discovery](openspec/specs/flow-discovery/spec.md).

## Handoff: передача работы между сессиями

Когда handoff включён (по умолчанию — да), каждый запуск flow
регистрируется как отдельная операция со своим ID и файлом состояния.
`.usw/HANDOFF.md` — таблица текущих операций.

```text
/usw-handoff                      # сохранить состояние
/usw-resume <operation-id>        # восстановить конкретную операцию
/usw-handoff finish <operation-id>  # закрыть одну операцию
/usw-handoff cleanup              # убрать все завершённые, активные остаются
```

Операции не блокируют друг друга: даже два запуска одного flow с одним
input получают разные ID. Конфликты в файлах проекта USW не отслеживает —
за независимость областей работы отвечает пользователь.

Вложенный flow, запущенный из другого flow, работает от имени родителя:
своей операции не получает, состояние не пишет; итог записывает только
корневой запуск.

Подробнее: [live-operation-state](openspec/specs/live-operation-state/spec.md),
[nested-flow-execution](openspec/specs/nested-flow-execution/spec.md),
[execution-artifacts](openspec/specs/execution-artifacts/spec.md).

## Платформы

USW работает на Linux, macOS и Windows; все возможности доступны везде.
Отличия Windows:

- **Защита от подмены путей слабее.** На Linux и macOS проверенный путь
  нельзя подменить после проверки (descriptor-relative доступ). На Windows
  такого механизма нет: symlink, junction и выход за пределы каталога
  отклоняются на каждом шаге, но окно между проверкой и чтением полностью
  не закрыто. Практически: обычные ошибки ловятся одинаково везде, а
  целенаправленная подмена пути возможна только у процесса, у которого и
  так есть права записи в ваш проект.
- **Файлы handoff не ограничены по правам доступа** — Windows не реализует
  POSIX-биты (на Linux и macOS они создаются с режимом `0600`).
- **`install.sh` не работает** — это POSIX-скрипт; ставьте USW через
  менеджер плагинов своего агента.

## Разработка

```bash
python3 -m unittest discover -s tests -v
```

Поведенческие сценарии (opt-in, локальные, требуют настроенного runner)
описаны в [`evals/README.md`](evals/README.md).
