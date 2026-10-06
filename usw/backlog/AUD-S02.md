# AUD-S02 — Writer не различает прежний и подставленный обычный каталог

- Статус: backlog
- Приоритет: P1
- Категория: находка аудита
- Действие: Сверять identity текущего parent с удерживаемым handle; cleanup удаляет только собственный созданный каталог.
- Условие возврата: ближайшее исправление writer
- Критерий готовности: directory swap во время staging не пишет во внешний перемещённый каталог и не удаляет чужую замену. Остаточное CAS-окно после final recheck не входит в обещание.
- Источник: [Аудит S02](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md:34)
