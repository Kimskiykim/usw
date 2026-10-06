# AUD-S03 — Частичный migration document блокирует автоматический повтор

- Статус: backlog
- Приоритет: P2
- Категория: находка аудита
- Действие: Удалять только принадлежащий попытке неполный operation document при ошибке exclusive write/flush/close.
- Условие возврата: следующая правка migration
- Критерий готовности: исходный HANDOFF сохранён, retry успешен, ранее существовавший destination не удаляется.
- Источник: [Аудит S03](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md:44)
