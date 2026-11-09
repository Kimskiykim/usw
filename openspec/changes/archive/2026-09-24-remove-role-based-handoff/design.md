## Context

См. [proposal.md](proposal.md). Runtime различает router, generic single-state и role-based HANDOFF. Последний обходит обычную валидацию, даёт отдельный результат Show/Resume и заменяется empty router при Finish. Generic single-state имеет собственную миграцию и остаётся в scope продукта.

## Goals / Non-Goals

**Goals:** Один путь разбора для router и generic state; прежний role-based файл отклоняется без изменения HANDOFF и operation files.

**Non-Goals:** Автоматически преобразовывать role-based данные или менять другие форматы и операции.

## Decisions

- Удалить особый parser и поле `legacy` из модели `Handoff`. Обычная валидация generic документа отклонит прежнюю таблицу ролей как `invalid_handoff`. Это сохраняет file-safe поведение без нового detector.
- Сделать `_ensure_router_locked` возвращающим только `Router`: generic single-state по-прежнему мигрирует, а прежний role-based файл вызывает ошибку до изменения state files. Вызовы Begin, Show/Resume, Save, Finish и Cleanup теряют ветки `router is None`.
- Упростить `discover_handoffs` и CLI-ответы, удалив больше не используемый `legacy` flag. `recovery_only` вычисляется по status или наличию зарегистрированных операций.
- Удалить специальный нормативный requirement и заменить его контрактом отказа без изменения файлов. В product skills убрать инструкции, которые предлагают Finish для role-based состояния.

## Risks / Trade-offs

- Старый файл больше нельзя прочитать через USW → ошибка сохраняет его bytes; пользователь может перенести нужный контекст вручную.
- Ранее сохранённый клиент CLI может ожидать ключ `legacy` → это намеренное удаление поля вместе с форматом; ключ не входит в текущую документацию команд.

## Migration Plan

Текущий role-based файл пользователь сохраняет отдельно, затем запускает `/usw-init` для создания empty router. Rollback к прежней версии runtime восстанавливает прежнее чтение без миграции файла.
