# Task 1.2: Remove legacy refinement and Git-policy consumers

## Artifact model

- `v1`

## Result

Intent clarification uses only safe local `.usw/refinements/` storage without reading shared refinement configuration or enforcing repository tracking policy.

## Scope

- Remove active discovery of configured and historical shared refinement roots.
- Preserve historical shared sessions byte-for-byte without blocking a new local session with the same ID.
- Remove Git tracked/ignore checks while retaining local path-type and symlink protections.
- Update focused refinement tests and skill instructions for the accepted local storage contract.

## Non-scope

- Migrating or deleting historical shared sessions.
- Weakening static local path and symlink validation.
- Changing the one-decision-case dialogue model.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/intent-clarification/spec.md`
- Specification: `../../specs/task-refinement/spec.md`

## Dependencies

- Task 1.1 removes `refinement.root` from the shared initializer configuration model.

## Definition of done

- Intent clarification no longer reads `refinement.root` or shared refinement sessions.
- Git-tracked or custom-ignored local refinement state does not block clarification.
- Historical shared bytes and static symlink protections remain intact.

## Verification

- Run: `python3 -m unittest tests.test_refine_task -v`
- Expect: all intent clarification state tests pass under the user-owned tracking policy.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | full-suite dependency exposed | `cr-001` | `tasks.md` | pending | `tasks.md` |
