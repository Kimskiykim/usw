# Задача 2.2: Определить безопасный replanning и reopening coding task

## Результат

Planning workflows изменяют оставшуюся работу, не удаляя завершённые факты, не
выдавая stale evidence за актуальное и сохраняя правдивый checkbox coding task
после blocking findings.

## Область

- Определить замену pending steps и сохранение completed-step history.
- Помечать evidence как stale при изменении source или definition of done.
- Повторно открывать ту же coding task при blocking finding внутри исходного
  `task.md` и повторно закрывать только после repair и required checks.
- Использовать Git history и reviewer receipts для хронологии без отдельного
  reopen status.
- Требовать user approval до создания задачи для независимого нового scope.
- Добавить fixtures для unchanged, partially completed, stale-evidence,
  in-scope reopening и new-scope scenarios.

## Вне области

- Универсальные Git diff heuristics сверх принятой source-identity boundary.
- Автоматическое решение, является ли предложение новым независимым scope.
- Выполнение replacement plan steps.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/execution-artifacts/spec.md`

## Зависимости

- Задача 2.1.

## Критерии готовности

- Replanning не удаляет completed-step history или executed evidence.
- Затронутое evidence сохраняется как stale с явным required rerun.
- Blocking in-scope finding меняет `[x]` обратно на `[ ]` для той же task.
- Новый независимый scope не создаётся без user approval.

## Проверка

- Запустить: `python3 -m unittest tests.test_replanning -v`
- Ожидание: preservation, staleness, reopening и new-scope boundaries проходят.
