# Development evidence

Writer authority: Development only.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| dev-concise-targeted | `cr-002` | `usw-source-v1:fb982e192c3b67bf24ad3f61a46958df71379cb6440d13b653d03ea6bc91f17a` | `python3 -m unittest tests.test_package_layout -v` | passed | 2026-07-22T03:41:14+03:00 |
| dev-concise-full | `cr-002` | `usw-source-v1:fb982e192c3b67bf24ad3f61a46958df71379cb6440d13b653d03ea6bc91f17a` | `python3 -m unittest discover -s tests -v` | passed | 2026-07-22T03:41:14+03:00 |
| dev-concise-openspec | `cr-002` | `usw-source-v1:fb982e192c3b67bf24ad3f61a46958df71379cb6440d13b653d03ea6bc91f17a` | `openspec validate add-markdown-flow-composition --type change --strict` | passed | 2026-07-22T03:41:14+03:00 |
| dev-mvp-targeted | `cr-002` | `usw-source-v1:a8f57e82367218382f421f36170868dec2eb9462b9c4aace29803e8a7899e288` | `python3 -m unittest tests.test_package_layout -v` | passed | 2026-07-22T03:29:04+03:00 |
| dev-mvp-full | `cr-002` | `usw-source-v1:a8f57e82367218382f421f36170868dec2eb9462b9c4aace29803e8a7899e288` | `python3 -m unittest discover -s tests -v` | passed | 2026-07-22T03:29:04+03:00 |
| dev-mvp-openspec | `cr-002` | `usw-source-v1:a8f57e82367218382f421f36170868dec2eb9462b9c4aace29803e8a7899e288` | `openspec validate add-markdown-flow-composition --type change --strict` | passed | 2026-07-22T03:29:04+03:00 |
| dev-targeted | `cr-001` | `usw-source-v1:fb5625aa4a283dacceb888b575eb77c5a338113c62d4dc2d8ce080fc41e640d1` | `python3 -m unittest tests.test_package_layout -v` | passed | 2026-07-22T02:28:57+03:00 |
| dev-full | `cr-001` | `usw-source-v1:fb5625aa4a283dacceb888b575eb77c5a338113c62d4dc2d8ce080fc41e640d1` | `python3 -m unittest discover -s tests -v` | passed | 2026-07-22T02:28:57+03:00 |
| dev-openspec | `cr-001` | `usw-source-v1:fb5625aa4a283dacceb888b575eb77c5a338113c62d4dc2d8ce080fc41e640d1` | `openspec validate add-markdown-flow-composition --type change --strict` | passed | 2026-07-22T02:28:57+03:00 |
| dev-targeted-2 | `cr-002` | `usw-source-v1:e725ad0db4f0626d8f528345501119d13a76f701db9bd0c080d58b5dba1bdc66` | `python3 -m unittest tests.test_package_layout -v` | passed | 2026-07-22T02:42:45+03:00 |
| dev-full-2 | `cr-002` | `usw-source-v1:e725ad0db4f0626d8f528345501119d13a76f701db9bd0c080d58b5dba1bdc66` | `python3 -m unittest discover -s tests -v` | passed | 2026-07-22T02:42:45+03:00 |
| dev-openspec-2 | `cr-002` | `usw-source-v1:e725ad0db4f0626d8f528345501119d13a76f701db9bd0c080d58b5dba1bdc66` | `openspec validate add-markdown-flow-composition --type change --strict` | passed | 2026-07-22T02:42:45+03:00 |
| dev-targeted-3 | `cr-002` | `usw-source-v1:7094195c1e1b2341ffd8def57f3362b769cbc09e16e87a30d5df00bfaad3ce1e` | `python3 -m unittest tests.test_package_layout -v` | passed | 2026-07-22T03:14:17+03:00 |
| dev-full-3 | `cr-002` | `usw-source-v1:7094195c1e1b2341ffd8def57f3362b769cbc09e16e87a30d5df00bfaad3ce1e` | `python3 -m unittest discover -s tests -v` | passed | 2026-07-22T03:14:17+03:00 |
| dev-openspec-3 | `cr-002` | `usw-source-v1:7094195c1e1b2341ffd8def57f3362b769cbc09e16e87a30d5df00bfaad3ce1e` | `openspec validate add-markdown-flow-composition --type change --strict` | passed | 2026-07-22T03:14:17+03:00 |
