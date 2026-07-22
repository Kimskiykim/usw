# Task 4.2: Apply agreed critical-review corrections

## Artifact model

- `v1`

## Result

The initialization contract and implementation incorporate the four owner-approved critical-review corrections without restricting explicit user configuration.

## Scope

- Remove only a partially written file created by the current `create_file` attempt, then prove a successful retry.
- Clarify that explicit standalone custom roots under `openspec/**` are honored; directory detection alone and the OpenSpec provider do not authorize writes there.
- Modify the legacy shared-refinement requirement so historical sessions are preserved but neither discovered nor used to block a local session.
- List the exact standard initializer filenames in the delta spec and assert them independently from production constants.
- Re-run focused and complete regression verification.

## Non-scope

- Workspace-wide transactional rollback.
- Concurrent symlink TOCTOU hardening.
- Rejecting user-selected standalone roots because of their directory name.
- Deleting, reading, or migrating historical shared refinement sessions.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/project-initialization/spec.md`
- Specification: `../../specs/workspace-configuration/spec.md`
- Specification: `../../specs/intent-clarification/spec.md`

## Dependencies

- Tasks 1.1 through 4.1 are complete.
- Owner decisions from the `dev-test` critical-review GATE are recorded in `.usw/HANDOFF.md`.

## Definition of done

- A fault-injected partial file is removed and the next create-only attempt succeeds.
- Explicit standalone roots under `openspec/**` remain supported and tested.
- Delta specs archive cleanly into the intended refinement and initialization contract.
- Exact generated filenames are pinned by literals outside production code.

## Verification

- Run: `python3 -m unittest tests.test_init_usw tests.test_refine_task tests.test_package_layout -v`
- Run: `python3 -m unittest discover -s tests -v`
- Run: `openspec validate align-usw-init-contract --strict`
- Expect: all available tests and strict validation pass.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | owner approved critical-review corrections | `cr-001` | `tasks.md` | pending | `tasks.md` |
