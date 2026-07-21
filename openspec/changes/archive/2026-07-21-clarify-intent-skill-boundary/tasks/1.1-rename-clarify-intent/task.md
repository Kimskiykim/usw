# Task 1.1: Переименовать skill и сузить его публичный контракт

## Artifact model

- `v1`

## Result

Package exposes `usw-refine-intent` as the single public identity for a skill
that conducts dialogue, clarifies one decision case per turn, and saves local
non-normative notes.

## Scope

- Rename the skill directory, frontmatter identity, script references and agent metadata.
- Rewrite the skill description and instructions around intent rather than task/change planning.
- Update session, decisions and outcome assets to allow a standalone result with no next flow.
- Remove the old `usw-refine-task` identity from packaged discovery.

## Non-scope

- Changing the state writer's filesystem root.
- Rewiring standard flow actions.
- Renaming `usw-brainstorm-solutions`.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/intent-clarification/spec.md`

## Dependencies

- None.

## Definition of done

- Supported harnesses discover `usw-refine-intent` and not the former identity.
- The contract lists exactly dialogue, sequential clarification and local notes as primary responsibilities.
- The skill explicitly forbids implicit backlog, spec, planning and implementation work.

## Verification

- Run: `python3 -m unittest tests.test_package_layout tests.test_install -v`
- Expect: package discovery and installation tests pass with only the new skill identity.

## Contract revision

- `cr-002`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | superseded | public name reconsidered before execution |
| 1 | contract revised | `cr-002` | pending | pending | `usw-refine-intent` naming decision |
