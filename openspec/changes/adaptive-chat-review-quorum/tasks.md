## 1. Зафиксировать contracts тестами

- [x] 1.1 Добавить failing text-contract tests для adaptive `chat-review`.
  - Результат: tests требуют review profiles, `--reviewers auto|2|3`, rubric,
    explicit votes, bounded third reviewer и per-finding human decisions.
  - Готово, когда: новые assertions падают на текущем `chat-review` по
    отсутствующим contract fragments.
  - Проверка: запустить targeted unittest → ожидаемый результат `FAIL` только
    по новым требованиям.

- [x] 1.2 Добавить failing dependency-closure test для packaged examples.
  - Результат: test извлекает dependency declarations и literal
    `CALL SKILL`, принимает declared external и требует bundled skill в package
    и standalone installer.
  - Готово, когда: текущие undeclared references дают диагностируемый failure,
    а test не разбирает control flow.
  - Проверка: запустить targeted unittest → ожидаемый результат `FAIL` со
    списком undeclared либо unavailable dependencies.

## 2. Обновить review-flow

- [x] 2.1 Добавить dependency blocks в canonical packaged examples.
  - Зависит от: 1.2.
  - Результат: `chat-review` объявляет bundled review executor и command
    profile; `dev-test` объявляет существующий `ponytail-review` как external
    без изменения обязательности вызова.
  - Готово, когда: dependency-closure test проходит, а external dependency не
    добавлена в USW installer.
  - Проверка: targeted dependency unittest → `OK`; diff installer не содержит
    `ponytail-review`.

- [x] 2.2 Переписать shared `chat-review` на adaptive review contract.
  - Зависит от: 1.1.
  - Результат: runnable flow выбирает initial budget 2/3, выполняет independent
    discovery, explicit voting, максимум один tie-break reviewer и отдельные
    human decisions.
  - Готово, когда: все ветки завершаются `completed` либо
    `decision_required`, число reviewer-ов не превышает трёх и review остаётся
    read-only.
  - Проверка: targeted text-contract unittest → `OK`; ручная проверка Markdown
    подтверждает отсутствие четвёртого reviewer-а и implementation actions.

- [x] 2.3 Синхронизировать canonical packaged `chat-review` с adaptive
  contract.
  - Зависит от: 2.1, 2.2.
  - Результат: ненормативный example содержит тот же review contract и
    copy-before-use warning.
  - Готово, когда: semantic contract shared flow и template совпадает, но
    existing initialized copies не перезаписаны.
  - Проверка: flow scenario/package tests → `OK`; `git diff` не содержит
    изменений под существующими `<flows.root>/examples/`.

## 3. Проверить change

- [x] 3.1 Выполнить focused и полный regression suite.
  - Зависит от: 2.1, 2.2, 2.3.
  - Результат: сохранён фактический результат проверок implementation.
  - Готово, когда: shell/package/flow tests и полный unittest suite завершаются
    без failures.
  - Проверка: `python3 -m unittest tests.test_install
    tests.test_flow_scenarios tests.test_package_layout` и
    `python3 -m unittest discover -s tests` → `OK`.

- [x] 3.2 Проверить OpenSpec и итоговый scope.
  - Зависит от: 3.1.
  - Результат: change валиден, а diff содержит только согласованные flow,
    example и test changes.
  - Готово, когда: OpenSpec validation проходит; runtime, handoff protocol и
    existing initialized examples не изменены.
  - Проверка: `openspec validate adaptive-chat-review-quorum --type change
    --strict` и `git diff --check` → успешно; ручной scope review → без лишних
    файлов.

## За пределами плана

- Автоматическая установка external skills.
- Parser, scheduler, normalized plan или machine voting state.
- Автоматический запуск implementation после review.
- Перезапись существующих initialized examples.
