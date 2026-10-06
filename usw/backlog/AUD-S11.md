# AUD-S11 — Путь установки может совпасть с источником и уничтожить его

- Статус: backlog
- Приоритет: P2
- Категория: находка аудита
- Действие: До очистки отклонять source/target overlap и aliases установки.
- Условие возврата: следующая правка installer
- Критерий готовности: совпадение QWEN_HOME с checkout и symlink alias не удаляют исходники.
- Источник: [Аудит S11](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md:112)
