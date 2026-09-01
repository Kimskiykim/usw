## Why

Перенос `.sync`-бандлов на Windows-зеркала даёт устойчивые EOL-отказы. Новый
контракт намеренно поддерживает только LF для текстовых файлов: канонический
текстовый blob с CR/CRLF отклоняется, а target обязан стабильно
материализовать такие пути с LF. Binary-пути с эффективным `-text` остаются
байт-точными и могут содержать произвольные байты. Disposable-клон должен
воспроизводить локальный конфиг и `.git/info/attributes` target; успешная
проверка индекса сама по себе не доказывает LF-совместимость worktree.

## What Changes

- На export/inspect определять текстовые пути по атрибуту `text`; для
  `text=auto`/unspecified применять консервативную проверку содержимого, а
  эффективный `-text` считать binary. Любой CR в текстовом blob — явный
  `UNSAFE_STOP/TEXT_EOL_NOT_LF`.
- Snapshot-staging перевести на байт-точный путь: `git hash-object -w
  --no-filters --stdin` (включая содержимое symlink-блобов через stdin) плюс
  `git update-index --cacheinfo` / `--force-remove`, минуя eol-конвертацию и
  `core.filemode`.
- Добавить LF-preflight в достоверно воспроизведённой среде: disposable-клон с
  копией релевантного локального конфига, `.git/info/attributes` и фактических
  worktree-байтов `unchanged`-файлов реального target. `autocrlf=true`,
  `eol=crlf` либо иная итоговая политика, способная материализовать текст не
  как LF, — явный `UNSAFE_STOP/LF_WORKTREE_UNSUPPORTED` до мутации target.
- После staging проверять отсутствие unstaged-расхождений всего
  tracked-дерева под итоговыми атрибутами, не доверяя stat-кешу; успех только
  индексного контракта без доказанного worktree не классифицировать как
  полную готовность.
- Patch-маршрут: blob-контракт проверять через `git apply --cached` в
  disposable-индексе; применимость к реальному worktree — отдельная проверка
  с собственным статусом в отчёте.
- `diff --check`: найденные whitespace-дефекты сделать неблокирующей
  диагностикой со стандартной фиксированной политикой инструмента;
  ошибки запуска Git или чтения индекса остаются блокирующими.
- Rollback: автоматический откат и выдаваемая команда используют захваченный
  исходный commit, а не подвижный `HEAD`; при отказе отката отчёт обязан
  сообщать `real_target_modified: true` и незавершённость отката.
- Транспорт: принимать UTF-8 BOM во всех трёх reader'ах; UTF-16 — явный отказ
  с понятным сообщением; идентификатор/версия и контейнер бандла, а также
  смысл `bundle_sha256` не меняются. Новый reader принимает старые snapshot
  без добавленного поля `text`.
- Согласовать `validate_sync_bundle.py` с теми же правилами клонирования и
  диагностики.

## Capabilities

### New Capabilities

- `external-sync-bundles`: гарантии байт-точной конвергенции, preflight-среды,
  классификации отчётов и rollback для `.sync`-инструментов.

### Modified Capabilities

Нет.

## Impact

- `dev/skills/export-external-sync-bundles/scripts/repo_snapshot_sync.py`:
  staging, preflight, постпроверка worktree, rollback, транспорт.
- `dev/skills/export-external-sync-bundles/scripts/sync_workflow.py` и
  `validate_sync_bundle.py`: cached-валидация, неблокирующий whitespace,
  клонирование среды.
- `dev/skills/export-external-sync-bundles/references/*.md` и `SKILL.md`:
  таблица статусов и новые stop-условия.
- Тесты `test_snapshot_sync.py` / `test_sync_tools.py`: регрессионные
  EOL-сценарии; часть выполнима только при доступном Git с нужными
  настройками, Windows-специфика — через конфиг-эмуляцию на POSIX.
