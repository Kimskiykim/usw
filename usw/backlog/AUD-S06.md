# AUD-S06 — Pathname lock открывает заранее существующую ссылку

- Статус: backlog
- Приоритет: P2
- Категория: находка аудита
- Действие: Защитить pathname lock от заранее существующих links/reparse points и неверного типа.
- Условие возврата: следующая правка locking
- Критерий готовности: dangling link не создаёт внешний файл, есть native Windows regression. Имеющееся доказательство — macOS filesystem с fake locking, не Windows exploit.
- Источник: [Аудит S06](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md:68)
