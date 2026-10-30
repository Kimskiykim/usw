# AUD-F15 — Принятие одного review gate может обойти результат второго. Дефект перехода

- Статус: принято
- Приоритет: P2
- Категория: находка аудита
- Действие: Добавить общий барьер двух review gates одной версии артефактов в opsx-intent2spec.
- Условие возврата: новые подтверждённые проблемы или отдельное решение о непроверенных сценариях
- Критерий готовности: решение одного gate не обходит pending второго; явно принятое владельцем исключение/риск сохраняется, без нового требования обязательно двух passed.
- Источник: [Аудит F15](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/REVIEW.md:132)
- Подтверждение: реальные случаи принятого drift/incomplete и oversized/incomplete остановились до шага 8; после разрешения обоих gate на неизменной редакции шаг 8 сохранил риски. При правке B проведены оба новых review. [Runtime-сводка](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-f15-incomplete-2026-10-31/runtime-report-for-critic.md), [отзыв критика](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-f15-incomplete-2026-10-31/runtime-critic-final.md), [приёмка](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-f15-incomplete-2026-10-31/acceptance.md).
- Граница: pending, manual/stuck, попытка перенести старый verdict, полный OpenSpec-путь и экономия не проверены. Приёмка относится к проверенному барьеру.
