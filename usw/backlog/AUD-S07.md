# AUD-S07 — Изменение `flows.root` во время staging обнаруживается после записи

- Статус: backlog
- Приоритет: P2
- Категория: находка аудита
- Действие: Перед replace повторно сравнивать effective authoring root с планом.
- Условие возврата: следующая правка writer
- Критерий готовности: смена flows.root во время staging даёт stale target до записи, косметическая правка YAML не считается сменой цели.
- Источник: [Аудит S07](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md:78)
