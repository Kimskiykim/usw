---
owner: maintainer
updated: 2026-09-01
---
# Start Here — USW

USW — устанавливаемый standalone workflow для Qwen Code, Codex и Claude Code:
именованные Markdown flow, исполняемые моделью как текст, плюс routed handoff.

## Перед любой задачей

1. Прочитать `01-product-context.md`, `02-domain-glossary.md`,
   `07-anti-patterns.md`.
2. Для design — дополнительно `03-architecture.md` и релевантные `ADR/`.
3. Для tasks — дополнительно `04-engineering-standards.md` и
   `06-testing-and-quality.md`; для работы с журналами, бэклогом и
   `.usw/` — `08-process-conventions.md`.
4. Не хватает контекста — не угадывать, явно назвать, какого.

## Главные запреты

- Спеки в `openspec/specs/` нормативны. Расходится skill/код со спекой —
  чинить производное, не спеку (кроме осознанного change спеки).
- У факта ровно один дом: кросс-катящий — здесь, специфичный для
  capability — в её спеке. Ссылаться можно, пересказывать нельзя.
- Не изменять `.gigacode/`, `.claude/` и другие сгенерированные файлы
  skills — кастомизация только через `openspec/config.yaml` и исходники.
- Text-first: не превращать flow-нотацию в machine DSL.
- Изменения вне scope текущей задачи не делать.
