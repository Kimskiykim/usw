## 1. Nested graph preflight

- [ ] 1.1 Add a safe strict-flow loader that validates the selected root, every path component, safe names, regular files, and fixed origin without fallback
- [ ] 1.2 Add an iterative nested graph model and preflight every direct, transitive, and parallel `CALL FLOW` target before executor invocation
- [ ] 1.3 Detect direct and indirect ancestor cycles while permitting non-recursive DAG reuse, with tests for paths and reported errors
- [ ] 1.4 Resolve descendant executors and aggregate declared writes so unavailable capabilities and authority mismatches fail before mutation

## 2. Production nested-flow execution

- [ ] 2.1 Register the built-in flow adapter only for `--experimental-structured` runs and preserve injected typed executors for other call kinds
- [ ] 2.2 Pass task, scope, action input, prior completed results, source context, and explicit permissions into sequential children
- [ ] 2.3 Drive a sequential child to a terminal outcome and propagate normalized status, detail, actual writes, references, and parent cursor behavior
- [ ] 2.4 Execute nested-flow branches through the existing `PARALLEL` boundary and aggregate branch results in document order

## 3. Durable nested state

- [x] 3.0 Store new checkpoints under origin/name/run UUID paths, support exact run resume, and retain read-only legacy `.usw/FLOW.json` loading
- [ ] 3.1 Add strict schema version 4 models and atomic serialization for root, nested, and ordered parallel execution nodes while retaining schema 1–3 readers
- [ ] 3.2 Persist ready and `in_progress` boundaries before invocation and completed outcomes after invocation through a single checkpoint coordinator
- [ ] 3.3 Resume the deepest unfinished sequential child first and reject stale flow or source identities across the complete saved ancestry
- [ ] 3.4 Preserve completed parallel branches and require explicit recovery for any branch left `in_progress` without a result

## 4. Operation and permission boundaries

- [ ] 4.1 Keep nested execution under one root HANDOFF Begin/Outcome and report active ancestry without creating child operations
- [ ] 4.2 Verify child scripts, writes, Git operations, delivery, deployment, and release retain their existing explicit permission boundaries
- [ ] 4.3 Verify nested checkpoints remain developer-local, atomic, mode `0600`, and do not duplicate flow contents or task data per frame

## 5. Compatibility and documentation

- [ ] 5.1 Add regression tests proving plain Markdown and non-nested v1/v2 flows keep existing lookup, cursor, outcome, and checkpoint behavior
- [ ] 5.2 Update `usw-run-flow` instructions and the version-2 reference with production nested lookup, preflight, lifecycle, resume, and failure semantics
- [ ] 5.3 Add an end-to-end structured parent/child fixture covering local and shared origins, multi-level completion, stop propagation, and resume

## 6. Verification

- [ ] 6.1 Run targeted flow-orchestrator and package-layout tests and resolve all regressions
- [ ] 6.2 Run `python3 -m unittest discover -s tests -v`
- [ ] 6.3 Run strict OpenSpec validation for `implement-nested-flow-runtime` and review the final diff for unrelated changes
