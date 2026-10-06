# AUD-S01 — Миграция HANDOFF теряет состояние при ошибке после замены router

- Статус: backlog
- Приоритет: P1
- Категория: находка аудита
- Действие: Не удалять документ операции после уже опубликованного router при ошибке sync/readback migration или Begin.
- Условие возврата: ближайшее исправление handoff
- Критерий готовности: отказы после replace не теряют recovery facts, любой опубликованный маршрут имеет документ.
- Источник: [Аудит S01](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md:24)
