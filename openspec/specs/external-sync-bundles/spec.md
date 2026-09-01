# Спецификация external-sync-bundles

## Purpose

Определить проверяемые гарантии LF-only, байт-точного Git staging,
disposable preflight, диагностики и отката для самодостаточных `.sync`-бандлов.

## Requirements

### Requirement: Текстовый контракт допускает только LF

Export и inspect SHALL классифицировать tracked blobs по эффективному
атрибуту `text` канонического дерева. Путь с `-text` SHALL считаться binary и
не проверяться на EOL. Явный `text` SHALL считаться текстовым; `text=auto` и
unspecified без NUL SHALL консервативно считаться текстовыми. Текстовый blob,
содержащий `CR`, MUST быть отклонён с `UNSAFE_STOP/TEXT_EOL_NOT_LF` до
создания пригодного к передаче бандла или до plan/apply.

#### Scenario: Канонический текст содержит CRLF
- **WHEN** tracked text/auto-файл содержит `CRLF`
- **THEN** export останавливается с `TEXT_EOL_NOT_LF` и перечисляет путь

#### Scenario: Binary содержит байты CRLF
- **WHEN** tracked путь имеет эффективный `-text` и содержит `0D 0A`
- **THEN** blob переносится байт-точно и не отклоняется как нарушение EOL

#### Scenario: Snapshot подделывает binary-классификацию
- **WHEN** snapshot объявляет CRLF blob как `text: false`, но итоговые tracked `.gitattributes` не задают пути `-text`
- **THEN** inspect останавливается с `TEXT_EOL_NOT_LF`

#### Scenario: Legacy patch нормализует CRLF в LF
- **WHEN** старый patch без text metadata заменяет CRLF-preimage на LF-postimage
- **THEN** postimage проверяется по итоговому индексу и bundle не отклоняется из-за CR в удаляемом контексте patch

### Requirement: Байт-точный staging сохраняет LF-контракт и режимы

Snapshot-apply SHALL помещать канонические блобы в индекс target через
`git hash-object -w --no-filters --stdin` и `git update-index --cacheinfo`,
удаления — через `git update-index --force-remove`. Содержимое symlink-блобов
MUST подаваться через stdin и никогда не читаться по целевому пути ссылки.
Итоговый индекс MUST байт-точно и по режимам совпадать с LF-каноническим
inventory независимо от `core.safecrlf` и `core.filemode`.

#### Scenario: safecrlf не блокирует staging
- **WHEN** у target установлен `core.safecrlf=true`
- **THEN** staging канонических байтов завершается без `LF would be replaced by CRLF`

#### Scenario: Новый исполняемый файл при filemode=false
- **WHEN** снапшот добавляет файл с режимом `100755`, а у target `core.filemode=false`
- **THEN** индекс записывает режим `100755`

### Requirement: Target обязан стабильно материализовать текст с LF

Preflight SHALL выполняться в disposable-среде, воспроизводящей
`.git/info/attributes` и релевантный эффективный конфиг реального target, и
сравнивать `unchanged`-файлы по фактическим worktree-байтам target. После
staging система SHALL проверять эффективные итоговые `text`/`eol`,
релевантный config, физические байты текстовых путей и отсутствие
unstaged-расхождений всего tracked-дерева без доверия stat-кешу.
`core.autocrlf=true`, эффективный `eol=crlf`, native CRLF на Windows без
явного LF либо иная несовместимость MUST завершаться
`UNSAFE_STOP/LF_WORKTREE_UNSUPPORTED` до любой мутации реального target.

#### Scenario: Атрибуты только в info/attributes
- **WHEN** реальный target задаёт `f.txt eol=crlf` только в `.git/info/attributes`
- **THEN** preflight воспроизводит атрибут и отклоняет target до изменения

#### Scenario: Смена .gitattributes при unchanged-файлах
- **WHEN** снапшот меняет только `.gitattributes` на политику, способную материализовать `unchanged`-файлы с CRLF
- **THEN** постпроверка всего дерева фиксирует расхождение, и успех не объявляется на основании одного `verify_index`

#### Scenario: Несвязанный legacy CRLF в target
- **WHEN** patch меняет LF-путь, а другой неизменяемый target-путь содержит закоммиченный CRLF при стабильной byte-preserving политике
- **THEN** CR проверяется только для канонических postimage patch и несвязанный путь не блокирует `CLEAN_APPLY`

#### Scenario: Binary-атрибут не включён в patch scope
- **WHEN** source классифицирует CRLF blob через явный `-text`, но итоговый target index не содержит этот атрибут
- **THEN** preflight останавливается с `ATTRIBUTE_SCOPE_MISMATCH` и требует включить `.gitattributes` в scope

#### Scenario: Не-EOL отказ worktree
- **WHEN** канонический путь не может быть материализован байт-точно по причине, не связанной с EOL — коллизия регистра на ignorecase-файловой системе, недоступный для записи путь, нормализация имён
- **THEN** отчёт останавливается с `WORKTREE_INCOMPATIBLE`, а не с `LF_WORKTREE_UNSUPPORTED`, и называет фактическую причину

### Requirement: Классификация различает индексный контракт и готовность worktree

`CONVERGED_STAGED` SHALL присваиваться только при одновременно доказанных
байт-точном индексе и отсутствии unstaged-расхождений tracked-дерева.
Успешная cached-проверка при пропущенной или неуспешной worktree-проверке
MUST классифицироваться отдельным статусом с ненулевым кодом выхода и не
объявлять готовность к обычному применению.

#### Scenario: Успешный cached-apply при провале worktree-проверки
- **WHEN** `git apply --cached` создаёт канонический индекс, но проверка реального worktree не выполнена или обнаружила несовместимость
- **THEN** отчёт содержит статус, отличный от полного успеха, и ненулевой код выхода

### Requirement: Whitespace-диагностика неблокирующая, отказ инструментов блокирующий

Найденные whitespace-дефекты SHALL публиковаться в отчёте как диагностика по
фиксированной стандартной политике инструмента и MUST NOT менять outcome.
Ошибка запуска Git или чтения индекса
при выполнении проверки MUST оставаться блокирующей. Сообщения `diff --check`
MUST попадать в отчёт из stdout.

#### Scenario: Канонический файл с конфликтным маркером переносится
- **WHEN** канонический файл содержит `<<<<<<< HEAD` и его SHA-256 совпадает
- **THEN** конвергенция успешна, а маркер перечислен в whitespace-диагностике отчёта

#### Scenario: Git пишет warning вместе с findings
- **WHEN** `git diff --check` возвращает findings в stdout и предупреждение в stderr с обычным кодом findings
- **THEN** findings остаются неблокирующей диагностикой

### Requirement: Полная инвентаризация читает blobs пакетно

Полные проверки index SHALL читать уникальные blobs через один
`git cat-file --batch` на инвентаризацию, а не запускать Git для каждого пути.

#### Scenario: Много путей с общим blob
- **WHEN** index содержит много файлов с одним object id
- **THEN** одна инвентаризация выполняет один batch-вызов и читает blob один раз

### Requirement: Rollback честен и привязан к захваченному commit

Автоматический откат и выдаваемая пользователю команда отката SHALL
использовать commit, захваченный до первой мутации, а не подвижный `HEAD`.
При отказе автоматического отката отчёт MUST содержать
`real_target_modified: true`, признак незавершённого отката и список
затронутых путей.

#### Scenario: Ошибка rollback с честным отчётом
- **WHEN** apply упал после частичной записи, и автоматический откат также завершился ошибкой
- **THEN** отчёт сообщает `real_target_modified: true` и незавершённость отката, не утверждая отсутствие изменений

### Requirement: Транспорт принимает UTF-8 BOM и явно отклоняет UTF-16

Все reader'ы `.sync` SHALL принимать файл с UTF-8 BOM как эквивалентный файлу
без BOM. Байты, указывающие на UTF-16, MUST давать явное сообщение о
необходимости пересохранить файл в UTF-8/ASCII. Формат бандла и смысл
существующего поля `bundle_sha256` MUST NOT изменяться.

#### Scenario: Бандл пересохранён Notepad с BOM
- **WHEN** валидный `.sync` получает префикс UTF-8 BOM
- **THEN** inspect и plan обрабатывают его как исходный бандл

#### Scenario: Бандл перекодирован PowerShell в UTF-16
- **WHEN** `.sync` сохранён в UTF-16LE с BOM
- **THEN** reader останавливается с сообщением, называющим кодировку причиной и требующим UTF-8/ASCII
