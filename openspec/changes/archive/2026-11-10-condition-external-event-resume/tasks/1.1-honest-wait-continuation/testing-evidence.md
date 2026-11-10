# Testing evidence: 1.1

Writer authority: Testing only.

| Evidence ID | Contract revision | Source identity | Check | Result | Finding | Timestamp |
|---|---|---|---|---|---|---|
| i13-testing-identity | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | 546-файловый canonical manifest, stable contract и 26 raw identities Development receipt | passed | none | 2026-11-10T20:42:09+00:00 |
| i13-testing-authoring | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | Blind ordinary/version-2 previews, installed bytes и совпадение ordinary preview/write/resolve/FLOW | passed | none | 2026-11-10T20:42:09+00:00 |
| i13-testing-runtime | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | Составной false/true trace, counters, snapshots, ответы и exact Outcome/readback | passed | none | 2026-11-10T20:42:09+00:00 |
| i13-testing-checks | `i13-wait-c1` | `usw-source-v1:71ff2aebd08270a47b73a422d382ffeef5173787400c3e21a988b1d8bb2f3275` | Сверка current Development logs 32/311, strict OpenSpec, diff/LF/links, recipe/spec/card scope | passed | none | 2026-11-10T20:42:09+00:00 |

Сверка существующих данных без повторного исполнения runtime и suites: `.usw/state/create-flow-improvement/condition-external-event-resume/primary/commands.json`, `fresh-installed/report.md`, `fresh-installed/independent-review.md`, `fresh-installed/independent-reader/report.md`, `fresh-installed/independent-reader/instrumentation/independent-audit.md` и их raw logs/snapshots/SHA256SUMS. Текущий manifest и stable digest пересчитаны независимо; ordinary preview совпадает с write/resolve и снимками, true show — с документом операции.

Ограничения: при авторинге второй серии проверено существование false HANDOFF; для неё `-B` не подтверждён. Первая серия даёт отдельный false runtime с `-B`; во второй факт отсутствия повтора эффекта следует из calls, а не из присваивания counter. Snapshots не доказывают отсутствие чтений; вывод о runtime ограничен trace и проверенными script paths/guards. True Resume не проверялся. Два archive links требуют проверки фактического target после archive; два других подпункта AUD-I13 остаются backlog.

Два предыдущих rejected transition основаны на ненормативном архивном parser и не устанавливают дефект DoD. Текущий переход принят по `openspec/specs/execution-artifacts/spec.md`; составной proof не означает безупречность каждого сеанса и не является final critic/Delivery.
