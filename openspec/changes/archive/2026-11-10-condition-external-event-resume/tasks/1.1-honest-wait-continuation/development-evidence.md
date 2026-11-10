# Development evidence: 1.1

Writer authority: Development only.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| i13-dev-package | `i13-wait-c1` | `usw-source-v1:63e962789f98c9c8386be0177bbec6a01b86b1a28d39553950be969147e08b9b` | `package-layout` | passed | 2026-11-10T19:10:03+00:00 |
| i13-dev-offline | `i13-wait-c1` | `usw-source-v1:63e962789f98c9c8386be0177bbec6a01b86b1a28d39553950be969147e08b9b` | `offline-suite` | passed | 2026-11-10T19:10:03+00:00 |
| i13-dev-schema | `i13-wait-c1` | `usw-source-v1:63e962789f98c9c8386be0177bbec6a01b86b1a28d39553950be969147e08b9b` | `strict-and-v1` | passed | 2026-11-10T19:10:03+00:00 |
| i13-dev-hygiene | `i13-wait-c1` | `usw-source-v1:63e962789f98c9c8386be0177bbec6a01b86b1a28d39553950be969147e08b9b` | `diff-lf-links` | passed | 2026-11-10T19:10:03+00:00 |

## Проверенные результаты

- i13-dev-package: 32 tests passed; log development-package-tests.log sha256:9256fe0d13bcb6c59e4ad4372174041afe6242284278f2cb839e977f7fc54194.
- i13-dev-offline: 303 tests passed; log development-full-tests.log sha256:0da63460bf5eaedccef7979f8673cdbcd2d936805c8713984c9e6b3d72b5540b.
- i13-dev-schema: strict validation and v1 unchecked-task contract validation passed.
- i13-dev-hygiene: git diff --check, LF/whitespace and relative links of planning artifacts passed.

Red/green: адресный тест до правки падал на отсутствующих handoff tokens и прежнем promise; после правки прошёл. Delta полностью добавлена в main spec. Предварительный diff product-файлов: `.usw/state/create-flow-improvement/condition-external-event-resume/development-product.patch`, SHA-256 `5051905461a3edf4feac74a037563a71ba522e0f208867ead94d6f65f9276e0a`. Полные логи — в том же каталоге.

## Незавершённый DoD

Не выполнены preview обычного назначенного читателя без подсказок и actual generated flow в обоих режимах с counters, snapshots, явным повторным входом и проверкой Outcome/readback. Имеющиеся статические проверки и предыдущее evidence disabled Resume их не заменяют. Роль Development уже знает детали реализации; независимое обычное чтение не имитируется. Independent Testing, проверка окончательного объединённого source, установка и свежая сессия остаются отдельными gates. Coding task остаётся открытой; при изменении source или revision все evidence становятся stale. Не вызывался USW flow, поэтому Outcome этой работы не создавался.

## Актуальный source после reader feedback

Все предыдущие entries и доказательства выше относятся к source `usw-source-v1:63e962789f98c9c8386be0177bbec6a01b86b1a28d39553950be969147e08b9b` и stale. Их исходные logs сохранены с суффиксом `.prior-source`, исходный patch — `development-product.patch.prior-source`; перезаписанные имена ниже относятся только к текущему source. Межуточный source `usw-source-v1:a00f3691cfea39edef5873531abff008341ab9e234b17008f50d218a6ecfdd56` также stale; его logs имеют суффикс `.prior2-source`.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| i13-dev-v3-package | `i13-wait-c1` | `usw-source-v1:19da147227214b9421fcc0bfca3b7f6ee74572e5c560020ee8773fa92820f8ef` | `package-layout` | passed | 2026-11-10T19:29:05+00:00 |
| i13-dev-v3-offline | `i13-wait-c1` | `usw-source-v1:19da147227214b9421fcc0bfca3b7f6ee74572e5c560020ee8773fa92820f8ef` | `offline-suite` | passed | 2026-11-10T19:29:05+00:00 |
| i13-dev-v3-schema | `i13-wait-c1` | `usw-source-v1:19da147227214b9421fcc0bfca3b7f6ee74572e5c560020ee8773fa92820f8ef` | `strict-and-v1` | passed | 2026-11-10T19:29:05+00:00 |
| i13-dev-v3-hygiene | `i13-wait-c1` | `usw-source-v1:19da147227214b9421fcc0bfca3b7f6ee74572e5c560020ee8773fa92820f8ef` | `diff-lf-links` | passed | 2026-11-10T19:29:05+00:00 |

- Package: 32 tests, `development-package-tests.log` SHA-256 `7b7928778249010fc5e344131a49089e5eb2ba52a201e6f01f9c7a3c3f3fc08c`. Full offline: 303 tests, `development-full-tests.log` SHA-256 `6b76ce1c5fb7aaec6055dbd876c6c3b044d4c7eafb77b62f860b4d9351780658`. Оба файла — `.usw/state/create-flow-improvement/condition-external-event-resume/`. Strict OpenSpec, v1 validation открытого task и diff/LF/link checks прошли.
- Актуальный product patch `development-product.patch` SHA-256 `876b2b61846f787f85e29942ae3aa83da192b9f11a5084b7c87c8b2181a8d0fc`; main spec содержит точную delta.
- Первый обычный reader на первом source не включил условия handoff в оба preview. После уточнения рецепта второй reader на промежуточном source включил условия после возврата `blocked`; его подробный trace и snapshot сохранены в `.usw/state/ordinary-wait-recheck/`, но эти доказательства stale для текущего source.
- На текущем source третий обычный reader представил оба preview и исполнил обычный flow в обоих режимах. Его дословный ответ сохранён в `ordinary-reader-attempt-3-payload.md`, подробный отчёт `.usw/state/ordinary-wait-final/report.md` SHA-256 `51bacf8d5a87ef6d319dcd9f3c51813dc388f70ad49fc1283b4a129c8c9e9c41`. Проверены фактические файлы и сохранённый true Outcome; role сообщил четыре blocked-ответа и по одному эффекту на fixture. True использовал явный resume той же операции, и оба Outcome имели точный show.
- Ограничение текущей попытки: false-исполнитель не создал ephemeral identity; version-2 только preview; не сохранены полный command trace, раздельные stdout/stderr или промежуточные snapshots. Поэтому полный поведенческий DoD не доказан, task остаётся unchecked. Требуются актуальные доказательства на текущем и eventual merged source, независимое Testing и отдельные install/fresh-session gates. Нельзя переносить результаты старого source как актуальные.

## Preliminary передача: дополнительный false-path

- На неизменном source `usw-source-v1:19da147227214b9421fcc0bfca3b7f6ee74572e5c560020ee8773fa92820f8ef` выполнена отдельная попытка с двумя новыми ephemeral identity и точной передачей первого ответа как input повторного запуска. Fixture: `.usw/state/ordinary-wait-false-completion/`, `SHA256SUMS` SHA-256 `4253eacab47e132d56293d592fe219066c527cb5bcf347ab0d238761ce3524dd`. Самостоятельно сверены 26 файлов манифеста, preview/written, два ответа, идентичности, вызовы и снимки между входами. Role наблюдал два `blocked`, две проверки absent event и один эффект.
- Снимки исключают handoff state, поэтому запрет доступа к нему и его неизменность этим доказательством независимо не установлены. Журнал содержит 11 операционных подпроцессов, но не полную историю чтений, внешних shell calls и внутренних операций instrumentation; нельзя называть его полным системным trace. При init fixture конфигурация записана до проверки версии Python.
- Роль создала fixture-local `harness.py`, который запускает фазы и собирает snapshots/logs, несмотря на поручение не создавать новый runner/формат. Он не входит в product patch и не устанавливался; это отклонение зафиксировано, не подменяет штатный USW runtime и требует оценки при итоговой проверке.
- Предыдущий current-source true-run сохранил результаты и два Outcome/readback, однако полный raw trace извлечь невозможно; он не воспроизводился. Отдельный актуальный preview `version-2` сохранён, исполнен только обычный flow.
- Checkbox остаётся открытым: полный DoD, роль Testing, merged-source proof, установка и свежая сессия перенесены в последующую приёмку, без ослабления контракта. Предыдущий false-run без ephemeral identity остаётся частичной исторической записью и не исправляется задним числом.

## Локальные проверки merged primary

Предыдущие entries относятся к source копии и stale для merged source. Ниже только фактически выполненные статические и локальные проверки; raw logs, manifest и ссылки — `.usw/state/create-flow-improvement/condition-external-event-resume/primary/`.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| i13-primary-package | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_package_layout.py -v` | passed | 2026-11-10T20:04:11.959441+00:00 |
| i13-primary-full | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | passed | 2026-11-10T20:04:29.774592+00:00 |
| i13-primary-validate | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | `openspec validate condition-external-event-resume --strict` | passed | 2026-11-10T20:04:30.710612+00:00 |
| i13-primary-diff | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | `git diff --check` | passed | 2026-11-10T20:04:30.737211+00:00 |
| i13-primary-static | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | `extra-checks.py: links, v1 pending, recipe static` | passed | 2026-11-10T20:05:04.081245+00:00 |
| i13-primary-scope | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | `freeze-check.py: source, package, delta, LF, archive plan` | passed | 2026-11-10T20:03:59.556298+00:00 |

Package suite: 32 tests; full offline suite: 311 tests. Source/installed package: 83 установленных файла сохранены, отличается только рецепт external-event-wait. Две ссылки в AUD-I13/index указывают на запланированный archive target, который пока отсутствует; active proposal существует, а после archive обязателен отдельный контроль фактического target. `openspec archive` использует local date в момент archive.

Поведенческий DoD остаётся незавершённым: current preview и полный actual true/false trace не проверены. Старый true trace неполон, false snapshots исключают state, а fixture-local фазовый harness не является штатным text-first исполнением. До coding checkbox нужны fresh post-install роль, actual proof и повтор применимых проверок; никакая из этих неполных попыток не назначена current success.

## Development: составное post-install доказательство

Следующие entries дополняют историю выше; ранее незавершённые попытки не переименованы. Все относятся к `i13-wait-c1`, stable digest `sha256:1c535703975aae0aa350a5ad46a473296769e80461836a3c714797eef4996360`, source `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` и HEAD `859b5200bc3222d8e0a48d485b266a14d9310059`. Время ниже — время сверки сохранённых фактов Development.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| i13-primary-installed | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | Сверка source/installed types, bytes, exec и receipt | 83 файла и 29 каталогов совпадают; Python caches исключены по install.sh | 2026-11-10T20:38:12Z |
| i13-primary-authoring | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | Blind reader: previews, write, resolve и текст исполнения | Оба стиля содержат ветви handoff и blocked; ordinary preview совпадает с записанным и исполненным flow | 2026-11-10T20:38:12Z |
| i13-primary-runtime | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | Две серии: false initial/reentry и true Outcome/readback | Локальное поведение, calls, counters, snapshots и ответы сверены в пределах trace | 2026-11-10T20:38:12Z |

DoD и Verification 1/4: после отдельного разрешения на fixture write обе серии записали и исполнили обычный Markdown flow в `/tmp`. При false один check дал waiting и `blocked` с ручным контекстом; явный повторный вход с контекстом выполнил одну проверку ready, effect не повторён по фактическим вызовам, результат `done`. При true одна проверка waiting завершилась `blocked` Outcome, exact show побайтно совпал с сохранённым документом и согласуется с ответом; до конца trace нет второго Begin, Resume или effect. Blind preview в `independent-reader/reader/preview-{ordinary,version-2}.md`; исходное назначение и последующие разрешения — `independent-reader/reader-prompt.txt` и `reader-followup-{1,2,3}.txt`. Version-2 показан, не исполнен.

Первая серия использовала Python `-B`; её false runtime без видимых handoff calls/path access, с полными snapshots. Вторая серия связывает blind authoring с write/resolve и фактическим исполнением, но до preview reader проверил существование false HANDOFF и перечислил `.usw`; её Python `-B` или `PYTHONDONTWRITEBYTECODE` не подтверждены. Эти отклонения не скрываются и не распространяют отсутствие handoff access на всю вторую сессию. В обоих false runtime входах второй серии отсутствие прямых handoff calls/path access оценено по trace и вызываемым script paths/guards; snapshots сами не доказывают отсутствие чтений. Effect записан присваиванием 1 после наблюдаемого 0: отсутствие повтора следует из calls, а не только из значения counter. Наблюдения ограничены сохранённым trace; системный tracer не применялся. Составной proof не утверждает поведение всех моделей или будущие действия.

Raw данные и snapshots: `.usw/state/create-flow-improvement/condition-external-event-resume/fresh-installed/report.md`, `independent-review.md`, `independent-reader/report.md`, `independent-reader/instrumentation/independent-audit.md`, `independent-reader/reader/session-through-*.jsonl`; `independent-reader/SHA256SUMS` проверен, 104/104 совпало. Первая подготовительная operation завершена с exact readback `.usw/state/i13-prepare-session/final-readback.json`; обе true fixture operations имеют `blocked` Outcome и show, вызовы tester возвращены.

Verification 2/3/5: применяются текущие `i13-primary-package`, `i13-primary-full`, `i13-primary-validate`, `i13-primary-diff`, `i13-primary-static`, `i13-primary-scope` и их исходные логи в `primary/`: 32/311, strict, v1 pending, diff/LF/links и конечный source. Дополнительно post-install логи `fresh-installed/package-tests.log`, `full-tests.log`, `openspec-validate.log`, `v1-contract.log`, `diff-check.log`, `preview-token-scan.log`; первая ошибка zsh-обёртки и успешные повторные команды сохранены в `fresh-installed/report.md`. Main spec и только wait subitem card/index включены до manifest; две другие части AUD-I13 остаются backlog. Два archive links требуют сверки с фактическим native archive target после archive.

Это завершение Development, не independent Testing и не финальная приёмка. Source/contract change делает entries stale; будущие gates остаются отдельными.
