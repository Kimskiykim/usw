## 1. Resolver-owned authoring target

- [x] 1.1 Add focused failing tests for default/custom shared roots, explicit local origin, both existing layouts, a new package, ambiguity, unexpected types and symlinks at root/package/entrypoint positions.
- [x] 1.2 Load the existing workspace config parser from `run_flow.py` and implement `prepare-write` with immutable Markdown, exact target metadata and a state-bound write token; verify focused preparation tests.

## 2. Revalidated atomic write

- [x] 2.1 Add focused failing tests for flat/package updates, package creation, preserved sibling resources, stale content/layout/config, invalid UTF-8 input and JSON CLI errors.
- [x] 2.2 Implement `write` through the shared safe-access boundary with token validation, immediate layout recheck, same-directory atomic replacement and read-back; verify focused writer and platform tests.

## 3. Skill and eval contracts

- [x] 3.1 Add stable-token tests requiring `usw-create-flow` to compute no root/layout/symlink decisions itself and to call `prepare-write` and `write`.
- [x] 3.2 Replace only the entrypoint-selection and write-safety sections of `usw-create-flow` with the resolver commands; preserve drafting, agreement, complexity, report and design-scan behavior.
- [x] 3.3 Add `create-default-shared` and `create-custom-flows-root` eval scenarios with filesystem expectations under their resolved shared roots; validate scenario loading.

## 4. First-slice acceptance

- [x] 4.1 Run focused resolver, CLI, platform, skill-contract and eval-harness tests and record zero failures.
  - Verification: resolver/platform — 70 tests OK; skill/eval/package contracts — 90 tests OK.
- [x] 4.2 Run `python3 -m unittest discover -s tests`, strict OpenSpec validation and change verification; record results and confirm no new script or design-scan change.
  - Verification: Python 3.11.9 and bundled Python 3.12.13 — 265 tests OK on each; `openspec validate --all --strict` — 20 passed; `git diff --check` — clean; no new script and no diff in `guided-flow-authoring`.

## 5. Review fixes: lazy roots and no-residue writes

- [x] 5.1 Add focused failing tests: prepare/write for a fresh project without `.usw/flows` (local), without `usw/flows` (shared) and with a configured-but-absent custom `flows.root`; `workspace_not_initialized` when `.usw` is absent; root-existence bound into the token (root appearing between prepare and write → `stale_flow_target`).
- [x] 5.2 Implement lazy-root creation in `write` (shared root component by component inside `<project>`; local `.usw/flows` only inside existing `.usw`) and the `workspace_not_initialized` stop in prepare; reuse the package `make_directory` safety path.
- [x] 5.3 Reject empty or whitespace-only stdin with `empty_flow_content` before any change; replace `secrets.compare_digest` with plain comparison so a malformed or non-ASCII token returns JSON `stale_flow_target` exit 2 (tests for both).
- [x] 5.4 Fix the shared config parser in `init_usw.py`: strip inline comments, build consumer paths from normalized `_root_parts` instead of the raw scalar; regression tests covering `root: x # comment` and `root: usw\flows` for both init and authoring.
- [x] 5.5 Move package `make_directory` after `_assert_write_target`, add non-recursive `SafeDirectory.remove_directory` (ENOTEMPTY tolerated) and remove directories created by a failed attempt so the token stays valid for retry; return `write_unverified` for any failure after the replacement landed (sync, read-back); preserve the replaced entrypoint's mode and create new files/directories with default permissions instead of 0600/0700 — tests for residue cleanup, token-retry, post-replace failure code and permissions.
- [x] 5.6 Update `usw-create-flow/SKILL.md`: suggest `usw-init` on `workspace_not_initialized`, report `write_unverified` as "записано, но не подтверждено", drop the unsatisfiable "другие файлы не изменились" check, replace remaining English prose terms (`selector`, `entrypoint`); harden negative stable-token guards (case-insensitive matching, forbid `flows.root` and `<project>/.usw/flows` in the create skill).
- [x] 5.7 Add an eval scenario authoring into a project without pre-created flow roots; re-run the full suite, `openspec validate --all --strict` and change verification; record results.
- [x] 5.8 Закрыть замечания повторного ревью: вернуть `write_unverified` с `written: true` при Ctrl+C после замены и сохранить исходный код ошибки при сбое удаления созданного каталога; проверить оба способа безопасного доступа регрессионными тестами.

### Проверка секции 5 — 2026-08-27

- Регрессионные тесты сначала воспроизвели отсутствующие корни, затирание пустым
  вводом, сбой не-ASCII токена, неверный разбор конфигурации, остатки каталогов,
  неверные права и ошибки после состоявшейся замены.
- `python3 -m unittest discover -s tests`: Python 3.11.9 — 281 тест, успешно.
- Тот же прогон на доступном Python 3.12.13 — 281 тест, успешно.
- `openspec validate --all --strict`: 20 объектов, успешно.
- `quick_validate.py skills/usw-create-flow`: скилл валиден.
- `git diff --check`: без замечаний.
- Сверка реализации: 2 требования и 20 сценариев дельты сопоставлены с кодом
  и тестами; секция 5 закрыта полностью. Дельта переведена на русский язык.
- Дополнительно воспроизведена и исправлена очистка через подменённый путь:
  проверены оба бэкенда, чужие файлы сохраняются. Возможный остаток временного
  файла при внешнем перемещении каталога явно описан в design и дельте.
- `resolve`/`inspect`/`resource`, проектный разбор и `guided-flow-authoring`
  не менялись; новых скриптов и зависимостей нет.
- Новый `create-missing-flow-root` проходит загрузчик сценариев. Живой прогон
  LLM и запуск на настоящей Windows в этой среде не проводились; путь Windows
  проверен через pathname-бэкенд и существующие платформенные тесты.

### Проверка повторного ревью — 2026-08-28

- До исправления тесты воспроизвели потерю исходного кода ошибки при сбое
  очистки (4 случая) и необработанный `KeyboardInterrupt` после замены.
- После исправления: 15 целевых тестов успешно; полная сьюта — 282/282 на
  Python 3.11.9 и 3.12.13; `openspec validate --all --strict` — 20/20;
  `git diff --check` — без замечаний.

| Проверка | Результат |
| --- | --- |
| Полнота | 17/17 задач; 2 требования и 20 сценариев сопоставлены с реализацией и тестами |
| Корректность | Оба замечания закрыты для descriptor- и pathname-доступа |
| Связность | Исправления соответствуют пункту 5.5; новые скрипты и зависимости не добавлены |

- Блокеров коммита не найдено. До архивации отдельно синхронизировать
  `support-packaged-flows`: главная спека ещё описывает плоскую запись.
- Живой прогон LLM и настоящая Windows не проверялись. Нормализация корней
  в run/find/assess и права shared-файлов init остаются отдельными задачами.
