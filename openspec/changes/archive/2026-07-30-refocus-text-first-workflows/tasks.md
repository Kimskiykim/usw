## 1. Preserve removed runtime

- [x] 1.1 Copy the exact structured runtime, references, fixtures and mixed tests from the migration manifest into `research/structured-runtime/`
- [x] 1.2 Move the two superseded active change packages into the research snapshot and add unsupported/superseded documentation

## 2. Text-first execution

- [x] 2.1 Replace the production runner with safe one-read Markdown resolution, byte identity and migration shims
- [x] 2.2 Update run-flow and create-flow contracts and references so plain and `version-2` use the same model path
- [x] 2.3 Add focused resolver, invocation, migration and legacy `FLOW.json` tests

## 3. Optional generic handoff

- [x] 3.1 Add strict top-level `handoff` boolean parsing with backwards-compatible default `true`
- [x] 3.2 Make initialization create or skip generic HANDOFF according to effective configuration
- [x] 3.3 Implement the generic status matrix, operation identity, atomic writes and read-only legacy recovery
- [x] 3.4 Update handoff/init skill and command contracts and add matrix coverage

## 4. Product contracts

- [x] 4.1 Replace obsolete normative runtime, orchestration and handoff requirements with text-first requirements
- [x] 4.2 Update README, examples, plugin metadata and package checks without changing unrelated skills
- [x] 4.3 Ensure production code and package surfaces have no import or runtime reference to `research/`

## 5. Verification

- [x] 5.1 Run strict OpenSpec validation and the complete production unittest discovery
- [x] 5.2 Verify research tests are excluded, packaging excludes research, legacy files remain untouched and all change tasks are complete

## 6. Review repair

- [x] 6.1 Bind every handoff Outcome to its expected operation, serialize read-check-write transitions and prevent save from bypassing the state matrix
- [x] 6.2 Resolve flow and local-state paths descriptor-relatively without following intermediate symlinks
- [x] 6.3 Remove remaining machine-runtime claims from normative specs and active project flows, and reconcile delta/main requirement identities
- [x] 6.4 Exclude Python bytecode from installed packages and cover the installed tree
- [x] 6.5 Give every Begin a unique invocation identity and reject idle Outcome or Save without an active operation
- [x] 6.6 Run the full suite, strict OpenSpec validation and a fresh two-branch `chat-review`
