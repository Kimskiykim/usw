# AUD-T07 — Custom discovery может не предоставить данные для обязательного voting

- Статус: принято
- Приоритет: P2
- Категория: статический контракт
- Действие: Определить минимальный смысл custom review output: findings с evidence либо clean/incomplete.
- Условие возврата: новые подтверждённые проблемы или отдельное решение о непроверенных сценариях
- Критерий готовности: count-only/PASS-FAIL контракт уточняется до discovery, корректные findings доступны voting. Фактический false accept не измерен.
- Источник: [Аудит T07](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/DATA_AND_CONTRACTS.md:70)
- Подтверждение: выполнена ограниченная правка custom-контракта; пять свежих случаев проверили остановку несовместимых контрактов до discovery, clean из init-примера, incomplete и переход findings к voting. [Runtime-сводка](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-t07-fresh-2026-10-31/runtime-report-for-critic.md), [отзыв критика](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-t07-fresh-2026-10-31/runtime-critic-final.md), [приёмка](/Users/leonidkim/Documents/projects/usw/.usw/state/usw-aud-t07-fresh-2026-10-31/acceptance.md).
- Граница: фактические false accept rate и экономия не измерены; native UI slash-dispatch не проверен. Решение owner, итоговый implementation handoff и остальные профили не проверены.
