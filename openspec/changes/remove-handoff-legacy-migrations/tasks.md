# План удаления миграций HANDOFF

## 1. Отказ от старых форматов

- [x] 1.1 В `tests/test_handoff_state.py` заменить migration/upgrade сценарии
  проверками отказа single-state и старых operation documents всеми командами,
  включая Save candidate; перевести положительные fixtures на router. Проверка:
  адресные тесты сначала падают из-за принятия старого формата.
- [x] 1.2 В `handoff_state.py` удалить single-state преобразование, старую форму
  operation parser, enrichment Outcome/Save и migration install mode. Проверка:
  `python3 -m unittest tests.test_handoff_state tests.test_platform_support -v`
  проходит, негативные сценарии сохраняют router/documents/candidates.
- [x] 1.3 Синхронизировать delta `live-operation-state` в main spec; согласовать
  handoff skill/reference, anti-patterns и README с отказом от совместимости.
  Проверка: поиск обещаний миграций в действующих исходниках, stable-token тесты
  и запуск behavior evals после изменения SKILL.md с явным отчётом ограничений.

## 2. Интеграционная проверка

- [x] 2.1 Прогнать `python3 -m unittest discover -s tests -v`,
  `openspec validate --all --strict` и `git diff --check`. Критерий:
  новых сбоев относительно HEAD нет, адресные тесты и строгая валидация change
  проходят; ограничения полного набора и eval явно записаны.
- [x] 2.2 Удалить выполненный R4 из `.usw/BACKLOG.md` после проверки; записать
  результаты в `verification.md` этого change. Проверка: R4 не остаётся
  открытой задачей, сохранены остальные решения текущего обсуждения.

## Workflow follow-up

- Архивировать change после проверки по отдельному запросу владельца.
