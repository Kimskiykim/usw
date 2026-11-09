# AUD-F07 — Готовые flow не всегда переносятся в обычный установленный проект. Дефект пути зависимости

- Статус: принято
- Приоритет: P2
- Категория: находка аудита
- Действие: Разрешать установленную команду отдельно от package resource; dependency критика сделать условной для llm-critic profile.
- Условие возврата: новые подтверждённые проблемы или отдельное решение о непроверенных сценариях
- Критерий готовности: flat/package примеры работают в проекте без checkout USW, custom не требует лишнего критика.
- Источник: [Аудит F07](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/REVIEW.md:84)
- Подтверждение: точечная приёмка трёх свойств: полный установленный prompt в `llm-critic`, `custom` при наблюдаемом OS-denial prompt и применение полного prompt в актуальном `opsx` gate 7.2. [Приёмка](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-f07-fresh-2026-10-31/acceptance.md), [отзыв критика](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-f07-fresh-2026-10-31/runtime-critic-final.md).
- Граница: Qwen/GigaCode runtime, native discovery/UI slash, полный flow и OpenSpec lifecycle не проверены; экономия и false accept rate не измерены. Отклонения исполнения раскрыты в [отчёте](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-f07-fresh-2026-10-31/report.md); безошибочное исполнение не утверждается.
