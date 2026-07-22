# Task 2.2: Align documentation and OpenSpec-owned instructions

## Artifact model

- `v1`

## Result

User-facing documentation and packaged assets describe the exact initialization boundary with one authoritative repo-local OpenSpec instruction file.

## Scope

- Split README into artifacts created by `/usw-init` and lazy local artifacts.
- State that `.usw/.gitignore` is generated convenience and repository tracking remains user-owned.
- Remove active `refinement.root` and automatic privacy-enforcement language from command and skill documentation.
- Update repo-local `openspec/AGENTS.md` to current task/evidence roles.
- Delete the unreachable packaged OpenSpec AGENTS template and adjust packaging assertions.
- Document provider-aware directory hints, OpenSpec no-write behavior and safe retry after partial failure.

## Non-scope

- Writing into any external or user-owned OpenSpec workspace during initialization.
- Automatic migration of historical shared refinement sessions.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/project-initialization/spec.md`
- Specification: `../../specs/intent-clarification/spec.md`
- Specification: `../../specs/task-refinement/spec.md`

## Dependencies

- Task 1.1 and Task 2.1 establish implementation and fallback terminology.

## Definition of done

- README inventory matches observed provider-specific initialization results.
- Only repo-local `openspec/AGENTS.md` remains as the OpenSpec workflow instruction source.
- No documentation promises enforced Git privacy or active shared refinement configuration.

## Verification

- Run: `python3 -m unittest tests.test_package_layout tests.test_init_usw -v`
- Expect: documentation/package assertions and initialization tests pass.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
