## 1. Enriched operation creation

- [x] 1.1 Add focused failing tests proving Begin writes bounded Summary, equal Started/Updated, Git base revision, expected writes and empty observed changes; verify the focused test fails for the missing fields.
- [x] 1.2 Implement the enriched parser/renderer and Begin API/CLI until the focused creation tests pass without changing router identity or paths.

## 2. Outcome and compatibility

- [x] 2.1 Add focused failing tests for preserving immutable recovery context, recording Outcome changes, read-only old-document support, old-document enrichment and downgrade rejection; verify the failures are caused by missing behavior.
- [x] 2.2 Implement Outcome enrichment, dual-shape validation, immutable Save checks and enriched discovery until the focused compatibility tests pass.

## 3. Contracts and verification

- [x] 3.1 Update `usw-manage-handoff` and `usw-run-flow` instructions to require factual summary/write/change hints while retaining the no-attribution and no-audit-log boundaries.
- [x] 3.2 Run the handoff unit suite, end-to-end suite, package tests and OpenSpec validation; resolve only regressions caused by this change.
