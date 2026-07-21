# Задача 1.2: Переключить инициализацию на standalone default

## Artifact model

- `legacy`

## Результат

`/usw-init` по умолчанию создаёт standalone shared workspace и воспринимает
существующий OpenSpec workspace только как неразрушающую opt-in подсказку.

## Область

- Обновить initialization scripts, templates, commands и отчёты.
- Создавать отсутствующие `usw.yaml`, `usw/changes`, `usw/refinements`,
  `usw/flows` и `usw/reviews`.
- Сохранить игнорируемый `.usw/HANDOFF.md` как developer-local state.
- Обнаруживать существующие OpenSpec files и доказывать, что они остаются
  byte-for-byte неизменными.

## Вне области

- Автоматический opt-in в OpenSpec provider.
- Миграция OpenSpec content в standalone artifacts.
- Создание change, task или review receipt при initialization.
- Наполнение `usw/flows` normative scenarios до появления scenario assets в
  задаче 3.1; эта задача создаёт безопасный пустой flow root.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/workspace-configuration/spec.md`

## Зависимости

- Задача 1.1.

## Критерии готовности

- Новый проект получает standalone provider и все default roots.
- До задачи 3.1 flow root может быть пустым и не использует неявные scenarios.
- Повторная initialization идемпотентна и не перезаписывает files.
- Существующий OpenSpec workspace только показывается пользователю.
- Unsafe paths и tracked developer-local state приводят к отказу без записи.

## Проверка

- Запустить: `python3 -m unittest tests.test_init_usw.InitializeUswTests -v`
- Ожидание: проходят standalone creation, idempotence, OpenSpec preservation,
  review-root creation, privacy и path-safety scenarios.
