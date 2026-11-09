# AUD-S04 — Initializer после проверки parent записывает через подменённую ссылку

- Статус: backlog
- Приоритет: P2
- Категория: находка аудита
- Действие: Перевести initializer на общий safe-access слой для создания файлов/каталогов.
- Условие возврата: следующая правка init
- Критерий готовности: POSIX parent-symlink swap после preflight не создаёт внешних файлов; ограничение pathname backend раскрыто.
- Источник: [Аудит S04](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/SECONDARY_AUDITS.md:52)
