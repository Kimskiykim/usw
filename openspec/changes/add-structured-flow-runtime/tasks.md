## 1. Structured parser

- [x] 1.1 Добавить version-aware data model и сохранить parser версии 1
- [x] 1.2 Разобрать канонические typed calls, постоянные имена и subagent payload
- [x] 1.3 Разобрать и проверить GATE, LOOP и PARALLEL control blocks

## 2. Runtime orchestration

- [x] 2.1 Разрешать exact typed executors и передавать invocation payload
- [x] 2.2 Исполнять gate transitions и bounded loop state по одной boundary
- [x] 2.3 Исполнять PARALLEL после полного preflight и агрегировать outcomes
- [x] 2.4 Сохранить и восстановить version-2 cursor и loop counters

## 3. Contract and documentation

- [x] 3.1 Обновить `usw-run-flow` для executable version-2 и composite executors
- [x] 3.2 Уточнить canonical runtime форму в `usw-create-flow` reference и README
- [x] 3.3 Расширить CLI validation report для обеих версий

## 4. Verification

- [x] 4.1 Покрыть parser всеми CALL types и invalid structured contracts
- [x] 4.2 Покрыть gate, loop, parallel, subagent payload и resume runtime tests
- [x] 4.3 Запустить полную регрессию и строгую OpenSpec validation
