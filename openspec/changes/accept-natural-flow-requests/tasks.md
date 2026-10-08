# Tasks

## 1. Активация и контракт

- [x] 1.1 Записать baseline старых инструкций и обновить package contract tests
  для native selection, guards и матрицы. DoD: новые требования дают ожидаемый
  FAIL до правки продукта. Proof: отчёт baseline и failing тесты.
- [x] 1.2 Обновить description, начальную активацию и metadata find/assess;
  нормализовать обычную просьбу перед прежним разбором аргументов.
  DoD: прямые просьбы принимаются, упоминания не активируют, неясный объект
  уточняется, read-only границы сохранены. Proof: passing tests и адресное
  наблюдение положительных/отрицательных запросов.
- [x] 1.3 Добавить матрицу шести skills в README и синхронизировать main specs.
  DoD: metadata и границы полномочий согласованы, handoff остаётся ручным.
  Proof: package tests и сравнение delta/main requirements.

## 2. Проверка

- [x] 2.1 Добавить activation evals direct/mention/generic/ambiguous с
  нейтральной вводной. DoD: scenarios загружаются без ложного предположения
  о вызове skill. Proof: harness result и явно записанные ограничения.
- [x] 2.2 Прогнать адресные и полные tests, behavior evals, strict change,
  diff check и независимое ревью. DoD: старые сбои отделены, результаты
  prompt acceptance и native discovery различены, AUD-I07 обновлён честно.
  Proof: verification.md и raw reports.
