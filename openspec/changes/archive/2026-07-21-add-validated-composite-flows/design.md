## Context

Существующий `usw-run-flow` уже гарантирует одно атомарное действие за вызов,
проверку write authority и нормализованный outcome, но parser и capability
registry замкнуты на Analysis, Development и Testing. Пользователю нужен тот же
уровень гарантий для произвольной project-owned последовательности, описанной
обычным Markdown, без YAML front matter, исполняемого псевдокода, branch graph и
циклов.

Изменение затрагивает загрузку и валидацию custom flow, разрешение executors и
developer-local resume. Существующие role flows и atomic skills не меняются.

## Goals / Non-Goals

**Goals:**

- сделать `usw-run-flow <name>` общим runner для standard и custom flows;
- сохранить обычный читаемый Markdown как единственный project-owned flow file;
- валидировать полный контракт до первого шага;
- поддержать линейные шаги skill и script;
- сохранить atomic execution, authority checks, observable stops и resume;
- не изменять существующее поведение standard role flows.

**Non-Goals:**

- язык программирования workflow, ветвления, циклы, параллельность и retries;
- произвольные shell-команды или hooks;
- автоматическое обнаружение «похожего» skill;
- публичный plugin API для сторонних executors;
- миграция или перезапись существующих role flows.

## Decisions

### Один versioned Markdown-контракт

Flow остаётся обычным Markdown. Обязательны только секции `Контракт`, `Порядок
действий` и `Полномочия записи`; остальные заголовки и текст являются свободной
документацией. Версия задаётся list field в секции `Контракт`, а исполняемая
семантика берётся только из ordered list действий и его вложенных полей.

Пример:

```markdown
# Flow: проверка-задачи

## Контракт

- Версия: `1`

## Порядок действий

1. Скилл: `usw-plan-small-steps`
   - Пишет: `task-index`
2. Скрипт: `scripts/check_plan.py`
   - Аргументы: `--strict`
   - Пишет: нет
## Полномочия записи

- `task-index`
```

Альтернатива с YAML front matter отклонена: она создаёт второй формат внутри
документа и не требуется для небольшой линейной модели. Свободный natural-
language Markdown также отклонён, поскольку не даёт детерминированной проверки.

### Линейная последовательность вместо control-flow graph

Runner хранит индекс шага и после `completed` увеличивает его на один. Любой
другой status останавливает flow. Review rejection и repair моделируются как
остановка и новый или resumed scoped run, а не обратный branch.

Альтернатива с `branches` отклонена: произвольный target требует semantics для
циклов, лимитов итераций, идемпотентности и cycle-safe resume.

### Два типа шага с одним outcome contract

- `Скилл` — точное имя доступной capability и вызов её declared contract.
- `Скрипт` — project-relative regular file плюс отдельные arguments без shell.

Все adapters возвращают существующий `ActionOutcome`. Flow-level validator
сравнивает declared writes с authority до вызова, а runner проверяет reported
writes после результата. Capability resolver остаётся закрытой internal
boundary; произвольный executable plugin API не вводится.

Альтернатива с универсальным `run:` отклонена: она скрывает тип executor и
упрощает попадание shell semantics в проектный документ.

### Безопасное разрешение имени и script path

Имя flow ограничивается kebab-case identifier и разрешается только как
`<flows.root>/<name>.md`. Script path разрешается от project root, запрещает
absolute path, `..`, symlink traversal и non-regular target. Args передаются
как отдельные значения, никогда как shell command string.

### Resume привязан к identity flow

Checkpoint дополняется именем flow, digest нормативного Markdown и индексом
следующего шага. Изменившийся flow делает checkpoint stale. Уже существующая
canonical product source identity продолжает отдельно отвечать за применимость
verification и evidence.

## Risks / Trade-offs

- [Markdown допускает косметические вариации] → разбирать Markdown structure,
  нормализовать пробелы и выдавать ошибки с section/step location.
- [Script не может доказать свои writes статически] → требовать declared writes,
  platform permission boundary и structured result; shell отключён.
- [Линейность не выражает сложный repair] → останавливать flow и продолжать из
  checkpoint; граф добавлять только после подтверждённого сценария.
- [Локализованные headings становятся частью контракта] → версия контракта
  фиксирует точные semantic labels; смена языка требует новой версии schema.

## Migration Plan

1. Добавить parser/validator custom Markdown flow рядом с текущим role runner.
2. Подключить вызов `usw-run-flow <name>` и document the contract.
3. Проверить один custom flow end-to-end без изменения standard role files.

Rollback удаляет custom loader; существующие role flows не затрагиваются.
