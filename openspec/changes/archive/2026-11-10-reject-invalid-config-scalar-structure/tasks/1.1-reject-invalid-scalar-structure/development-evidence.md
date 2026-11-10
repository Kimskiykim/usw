# Development evidence: 1.1

Writer authority: Development only. Source предварительный; card/index и независимые gates остаются.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| t01-c2-red | `t01-c2` | `usw-source-v1:908b2a81bc2a05a9413396a2319639fe3af91542a6d4939c7b211634b54e0a90` | scalar nesting regression on original parser | expected failure: 2 assertions | 2026-11-10T17:46:47.413950+00:00 |
| t01-c2-red-provenance | `t01-c2` | `usw-source-v1:4d7fe462e2bd13be9909c4643be8f309e8670cce91b889a9a457dfa738831627` | red tree, реконструкция по baseline и test patch | реконструкция; исторически не измерен | 2026-11-10T18:00:05.379470+00:00 |
| t01-c2-pre-test_init_usw.py | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | python3 -B -m unittest discover -s tests -p test_init_usw.py -v | passed | 2026-11-10T17:48:55.615385+00:00 |
| t01-c2-pre-test_flow_orchestrator.py | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | python3 -B -m unittest discover -s tests -p test_flow_orchestrator.py -v | passed | 2026-11-10T17:48:56.520574+00:00 |
| t01-c2-pre-test_handoff_state.py | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | python3 -B -m unittest discover -s tests -p test_handoff_state.py -v | passed | 2026-11-10T17:48:57.477520+00:00 |
| t01-c2-pre-test_package_layout.py | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | python3 -B -m unittest discover -s tests -p test_package_layout.py -v | passed | 2026-11-10T17:48:57.525431+00:00 |
| t01-c2-pre-test_atomic_skill_contracts.py | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | python3 -B -m unittest discover -s tests -p test_atomic_skill_contracts.py -v | passed | 2026-11-10T17:48:57.570680+00:00 |
| t01-c2-pre-full | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | python3 -B -m unittest discover -s tests -v | passed | 2026-11-10T17:49:16.412473+00:00 |
| t01-c2-pre-validate | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | openspec validate reject-invalid-config-scalar-structure --strict | passed | 2026-11-10T17:49:18.004425+00:00 |
| t01-c2-pre-diff | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | git diff --check | passed | 2026-11-10T17:49:18.036734+00:00 |
| t01-c2-pre-actual | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | N1–N4/P1–P4 trees, real callers and supplied-root resolve | passed | 2026-11-10T17:50:07.275325+00:00 |
| t01-c2-pre-scope | `t01-c2` | `usw-source-v1:60fe7a0105a186bf084ab3343f0692abe0028a2c15ac12434c0c5c0d20daa62f` | manifest, LF, 6 planning hashes, installed 83, scope | passed | 2026-11-10T17:50:59.112334+00:00 |

Raw команды, stdout/stderr, снимки полных деревьев и manifest: `.usw/state/autonomous-improvement/2026-11-10/t01-preliminary/`. Handoff сообщает `handoff_io_error` с `invalid_config` в detail; shared authoring — `invalid_config`. Run resolve проверен только с переданным root.

Уточнение `t01-c2-red`: `908b2a…` в исходной строке — только reference baseline, не full red-source. Исходный parser SHA-256 `c3eec8e186894079c6be5f0985b5cb800ad0c1581d9464e88485dff2170cd17c`; red log и exit сохранены. Full red-source выше реконструирован по trace при условии отсутствия иных включённых изменений; исторического измерения нет. Proof: `.usw/state/autonomous-improvement/2026-11-10/t01-preliminary/red-provenance/`.

## Current Development: конечная редакция

Повторы после включённых card/index edits; предыдущие entries сохранены как история и stale для этого source. Raw: `.usw/state/autonomous-improvement/2026-11-10/t01-finalization/` (`commands.json`, logs, `actual-proof/`, `supplementary.json`, `scope.json`, manifest). Исходный red и его реконструированная identity остаются историческими; повтор red не выполнялся.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| t01-final-test_init_usw.py | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | -m unittest discover -s tests -p test_init_usw.py -v | pass; 30 tests | 2026-11-10T18:29:10.320469+00:00 |
| t01-final-test_flow_orchestrator.py | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | -m unittest discover -s tests -p test_flow_orchestrator.py -v | pass; 57 tests | 2026-11-10T18:29:11.263410+00:00 |
| t01-final-test_handoff_state.py | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | -m unittest discover -s tests -p test_handoff_state.py -v | pass; 58 tests | 2026-11-10T18:29:12.223815+00:00 |
| t01-final-test_package_layout.py | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | -m unittest discover -s tests -p test_package_layout.py -v | pass; 31 tests | 2026-11-10T18:29:12.260318+00:00 |
| t01-final-test_atomic_skill_contracts.py | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | -m unittest discover -s tests -p test_atomic_skill_contracts.py -v | pass; 13 tests | 2026-11-10T18:29:12.304388+00:00 |
| t01-final-full | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | -m unittest discover -s tests -v | pass; 306 tests | 2026-11-10T18:29:30.527273+00:00 |
| t01-final-validate | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | reject-invalid-config-scalar-structure --strict | pass | 2026-11-10T18:29:31.327272+00:00 |
| t01-final-diff | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | --check | pass | 2026-11-10T18:29:31.354697+00:00 |
| t01-final-actual | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | actual-proof.py: N1–N4/P1–P4, callers, supplied-root resolve | pass; 14 negative trees, 4 positive controls | 2026-11-10T18:29:10.594332+00:00 |
| t01-final-supplement | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | supplementary.json: templates, router, v1/checkbox, delta and index | pass | 2026-11-10T18:30:14.940340+00:00 |
| t01-final-scope | `t01-c2` | `usw-source-v1:30e75f7232f1bf0018002d74b60591be5e4e1f7e86040feb7d243e09cdcc9050` | verify-scope.py: canonical manifest, LF, planning, package, volume | pass; 83 files | 2026-11-10T18:30:22.034474+00:00 |

## Current Development: исправленная конечная редакция

После корректировки карточки freeze `30e75f…` и все его evidence стали stale; результаты сохранены как история. Raw текущих проверок: `.usw/state/autonomous-improvement/2026-11-10/t01-finalization-correction/`. Red исторический; его реконструированная identity не измерялась.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| t01-correction-test_init_usw.py | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | -m unittest discover -s tests -p test_init_usw.py -v | pass; 30 tests | 2026-11-10T18:32:33.718786+00:00 |
| t01-correction-test_flow_orchestrator.py | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | -m unittest discover -s tests -p test_flow_orchestrator.py -v | pass; 57 tests | 2026-11-10T18:32:34.668284+00:00 |
| t01-correction-test_handoff_state.py | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | -m unittest discover -s tests -p test_handoff_state.py -v | pass; 58 tests | 2026-11-10T18:32:35.641924+00:00 |
| t01-correction-test_package_layout.py | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | -m unittest discover -s tests -p test_package_layout.py -v | pass; 31 tests | 2026-11-10T18:32:35.678731+00:00 |
| t01-correction-test_atomic_skill_contracts.py | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | -m unittest discover -s tests -p test_atomic_skill_contracts.py -v | pass; 13 tests | 2026-11-10T18:32:35.722925+00:00 |
| t01-correction-full | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | -m unittest discover -s tests -v | pass; 306 tests | 2026-11-10T18:32:52.938958+00:00 |
| t01-correction-validate | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | reject-invalid-config-scalar-structure --strict | pass | 2026-11-10T18:32:54.076873+00:00 |
| t01-correction-diff | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | --check | pass | 2026-11-10T18:32:54.101170+00:00 |
| t01-correction-actual | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | actual-proof.py: N1–N4/P1–P4, callers, supplied-root resolve | pass; 14 negative trees, 4 positive controls | 2026-11-10T18:32:33.997138+00:00 |
| t01-correction-supplement | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | supplementary.py: templates, router, v1/checkbox, delta, index, card | pass | 2026-11-10T18:33:18.479707+00:00 |
| t01-correction-scope | `t01-c2` | `usw-source-v1:02154a32adb1b3775c4f49611d7b0a5f4c104ad22df5da652013d347ba2b5850` | verify-scope.py: canonical manifest, LF, planning, package, volume | pass; 83 files | 2026-11-10T18:33:28.008075+00:00 |
