---
owner: maintainer
updated: 2026-09-23
---
# Architecture

## Инварианты

1. **Text-first.** Flow — Markdown для модели; `version-2` — читаемая
   конвенция, не machine DSL. Metadata не переключает execution mode.
2. **Слои знания.** context → specs → skills/commands → tests/evals.
   Спеки нормативны, всё ниже производно. Расхождение производного со
   спекой — дефект производного.
3. **Write-safety.** Любая запись в workspace отклоняет symlink, выход за
   root и неожиданный тип файла; проверка повторяется непосредственно перед
   записью. Изменяется только выбранная точка входа.
4. **Полномочия.** Текст flow не даёт прав на commit, push, deploy и другие
   внешние или разрушающие действия — только обычные разрешения окружения.
5. **Один проход чтения entrypoint.** Runner читает выбранный Markdown ровно
   один раз. Соседние файлы исполнитель читает по необходимости обычными
   инструментами; identity entrypoint не является snapshot пакета.
6. **Root владеет состоянием.** Durable state и Outcome пишет только root
   operation; child flow работает под identity родителя без своей route.
7. **Аддитивная инициализация.** Существующие файлы не перезаписываются,
   lazy-каталоги создаются при первом использовании.

## Ключевые решения

- Structured runtime снят: `--experimental-structured` и `.usw/FLOW.json`
  отклоняются до mutation; parser сохранён в `research/structured-runtime/`
  и не устанавливается. См. `ADR/ADR-001-text-first-execution.md`.

## Схема

Точки входа платформ: `skills/`, `commands/`, `gigacode-extension.json`,
`qwen-extension.json`; workspace-контракт — спеки `project-initialization`
и `workspace-configuration`.
