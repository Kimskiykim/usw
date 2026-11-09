# AUD-S05 — Регистр имени обходит запрет записи в `.git`

- Статус: backlog
- Приоритет: P2
- Категория: находка аудита
- Действие: Проверять filesystem aliases и регистр reserved/writable roots.
- Условие возврата: следующая правка validator
- Критерий готовности: .GiT/.USW и пересекающиеся roots на нечувствительном к регистру томе отклоняются до записи; одного normcase на macOS недостаточно.
- Источник: [Аудит S05](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md:60)
