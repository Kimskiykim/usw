## Context

Сейчас `usw-run-flow` одновременно выбирает root, валидирует только версии `1`
и `version-2`, строит `CustomFlow`, разрешает executors, управляет cursor,
ветвлениями, loops, parallel, binding и resume. Это полезно для
детерминированного workflow engine, но делает экспериментальную механику
обязательной для обычного пользователя.

Основной пользовательский интент проще: «запусти эту задачу с этим flow».
Flow является Markdown-файлом в одной из существующих папок. Его формат не
должен быть частью публичного контракта запуска.

## Goals / Non-Goals

**Goals:**

- запускать по умолчанию любой безопасно найденный Markdown-flow;
- принимать задачу и имя flow без schema-specific параметров;
- оставить structured runtime доступным через явный экспериментальный opt-in;
- закрепить создание структурированной формы за `usw-create-flow`;
- сохранить permissions, безопасное разрешение файлов и наблюдаемый HANDOFF.

**Non-Goals:**

- автоматически включать строгий runtime по полю версии внутри Markdown;
- требовать от пользователя DSL, action map или result bindings;
- превращать default-путь в scheduler либо универсальный workflow engine;
- угадывать отсутствующий flow name или обходить внешние permissions;
- добавлять новый DSL, dependency или отдельный state service.

## Decisions

### 1. Default `run-flow` является тонким фасадом

Публичный вход состоит из текста задачи и безопасного имени flow. Фасад ищет
`<name>.md` сначала в developer-local `<project>/.usw/flows`, затем в
настроенном shared root. Явный origin selector ограничивает поиск одним root.
Local flow тем самым может осознанно переопределить shared flow с тем же именем.

После разрешения фасад передаёт задачу и содержимое файла Markdown executor без
проверки версии. Отсутствующий файл, небезопасное имя либо unsafe filesystem
object останавливают запуск до исполнения.

### 2. Обычный Markdown исполняется как описание процесса

Default executor читает документ целиком и следует описанному в нём порядку,
используя обычные skill/agent capabilities. Заголовки, язык, формат списков и
наличие metadata не являются runtime API. Если документ не позволяет выбрать
следующее действие без существенной догадки, executor возвращает
`decision_required`.

Весь default-запуск является одной observable operation boundary. HANDOFF
фиксирует flow identity, задачу, начало и итог, но default-путь не создаёт
machine cursor для каждого Markdown-пункта и не требует normalized plan.

### 3. Строгий runtime включается только явно

Существующий parser/orchestrator `CustomFlow` сохраняется как
экспериментальный runtime за явным selector `--experimental-structured`.
Только этот путь валидирует v1/v2, строит execution model, разрешает typed
executors и управляет gates, loops, parallel и cursor/checkpoint.

Поле `Версия` внутри файла само по себе не включает experiment. Это сохраняет
правило «любой Markdown по умолчанию» и не делает внутренний формат скрытым
переключателем поведения.

### 4. Структурирование принадлежит `usw-create-flow`

`usw-create-flow` создаёт или обновляет строгую форму, когда пользователь явно
выбирает structured/experimental режим. Он отвечает за постоянные имена,
executors, transitions и применимые binding declarations. `usw-run-flow` не
переписывает flow и не просит пользователя нормализовать документ перед
обычным запуском.

### 5. Binding экспериментален и необязателен

Strict runtime может передавать именованные inputs/results, включая child
outcomes `PARALLEL`, но отсутствие такого binding не мешает запуску. Default
Markdown executor получает исходную задачу целиком и не требует распределять
её по action names.

### 6. Общая безопасность не является экспериментом

Оба пути сохраняют безопасное разрешение flow и scripts, запрет неявного shell,
проверку доступности capabilities и отдельное разрешение на commit, push, PR,
deploy, release и другие внешние side effects. Experiment меняет способ
интерпретации flow, но не расширяет полномочия.

## Risks / Trade-offs

- [Обычный Markdown допускает несколько толкований] → возвращать
  `decision_required`, когда выбор существенно влияет на результат.
- [Local flow неожиданно скрывает shared flow] → сообщать resolved origin и
  identity до исполнения; явный selector позволяет выбрать root.
- [Default execution менее детерминированно, чем строгий runtime] → для точного
  cursor/resume пользователь явно включает structured experiment.
- [Два режима расходятся] → общими оставить lookup, permissions, outcome и
  HANDOFF envelope; schema-specific поведение держать только в adapter.
- [Экспериментальная версия в файле выглядит как auto-opt-in] → документация и
  тесты закрепляют, что нужен отдельный selector запуска.

## Migration Plan

1. Удалить незавершённый default binding, предполагающий готовый action map.
2. Добавить facade input «задача + flow name» и поиск local → shared.
3. Добавить generic Markdown executor как default path.
4. Перенести строгую v1/v2 маршрутизацию за
   `--experimental-structured`, сохранив её текущие safety checks.
5. Обновить `usw-create-flow`, references, README и тесты.
6. Запустить полную регрессию и строгую OpenSpec validation.

Откат возвращает строгий parser как default для v1/v2. Markdown-файлы не
мигрируют и не переписываются автоматически.

## Open Questions

Нет блокирующих вопросов.
