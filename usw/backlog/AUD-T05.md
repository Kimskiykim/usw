# AUD-T05 — Unicode-разделители строк ломают сохранение exact input

- Статус: backlog
- Приоритет: P2
- Категория: находка аудита
- Действие: Экранировать Unicode-разделители строк в JSON-полях handoff с сохранением decoded input/digest.
- Условие возврата: следующая правка serializer
- Критерий готовности: U+0085/U+2028/U+2029 проходят Begin/read, workspace имеет явную политику допустимости.
- Источник: [Аудит T05](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/DATA_AND_CONTRACTS.md:54)
