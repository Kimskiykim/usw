# Задача 2.2: Определить безопасный replanning и reopening coding task

## Artifact model

- `legacy`

## Результат

Workflows изменяют оставшуюся работу, не удаляя завершённые факты, не
выдавая stale evidence за актуальное и сохраняя правдивый checkbox coding task
после blocking findings.

## Область

- Определить замену pending operations текущей сессии и сохранение подтверждённых
  facts, task Milestone log, evidence и receipts.
- Отличать изменение локальных operations от новой revision стабильного task
  contract.
- При изменении contract revision или task source identity помечать всё
  Development и Testing evidence задачи stale без частичного dependency analysis
  и без mutation role-owned entries.
- Вычислять current/stale сравнением сохранённых evidence identities с текущими
  contract revision и source identity задачи.
- Реализовать canonical full-product-tree manifest без commit OID для конечного
  tracked/untracked worktree state.
- Реализовать точную `USW-SOURCE-V1` binary serialization: normalized UTF-8 NFC
  paths, unsigned byte sorting, big-endian lengths, kind byte, payload length и
  raw SHA-256 payload digest; отклонять unsafe paths и normalization collisions.
- Исключать `.git`, `.usw` и configured workflow roots, чтобы workflow writes не
  меняли source identity.
- Повторно открывать ту же coding task при blocking finding внутри исходного
  `task.md` и повторно закрывать только после repair и required checks.
- Добавлять новую attempt в Milestone log и новый receipt, сохраняя прежние
  evidence и receipts без отдельного reopen status.
- Требовать user approval до создания задачи для независимого нового scope.
- Добавить fixtures для unchanged, partially completed, stale-evidence,
  in-scope reopening и new-scope scenarios.

## Вне области

- Универсальные Git diff heuristics сверх принятой source-identity boundary.
- Автоматическое решение, является ли предложение новым независимым scope.
- Выполнение replacement operations.

## Ссылки

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/execution-artifacts/spec.md`

## Зависимости

- Задача 2.1.

## Критерии готовности

- Replanning не удаляет подтверждённые facts, Milestone log или executed evidence.
- Изменение только порядка operations не меняет contract revision.
- Изменение contract revision или task source identity сохраняет всё evidence
  задачи как stale и требует полного rerun обязательных Development/Testing checks.
- Invalidation Testing evidence не предоставляет Development write authority на
  `testing-evidence.md`.
- Одинаковый worktree product state даёт стабильный digest; изменение любого
  включённого product file меняет digest, а workflow-only change — нет.
- Workflow-only commit с новым HEAD не меняет digest; staged/unstaged, executable
  mode, symlink target и Git-visible untracked cases покрыты fixtures.
- Blocking in-scope finding меняет `[x]` обратно на `[ ]` для той же task.
- Новый независимый scope не создаётся без user approval.

## Проверка

- Запустить: `python3 -m unittest tests.test_replanning -v`
- Ожидание: preservation, staleness, reopening и new-scope boundaries проходят.
