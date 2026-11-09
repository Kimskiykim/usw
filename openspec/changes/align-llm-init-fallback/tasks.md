# Tasks

## 1. AUD-F08a — partial write

- [x] 1.1 Наблюдать старый fallback и добавить failing stable-token тест
  очистки нового incomplete file. Исправить только обработку сбоя.
  DoD: разрешена очистка лишь своего недописанного файла, остальные файлы
  сохраняются. Proof: baseline, отдельный тест и повторное наблюдение.

## 2. AUD-F08b — существующий HANDOFF

- [x] 2.1 Добавить failing stable-token тест разделения нового и существующего
  HANDOFF; исправить preflight snapshot и финальную проверку.
  DoD: повторный init допускает непустой router и operation directory,
  сохраняя байты. Proof: тест и отдельное сравнение byte snapshot.

## 3. AUD-I06 — обещания init

- [x] 3.1 Уточнить roots, metadata и границу fallback в skill/reference.
  DoD: разрешён containment flow/review внутри artifact root без взаимного
  overlap, lazy templates не обещаны, остальные skills требуют Python.
  Proof: failing затем passing package contract test и сверка с runtime.

## 4. Интеграционная проверка

- [x] 4.1 Добавить адресные eval fixtures, прогнать package/init тесты,
  полный unittest suite, behavior evals, strict validation и diff check;
  выполнить независимое ревью. DoD: результаты и ограничения записаны в
  verification.md; карточки обновлены по подтверждённому объёму.
  Proof: свежий отчёт, baseline и проверка файлов после модельного наблюдения.
