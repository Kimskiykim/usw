# USW

USW помогает создавать, находить, оценивать и выполнять рабочие процессы
(flow) в Markdown через Qwen Code, Codex, Claude Code и GigaCode.
Handoff сохраняет состояние работы для продолжения в новой сессии.

## Установка

В Linux и macOS откройте локальный каталог USW и запустите установщик:

```bash
./install.sh          # Qwen Code, Codex и Claude Code
./install.sh claude   # только Claude Code; также доступны qwen и codex
```

Для обновления добавьте `--force`. Без этого флага установщик
не перезаписывает существующие компоненты.

Qwen Code также можно подключить к локальному каталогу командой
`qwen extensions link .`. В Windows для Qwen Code, Codex и Claude Code
используйте менеджер плагинов своего агента.

Для GigaCode скопируйте каталоги из USW в локальный `.gigacode/`
в корне рабочего проекта:

- `commands/` → `.gigacode/commands/`;
- `skills/` → `.gigacode/skills/`.

После установки откройте новую сессию. Для скриптов USW нужен Python 3.10+.

## Быстрый старт

```text
/usw-init
$usw-create-flow Создай flow plan-check из проверки плана.
$usw-run-flow plan-check "Проверь текущий план"
```

`/usw-init` создаёт конфигурацию `usw.yaml`, локальное состояние `.usw/`
и примеры в `usw/flows/examples/`. Существующие файлы сохраняются.
Чтобы использовать пример, скопируйте его в `usw/flows/<name>/FLOW.md`
или `usw/flows/<name>.md` и адаптируйте под задачу.

## Команды

| Команда | Что делает |
| --- | --- |
| `/usw-init` | Инициализировать USW в проекте |
| `$usw-create-flow <описание>` | Создать или обновить flow |
| `$usw-run-flow <name> "<input>"` | Выполнить flow |
| `$usw-assess-flow <name>` | Оценить flow без запуска |
| `/usw-find-flow "<намерение>"` | Найти подходящий существующий flow |
| `/usw-handoff` | Сохранить состояние текущей работы |
| `/usw-resume <operation-id>` | Восстановить сохранённую работу |
| `/usw-reviewer-llm-critic [scope]` | Проверить код без изменений |

## Flow

Flow описывает порядок действий обычным Markdown. Поддерживаются две формы:

```text
usw/flows/
├── review/FLOW.md            # flow с ресурсами в своём каталоге
└── plan-check.md             # одиночный файл
```

Локальные flow в `.usw/flows/` имеют приоритет над общими в `usw/flows/`.
Если в одном каталоге существуют обе формы с одним именем, запуск
останавливается с ошибкой `ambiguous_flow_layout`.

`$usw-create-flow` создаёт обычный Markdown; флаг `--structured` выбирает
структурированный формат с маркерами `CALL`, `GATE`, `LOOP`, `PARALLEL`.
После сохранения skill предлагает до трёх улучшений; запись правок
требует явного указания пользователя.

`$usw-assess-flow` проверяет порядок действий, зависимости и условия
завершения. Вердикты: `executable`, `executable-with-risks`,
`not-executable`, `insufficient-data`.

`/usw-find-flow` возвращает подходящий flow и команду его запуска.
Поиск и оценка сами flow не запускают.

## Продолжение работы

Handoff включён по умолчанию. Каждый запуск flow получает ID операции;
текущие операции перечислены в `.usw/HANDOFF.md`.

```text
/usw-handoff                       # сохранить состояние
/usw-resume <operation-id>         # восстановить операцию
/usw-handoff finish <operation-id> # закрыть операцию
/usw-handoff cleanup               # убрать завершённые операции
/usw-handoff cleanup --all         # убрать все операции
```

В `usw.yaml` можно изменить каталоги flow и reviews или отключить
сохранение состояния через `handoff: false`.

## Команды для отдельных ролей

| Команда | Что делает |
| --- | --- |
| [/usw-scout](commands/usw-scout.md) | Найти реализацию, связи и тесты |
| [/usw-hypothesis-checker](commands/usw-hypothesis-checker.md) | Проверить конкретное подозрение |
| [/usw-bounded-implementer](commands/usw-bounded-implementer.md) | Внести ограниченную правку и проверить её |
| [/usw-coverage-checker](commands/usw-coverage-checker.md) | Найти пробелы в проверках |

Передайте выбранной роли цель, область работы и разрешённые действия.
Субагенты автоматически не запускаются.

## Документация и проверки

[metadata.md](metadata.md) — сведения об USW.
[Спецификации](openspec/specs/) — точные правила и сценарии.
[Skills](skills/) — инструкции для агента.

```bash
python3 -m unittest discover -s tests -v
```

Поведенческие проверки модели описаны в [evals/README.md](evals/README.md).
