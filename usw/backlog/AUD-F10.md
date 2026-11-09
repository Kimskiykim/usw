# AUD-F10 — Условие завершения review-fix-and-backlog слабее его обязательств. Дефект контракта

- Статус: принято
- Приоритет: P2
- Категория: находка аудита
- Действие: Завершать review-fix-and-backlog только после всех FIX NOW и успешных обязательных проверок.
- Условие возврата: новые подтверждённые проблемы или отдельное решение о непроверенных сценариях
- Критерий готовности: nonblocking FIX NOW и failed check остаются видимыми препятствиями завершению.
- Источник: [Аудит F10](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/REVIEW.md:102)
- Подтверждение: чистое завершение и `partial` с оставшимся FIX NOW после двух циклов при ограниченном бюджете; [evidence](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-f10-controlled-2026-10-29/negative-run-report.md), [отзыв критика](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-f10-controlled-2026-10-29/critic-acceptance.md).
- Граница: отдельный живой случай с упавшей обязательной проверкой после двух циклов и типичность исчерпания не подтверждены; условие failed check проверено статически.
