## 1. Контракт отказа

- [x] 1.1 Заменить role-based recovery-тесты проверкой `invalid_handoff` без изменения HANDOFF и operation files для parser и команд; подтвердить, что новые тесты падают на прежнем runtime.

## 2. Runtime и тексты

- [x] 2.1 Удалить role-based parser, ветки команд и `legacy` из CLI-ответов; проверить `python3 -m unittest tests.test_handoff_state tests.test_end_to_end -v`.
- [x] 2.2 Удалить role-based инструкции из product skills и reference без применения общего сокращения скилла; проверить поиском, что актуальные product-тексты не обещают поддержку старого формата, и запустить `python3 evals/run_evals.py`.
- [x] 2.3 Обновить stable-token/контрактные тесты для нового нормативного поведения; проверить `python3 -m unittest tests.test_atomic_skill_contracts -v`.

## 3. Интеграция

- [x] 3.1 Проверить `openspec validate remove-role-based-handoff --strict` и полный `python3 -m unittest discover -s tests -v`; убедиться, что generic single-state миграция остаётся зелёной.
