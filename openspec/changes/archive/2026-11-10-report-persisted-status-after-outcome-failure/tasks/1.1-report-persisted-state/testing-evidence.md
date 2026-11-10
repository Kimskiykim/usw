# Testing evidence: 1.1

Writer authority: Testing only.

| Evidence ID | Contract revision | Source identity | Check | Result | Finding | Timestamp |
|---|---|---|---|---|---|---|
| f05-c2-final-test-before | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | before-document: exact Show, ответ, snapshots, calls | passed | none | 2026-11-10T16:45:54.578541+00:00 |
| f05-c2-final-test-after | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | after-document: exact Show, ответ, snapshots, calls | passed | none | 2026-11-10T16:45:54.602523+00:00 |
| f05-c2-final-test-unreadable | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | unreadable-state: exact Show, ответ, snapshots, calls | passed | none | 2026-11-10T16:45:54.625868+00:00 |
| f05-c2-final-test-guards | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | 6 адресных unittest и чтение installed guard instructions | passed | none | 2026-11-10T16:45:25.840754+00:00 |
| f05-c2-final-test-source | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | canonical manifest и 83 source/installed/record файла | passed | none | 2026-11-10T16:44:39.133309+00:00 |

## Raw evidence

- `.usw/state/autonomous-improvement/2026-11-10/f05-c2-final-testing/`: source-manifest.bin, package-comparison.json, guard-checks.json и scenario-comparison.json; в каталогах каждого случая — ответы до сверки, calls, snapshots и raw-manifest.
- Во всех случаях один setup Outcome, один exact Show, counter=1, сосед и candidates неизменны. При ошибке чтения текущий status и сохранность в ответе не утверждены; offline snapshot сверялся после ответа.
- Проверен возврат после подготовленного Outcome, а не полный flow от Begin. Manual и child authority проверены по тексту; тесты parent/disabled исполняют backend. Универсального доказательства поведения моделей нет.
- Прежняя консультация unknown-phase на `9f1707` — историческое наблюдение о том же installed package, не новый backend test текущего source.
