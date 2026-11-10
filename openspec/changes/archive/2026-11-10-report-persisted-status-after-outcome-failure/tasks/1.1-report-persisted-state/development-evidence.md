# Development evidence: 1.1

Writer authority: Development only.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| f05-c2-repair1-handoff | `f05-c2` | `usw-source-v1:9f1707d8e293f061bc9a15cda2b45bde43a53d0d1afcc3af60fe3a656d791cc7` | `python3 -m unittest discover -s tests -p test_handoff_state.py -v` | passed | 2026-11-10T16:20:12.190567+00:00 |
| f05-c2-repair1-atomic | `f05-c2` | `usw-source-v1:9f1707d8e293f061bc9a15cda2b45bde43a53d0d1afcc3af60fe3a656d791cc7` | `python3 -m unittest discover -s tests -p test_atomic_skill_contracts.py -v` | passed | 2026-11-10T16:20:12.243914+00:00 |
| f05-c2-repair1-harness | `f05-c2` | `usw-source-v1:9f1707d8e293f061bc9a15cda2b45bde43a53d0d1afcc3af60fe3a656d791cc7` | `python3 -m unittest discover -s tests -p test_eval_harness.py -v` | passed | 2026-11-10T16:20:13.047330+00:00 |
| f05-c2-repair1-package | `f05-c2` | `usw-source-v1:9f1707d8e293f061bc9a15cda2b45bde43a53d0d1afcc3af60fe3a656d791cc7` | `python3 -m unittest discover -s tests -p test_install.py -v` | passed | 2026-11-10T16:20:28.031271+00:00 |
| f05-c2-repair1-full | `f05-c2` | `usw-source-v1:9f1707d8e293f061bc9a15cda2b45bde43a53d0d1afcc3af60fe3a656d791cc7` | `python3 -m unittest discover -s tests -v` | passed | 2026-11-10T16:20:46.117635+00:00 |
| f05-c2-repair1-controls | `f05-c2` | `usw-source-v1:9f1707d8e293f061bc9a15cda2b45bde43a53d0d1afcc3af60fe3a656d791cc7` | `python3 .usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/controls.py` | passed | 2026-11-10T16:20:46.515247+00:00 |
| f05-c2-repair1-list | `f05-c2` | `usw-source-v1:9f1707d8e293f061bc9a15cda2b45bde43a53d0d1afcc3af60fe3a656d791cc7` | `python3 evals/run_evals.py --list` | passed | 2026-11-10T16:20:46.543976+00:00 |
| f05-c2-repair1-validate | `f05-c2` | `usw-source-v1:9f1707d8e293f061bc9a15cda2b45bde43a53d0d1afcc3af60fe3a656d791cc7` | `openspec validate report-persisted-status-after-outcome-failure --strict` | passed | 2026-11-10T16:20:47.480638+00:00 |
| f05-c2-repair1-diff | `f05-c2` | `usw-source-v1:9f1707d8e293f061bc9a15cda2b45bde43a53d0d1afcc3af60fe3a656d791cc7` | `git diff --check` | passed | 2026-11-10T16:20:47.508787+00:00 |

| f05-c2-final-handoff | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | unittest test_handoff_state.py (58) | passed | 2026-11-10T16:39:20.095045+00:00 |
| f05-c2-final-atomic | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | unittest test_atomic_skill_contracts.py (13) | passed | 2026-11-10T16:39:20.145007+00:00 |
| f05-c2-final-harness | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | unittest test_eval_harness.py (59) | passed | 2026-11-10T16:39:20.908506+00:00 |
| f05-c2-final-package | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | unittest test_install.py (11) | passed | 2026-11-10T16:39:36.265890+00:00 |
| f05-c2-final-full | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | unittest discover tests (302) | passed | 2026-11-10T16:39:52.589344+00:00 |
| f05-c2-final-controls | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | 3 deterministic fault controls | passed | 2026-11-10T16:39:52.962906+00:00 |
| f05-c2-final-list | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | evals/run_evals.py --list | passed | 2026-11-10T16:39:52.990503+00:00 |
| f05-c2-final-search | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | rg old Outcome/in_progress claim | passed | 2026-11-10T16:39:52.998985+00:00 |
| f05-c2-final-validate | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | openspec validate change --strict | passed | 2026-11-10T16:39:54.181630+00:00 |
| f05-c2-final-diff | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | git diff --check | passed | 2026-11-10T16:39:54.206431+00:00 |
| f05-c2-final-contract | `f05-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | anchored contract and 7 planning hashes | passed | 2026-11-10T16:40:11.836462+00:00 |

## Raw evidence

- Финальные команды, время, raw logs и manifest: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-final-source/`. Случаи с реальным исполнением роли на конечном source и Testing выполняются отдельно.

- Canonical manifest: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/source-manifest.json`; binary SHA-256 `9f1707d8e293f061bc9a15cda2b45bde43a53d0d1afcc3af60fe3a656d791cc7`; legacy `usw/refinements` включён.
- Команды, время начала/окончания, exit и журналы: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/commands.json`.
- handoff: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/handoff.log` SHA-256 `8daa6a23d71a2fc7a0c8833e5b61deac9b0e62204237d20d88001902e8af10bb`.
- atomic: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/atomic.log` SHA-256 `c94fa0d9fc7e4e0a5505bb34a0c409daaa14d86f17b542ac7cd5e0b718100789`.
- harness: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/harness.log` SHA-256 `1bf97602110a3b253df241e1be288b315fb52fe23399f5ed1d7b24b6adc97013`.
- package: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/package.log` SHA-256 `a76827ca967fa537d159ca149453b766ca530727905560dc7dfd9c30ee03ea82`.
- full: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/full.log` SHA-256 `eb37901ec829392d3e6ede51520b87cf6d76242916542fd14728f275b6409e64`.
- controls: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/controls.log` SHA-256 `33f9f1f8d3de23977f41de5b4cf3bf0fa8b5fa016348ceb59f067e511ddcf5a1`.
- list: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/list.log` SHA-256 `fac0bde61bf2660cc514ed93c0e04748618ddfca2a602119e04ff7c9155efc26`.
- validate: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/validate.log` SHA-256 `f893db905a03f651a17f6841e79d06b327e89b890c818243a78a1c8c7428bf8d`.
- diff: `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/diff.log` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Три контроля: снимки до Outcome, до/после Show, вызовы и точный readback в `.usw/state/autonomous-improvement/2026-11-10/f05-c2-repair1/controls`; это не независимая ролевая проверка.
- Предыдущий Development payload для `f4e73a...` сохранён как история; fresh installed Testing и приёмка ещё не выполнены.
