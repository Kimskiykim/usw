---
owner: maintainer
updated: 2026-09-01
---
# Anti-patterns

## Deprecated / снятое

- `--experimental-structured`, `.usw/FLOW.json` и внутренние команды снятого
  structured runtime — отклонять до mutation; код живёт только в
  `research/structured-runtime/` и не устанавливается.
- Generic single-state `HANDOFF.md` — legacy; мигрирует в router при первом
  обращении, новый код пишет только routed-форму.

## Чего не делать

- Не выдумывать capabilities: `CALL SKILL` только для skill, явно
  названного и присутствующего в текущем списке available skills.
- Не переводить contract tokens (`approve`, `change`, `blocked`…) —
  человек вводит их дословно.
- Не использовать маркеры `CALL`/`GATE`/`LOOP`/`PARALLEL` в обычном
  Markdown flow — только в `version-2`.
- Не имитировать todo-инструмент markdown-чек-листом — если инструмент
  недоступен, останавливаться со статусом `blocked`.
- Не пересказывать спеки в производных текстах (skills, README, context) —
  ссылаться на спеку.
- Не мигрировать раскладку flow (`<name>.md` ↔ `<name>/FLOW.md`)
  автоматически и не менять стиль существующего flow без явной просьбы.
- Не публиковать review finding без конкретного evidence.
- Не добавлять «robustness» для неподдерживаемых сценариев и слои «на
  будущее» без подтверждённого use case.

## На чём спотыкаются

- Правят skill, забывая, что источник — спека: правка перегенерируется или
  разойдётся. Сначала спека (через change), потом производные.
- Правят нормативный текст и молча ломают stable-token тесты — токены
  контрактны.
