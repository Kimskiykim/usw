# Task 1.2: Перенести state writer в `.usw/refinements`

## Artifact model

- `v1`

## Result

Every new clarification session is safely stored under the developer-local
`.usw/refinements/<refinement-id>/` root, while historical shared sessions are
left unchanged.

## Scope

- Resolve a fixed local clarification root independent of provider configuration.
- Preserve the three-file resumable model and one-case update behavior.
- Add safe-ID, path traversal, symlink and Git-ignore privacy checks.
- Detect a matching legacy shared session and stop with an explicit migration diagnostic.
- Update behavioral tests for create, resume, supersede, outcome and unsafe paths.

## Non-scope

- Automatically moving, copying, merging or deleting legacy shared sessions.
- Changing `.usw/HANDOFF.md` semantics.
- Writing provider-owned planning artifacts.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/intent-clarification/spec.md`

## Dependencies

- Task 1.1.

## Definition of done

- New and resumed sessions use only `.usw/refinements/`.
- Unsafe or trackable local state is rejected before a write.
- Legacy shared state remains byte-for-byte unchanged and is never selected silently.
- A ready outcome may record no recommended next flow.

## Verification

- Run: `python3 -m unittest tests.test_refine_task -v`
- Expect: local persistence, privacy, resume, supersession and legacy-preservation scenarios pass.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | proposal, design, intent-clarification spec |
