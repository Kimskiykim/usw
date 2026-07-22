# Development evidence

Writer authority: Development only.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| dev-targeted | `cr-001` | `usw-source-v1:fb982e192c3b67bf24ad3f61a46958df71379cb6440d13b653d03ea6bc91f17a` | `python3 -m unittest tests.test_package_layout tests.test_flow_scenarios tests.test_flow_orchestrator -v` | passed | 2026-07-22T03:41:14+03:00 |
| dev-full | `cr-001` | `usw-source-v1:fb982e192c3b67bf24ad3f61a46958df71379cb6440d13b653d03ea6bc91f17a` | `python3 -m unittest discover -s tests -v` | passed | 2026-07-22T03:41:14+03:00 |
| dev-openspec | `cr-001` | `usw-source-v1:fb982e192c3b67bf24ad3f61a46958df71379cb6440d13b653d03ea6bc91f17a` | `openspec validate add-markdown-flow-composition --type change --strict` | passed | 2026-07-22T03:41:14+03:00 |
