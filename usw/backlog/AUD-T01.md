# AUD-T01 — Текст неизвестного YAML-поля становится управляющими настройками

- Статус: исправлено
- Приоритет: P2
- Категория: находка аудита
- Действие: Не интерпретировать вложенный текст неизвестного scalar как top-level configuration; проверять отступы.
- Условие возврата: следующая правка parser
- Критерий готовности: notes не меняет flows.root/handoff, неподдержанный block scalar явно отклонён либо непрозрачен.
- Источник: [Аудит T01](/Users/leonidkim/Documents/projects/usw/usw/reviews/skills-prompts-audit-2026-10-03/DATA_AND_CONTRACTS.md:9)
- История: исходный статус — backlog; выбран change `reject-invalid-config-scalar-structure`.
- Результат: parser отклоняет неподдерживаемый block scalar и вложенную структуру под scalar до managed writes; допустимые неизвестные поля не меняют настройки.
- Основание: change `reject-invalid-config-scalar-structure`; [main spec](../../openspec/specs/workspace-configuration/spec.md), [регрессионные тесты](../../tests/test_init_usw.py) и [проверки контракта](../../tests/test_package_layout.py).
