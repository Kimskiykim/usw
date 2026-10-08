# Proposal

## Why

LLM fallback противоречит уже действующему create-only контракту:
запрещает очистку недописанного нового файла и требует пустой HANDOFF от
существующего workspace. Metadata init также обещает lazy templates.

## What Changes

- Разрешить удаление только недописанного нового файла текущей попытки
  после ошибки записи; сохранять остальные файлы.
- Разделить проверку созданного и существовавшего HANDOFF.
- Уточнить допустимые пересечения roots, фактический inventory и границы
  работы без Python в skill, reference и metadata.

## Scope

AUD-F08 и AUD-I06: только инструкции и metadata инициализации, адресные
проверки и отчёт. Две правки F08 выполняются и проверяются отдельно.

## Non-goals

Новая семантика init, изменение Python runtime, миграция HANDOFF, поддержка
других USW skills без Python, установка глобальных skills, commit/push.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

Нет. Восстанавливаются действующие `project-initialization` и
`workspace-configuration`; `skip_specs: true` задан явно.

## Impact

`skills/usw-initialize-project/`, package tests, адресные наблюдения модели,
behavior scenarios и карточки бэклога. Новых зависимостей нет.
