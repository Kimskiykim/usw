# AUD-I13 — Разрешения на внешние действия и ожидание событий

- Статус: backlog
- Приоритет: P3
- Категория: рекомендация
- Действие: External-action-approval/external-event-wait/input-preflight: учитывать действующее разрешение на точный эффект, не обещать durable resume без handoff, различать ответ человека и внешний blocker.
- Условие возврата: следующая правка рецептов
- Критерий готовности: нет повторного запроса того же разрешения или необоснованного обещания восстановления.
- Источник: [Аудит и рекомендации](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/REVIEW.md)
- External-event-wait: [рецепт](../../skills/usw-create-flow/references/recipes/external-event-wait.md) различает ручной повторный вход при выключенном handoff и восстановление по действующему контракту при включённом; [change](../../openspec/changes/archive/2026-11-10-condition-external-event-resume/proposal.md). External-action-approval и input-preflight остаются открытыми.
