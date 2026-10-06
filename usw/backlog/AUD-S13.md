# AUD-S13 — Явно пустой `--runner` не перекрывает переменную окружения

- Статус: backlog
- Приоритет: P2
- Категория: находка аудита
- Действие: Различать отсутствующий и явно пустой --runner.
- Условие возврата: следующая правка harness
- Критерий готовности: пустой override не запускает команду из окружения; допустим явный отказ вместо silent fallback.
- Источник: [Аудит S13](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md:130)
