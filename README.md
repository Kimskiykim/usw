# USW

USW — устанавливаемый харнес для Qwen Code и Codex.

Первая команда харнеса инициализирует USW в текущем проекте и создаёт:

```text
<project>/
├── hello_world.py
└── usw/
    └── SYNC.md
```

Если один из файлов уже существует, команда оставляет его без изменений.

## Qwen Code

Установите USW как Qwen extension:

```bash
qwen extensions install https://github.com/Kimskiykim/usw
```

После установки выполните в Qwen Code:

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

После установки откройте новую задачу и вызовите команду:

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
./install.sh --force
```

## Разработка

Запуск тестов не требует сторонних зависимостей:

```bash
python3 -m unittest discover -s tests -v
```
