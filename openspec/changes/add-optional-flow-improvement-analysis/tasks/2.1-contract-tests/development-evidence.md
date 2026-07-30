# Development evidence

Writer authority: Development only.

| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |
|---|---|---|---|---|---|
| dev-targeted | `cr-001` | `usw-source-v1:f39d2e4e16948c71d5215ebceae0c812448c4c6c9369801626d70a9a8b954693` | `python3 -m unittest tests.test_package_layout -v` | passed | 2026-07-29T17:27:25+03:00 |
| dev-full | `cr-001` | `usw-source-v1:f39d2e4e16948c71d5215ebceae0c812448c4c6c9369801626d70a9a8b954693` | `python3 -m unittest discover -s tests -v` | passed | 2026-07-29T17:27:25+03:00 |
| dev-openspec | `cr-001` | `usw-source-v1:f39d2e4e16948c71d5215ebceae0c812448c4c6c9369801626d70a9a8b954693` | `openspec validate add-optional-flow-improvement-analysis --strict` | passed | 2026-07-29T17:27:25+03:00 |
| dev-description-full | `cr-001` | `usw-source-v1:b48ccd5ab5fab5ac5cb9c3ea7b5b9e1da07911944f383f664ed75d690edf9231` | `python3 -m unittest discover -s tests -v` | passed | 2026-07-29T17:34:26+03:00 |
| dev-russian-description-full | `cr-001` | `usw-source-v1:d3c54bb69a2ef3e05f9b6b71a4244cbfdc037b4c93949fe2cf5ffd8fb8a94a18` | `python3 -m unittest discover -s tests -q` | passed | 2026-07-29T17:37:27+03:00 |
