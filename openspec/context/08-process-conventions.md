---
owner: maintainer
updated: 2026-09-01
---
# Process Conventions

Конвенции процесса разработки: рабочие файлы, журналы, слои видимости.
Как писать код и запускать проверки — в `04-engineering-standards.md`.

## Рабочие файлы и журналы

- Временные материалы любого процесса (decision log, черновики, scratch) —
  в developer-local `.usw/state/<процесс>/<slug>/` (gitignored).
- Decision log — один `decision-log.md` на процесс, append-only: записи
  дописываются в конец, не переписываются и не удаляются.
- Находки «полезно, но вне scope текущей задачи» — в `.usw/BACKLOG.md`.
- Flow и skills ссылаются на эту конвенцию, а не переопределяют её;
  специфичный состав своего state каждый flow описывает у себя.
- Нормативная часть `.usw/` (HANDOFF.md, handoffs/) определена спекой
  live-operation-state — здесь не пересказывается.

## Перенос из `.usw/` в видимый слой

Материал из developer-local `.usw/` переносится в project-видимый слой
только явным действием, по типу материала:

- **flow**: `.usw/flows/<name>` → `usw/flows/<name>` тем же текстом
  (`$usw-create-flow --shared`); после переноса локальную копию удалить,
  иначе она затеняет общую при discovery;
- **пункт бэклога**: создать OpenSpec change (интент) либо перенести строку
  в общий `usw/BACKLOG.md` с сохранением условия возврата;
- **решение из decision log**: не копировать лог целиком — дистиллировать
  в `openspec/context/ADR/` (пережившее change) или в `design.md` change
  (scoped); сырой лог остаётся локальным и append-only.
