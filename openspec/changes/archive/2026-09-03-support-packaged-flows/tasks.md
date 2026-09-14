## 1. Resolver data contract

- [x] 1.1 Add failing unit tests proving a packaged `name/FLOW.md` resolves with exact bytes, entrypoint path, exact absolute package `flow_directory`, and unchanged origin-bound identity; verify only the targeted tests fail for missing package support.
- [x] 1.2 Extend `MarkdownFlow`, root preparation, nested preparation, `resolve`, and `inspect` CLI JSON with `flow_directory`; verify the new package test and existing flat-flow identity tests pass.
- [x] 1.3 Add failing tests for flat/package ambiguity, local-first lookup across layouts, missing-local fallback, and package-directory or `FLOW.md` symlinks; verify failures identify the absent safety behavior.
- [x] 1.4 Implement descriptor-relative selection of one flat or packaged entrypoint per origin and the stable `ambiguous_flow_layout` error; verify all resolver safety tests pass on native and Windows-fallback paths.

## 2. Package resource boundary

- [x] 2.1 Add failing tests for a packaged Markdown resource, a path supplied only by user input, absolute paths, `..` escape, symlink components, missing targets, unexpected filesystem types, and the existing flat-flow workspace-relative reference in `usw/flows/chat-review.md`.
- [x] 2.2 Add the minimum executor-facing resource boundary needed by `usw-run-flow`; derive its base only from the resolved invocation, reject unsafe discovered paths at use, and avoid automatic package scanning or new authority; verify the resource and compatibility tests pass.
- [x] 2.3 Update root and nested execution instructions to pass exact `flow_directory`, distinguish packaged-Markdown dependencies from user input, preserve flat-flow path semantics, and retain normal tool and permission checks; verify atomic skill-contract tests cover these instructions.

## 3. Authoring and discovery

- [x] 3.1 Add prompt text-contract assertions that `usw-create-flow` instructs the model to use `<name>/FLOW.md`, preserve existing layouts/resources, and stop on dual, late-created, symlink, or non-regular entrypoints; do not claim deterministic model-behavior coverage.
- [x] 3.2 Update `usw-create-flow` and guided revision instructions for safe package creation and in-place layout preservation; verify the authoring prompt contract passes.
- [x] 3.3 Add prompt text-contract assertions that `usw-find-flow` instructs the model to catalog only direct flat entries and packages, ignore nested resource Markdown, return exact paths, and surface resolver-owned `ambiguous_flow_layout` evidence.
- [x] 3.4 Update finder instructions to enumerate bounded package candidates and load them through the shared resolver; verify the discovery prompt contract passes without claiming a model eval.

## 4. Assessment and documentation

- [x] 4.1 Add CLI tests that inspection returns exact absolute `flow_directory` without reopening files, plus prompt text-contract assertions that assessment treats named package resources as unverified; do not claim deterministic assessor-model behavior.
- [x] 4.2 Update assessor instructions, README examples, and normative descriptions to document package layout, compatibility, ambiguity, resource paths, and non-goals; verify documentation assertions and package-layout tests pass.

## 5. Acceptance

- [x] 5.1 Run focused resolver, resource, authoring, finder, assessment, and package-layout tests; record each command and its zero-failure result.
- [x] 5.2 Run the complete repository test suite and `openspec validate support-packaged-flows --strict`; fix only regressions attributable to this change and record the final results.

## 6. Review fixes

- [x] 6.1 Add a failing post-resolution ancestor-symlink swap test, anchor resource traversal at the resolved project root, and verify the escape is rejected.
- [x] 6.2 Add a failing skill-facing resource CLI test, bind it to the original flow identity and entrypoint path, update runner instructions, and verify forged or stale context is rejected.
- [x] 6.3 Add a failing authoring contract test for explicit `--shared`, document it as mutually exclusive with local selectors, and verify package-layout contracts pass.
- [x] 6.4 Re-run the complete test suite, strict OpenSpec validation, task status, and diff checks after review fixes.

## 7. Subagent review fixes

- [x] 7.1 Add failing resolver tests for non-blocking final-file opens and fail-closed Windows pathname fallback; implement the minimum safe behavior and verify focused resolver tests.
- [x] 7.2 Add failing resource CLI tests for mandatory exact origin, conflicting origin selectors, and a resource absent from immutable Markdown; enforce those boundaries and verify focused resource tests.
- [x] 7.3 Add failing skill-contract tests for selector-free shared authoring, resolver-owned ambiguity evidence, and packaged-only assessment resources; reconcile the three instruction contracts and verify package-layout tests.
- [x] 7.4 Record focused and complete acceptance commands with their observed results, then run the complete test suite, strict OpenSpec validation, task status, and diff checks.

## Acceptance evidence

Prompt substring checks below verify instruction text only. They are not a
deterministic create/find/assess model-behavior evaluation; runtime guarantees
are covered by resolver and CLI tests.

- `python3 -m unittest tests.test_flow_orchestrator tests.test_package_layout tests.test_atomic_skill_contracts` — 70 tests, OK.
- `python3 -m unittest discover -s tests` — 175 tests, OK.
- `openspec validate support-packaged-flows --strict` — change is valid.
- `openspec status --change support-packaged-flows --json` — planning artifacts complete.
- `git diff --check` — exit 0, no whitespace errors.

## 8. LLM-critic review fixes

- [x] 8.1 Add failing Windows-fallback tests proving legacy flat resolve remains compatible while packaged and resource operations fail closed; restore only the legacy flat path.
- [x] 8.2 Add failing resource-declaration tests for ordinary Markdown punctuation, replace the punctuation allowlist with a general path boundary, and verify focused resource tests.
- [x] 8.3 Add failing tests that resource bytes are read from the held descriptor and survive a post-read pathname swap; return immutable resource bytes and identity from the CLI without reopening the path.
- [x] 8.4 Rename prompt substring tests and acceptance wording to text-contract assertions, document the lack of deterministic model-behavior evaluation, then rerun focused tests, the complete suite, strict validation, task status, and diff checks.
