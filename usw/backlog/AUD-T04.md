# AUD-T04 — Валидатор относительных roots принимает Windows drive paths

- Статус: backlog
- Приоритет: P2
- Категория: находка аудита
- Действие: Отклонять Windows drive-absolute/drive-relative roots до нормализации.
- Условие возврата: следующая правка validator
- Критерий готовности: C:/… и C:relative запрещены, обычный относительный путь работает. Выход записи за проект на native Windows пока не доказан.
- Источник: [Аудит T04](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/DATA_AND_CONTRACTS.md:46)
