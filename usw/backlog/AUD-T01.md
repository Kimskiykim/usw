# AUD-T01 — Текст неизвестного YAML-поля становится управляющими настройками

- Статус: backlog
- Приоритет: P2
- Категория: находка аудита
- Действие: Не интерпретировать вложенный текст неизвестного scalar как top-level configuration; проверять отступы.
- Условие возврата: следующая правка parser
- Критерий готовности: notes не меняет flows.root/handoff, неподдержанный block scalar явно отклонён либо непрозрачен.
- Источник: [Аудит T01](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/DATA_AND_CONTRACTS.md:9)
