## 1. LF-инвариант и байт-точный staging

- [x] 1.1 Добавить падающие тесты: text/text=auto с CR или CRLF отклоняется; `-text` binary с `0D 0A` принимается; inspect повторно проверяет LF-инвариант.
- [x] 1.2 Реализовать классификацию text по `git check-attr --source=<head>` и консервативной auto-эвристике; выдавать `TEXT_EOL_NOT_LF` с путями.
- [x] 1.3 Заменить `git add -A` в `apply_to_repo` на `hash-object -w --no-filters --stdin` + `update-index --cacheinfo`/`--force-remove`; проверить фокусные тесты.

## 2. Preflight в воспроизведённой среде

- [x] 2.1 Добавить падающие тесты: `eol=crlf` только в `.git/info/attributes`, `autocrlf=true` и смена `.gitattributes` на CRLF-политику отклоняются до мутации target; `unchanged` сравниваются по фактическим байтам target.
- [x] 2.2 Реализовать перенос `.git/info/attributes` и ключей `core.autocrlf|eol|safecrlf|symlinks|ignorecase|filemode` в disposable-клон до checkout; сравнение `unchanged` по worktree-байтам target.
- [x] 2.3 Проверять итоговые `text`/`eol`, config, физические LF-байты и весь tracked-worktree; в preflight — `UNSAFE_STOP/LF_WORKTREE_UNSUPPORTED`, на реальном apply — транзакционный откат.

## 3. Классификация и patch-маршрут

- [x] 3.1 Тесты: LF-патч проходит `git apply --cached`, но target с CRLF-политикой даёт отдельный статус и ненулевой код выхода; `CONVERGED_STAGED` требует обоих доказательств.
- [x] 3.2 Перевести blob-контракт patch-валидации на `apply --cached` в disposable-индексе; отдельная worktree-проверка со своим полем статуса; статус `INDEX_CONTRACT_ONLY`.

## 4. Whitespace-диагностика и rollback

- [x] 4.1 Тесты: LF-файл с `<<<<<<< HEAD` даёт `whitespace_findings`, чистый LF не даёт находок, ошибка запуска Git остаётся блокирующей.
- [x] 4.2 Сделать найденные дефекты стандартного `diff --check` неблокирующими во всех трёх скриптах; сбой самой проверки — блокирующий.
- [x] 4.3 Тест ошибки отката: отчёт с `real_target_modified: true` и незавершённым rollback; захваченный commit в `restore_backup` и в команде отката вместо `HEAD`.

## 5. Транспорт и согласование

- [x] 5.1 Тесты: `.sync` с UTF-8 BOM принимается всеми reader'ами; UTF-16LE — явное сообщение про кодировку; `bundle_sha256` не переосмыслен.
- [x] 5.2 Реализовать срез BOM и детект UTF-16 в `repo_sync.read_bundle`, `repo_snapshot_sync.read_snapshot`, `validate_sync_bundle`.
- [x] 5.3 Обновить `SKILL.md` и references: таблица статусов, новые stop-условия, границы preflight (фильтры/`working-tree-encoding` ловятся постпроверкой, не переносом).

## 6. Приёмка

- [x] 6.1 Прогнать оба тестовых модуля скилла и зафиксировать ноль падений; убедиться, что LF-only, binary `-text`, CRLF-policy target, cached-only, отказ rollback и BOM/UTF-16 покрыты по одному тесту каждый.
- [ ] 6.2 `openspec validate --all --strict`; проверить неизменность идентификатора/версии/контейнера и чтение legacy-бандлов.
  Текущий change проходит strict-валидацию; общий прогон блокируют несвязанные
  `support-packaged-flows` и `support-windows-execution`. Legacy patch/snapshot
  и неизменные `repo-sync-*-v1` покрыты тестами.

## 7. Замечания внешнего критического ревью

- [x] 7.1 Перепроверять snapshot `text` по содержащимся в нём tracked `.gitattributes`; тест поддельного `text:false`.
- [x] 7.2 Не приписывать patch-бандлу несвязанный legacy CRLF target; отдельный `ATTRIBUTE_SCOPE_MISMATCH` для невключённого `-text`.
- [x] 7.3 Разрешить legacy CRLF→LF patch по фактическому postimage вместо CR во всём patch-тексте.
- [x] 7.4 Перевести `index_inventory` и snapshot `index_files` на `cat-file --batch`; тест одного batch-процесса.
- [x] 7.5 Не блокировать whitespace findings из-за advisory stderr; сохранять контекст receipt при отказе rollback.
- [x] 7.6 Разделить EOL-политику и физическое несовпадение байтов: не-EOL отказ worktree классифицируется как `WORKTREE_INCOMPATIBLE`; отказ отката в disposable-клоне не заявляет мутацию реального target; регрессионный тест на коллизию регистра.
