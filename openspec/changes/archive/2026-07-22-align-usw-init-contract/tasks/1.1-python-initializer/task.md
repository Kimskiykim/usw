# Task 1.1: Align the Python initializer and focused tests

## Artifact model

- `v1`

## Result

The Python `/usw-init` path implements the accepted user-owned Git policy, provider-aware directory hint, removed legacy refinement configuration, exact artifact inventory, and partial-failure guidance.

## Scope

- Remove Git tracked/ignore enforcement while preserving creation of `.usw/.gitignore`.
- Remove active and diagnostic behavior for `refinement.root` without migrating historical files.
- Treat `openspec/` as a directory hint and emit provider-aware messages.
- Preserve create-only, static symlink, configured-root and idempotent behavior.
- Report safe retry guidance on a partial I/O failure.
- Update focused initialization tests for standalone, OpenSpec, custom roots, lazy local directories and the removed policies.

## Non-scope

- LLM fallback instructions.
- Transactional writes or concurrent symlink TOCTOU hardening.
- Provider artifact validation.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/project-initialization/spec.md`
- Specification: `../../specs/workspace-configuration/spec.md`

## Dependencies

- None.

## Definition of done

- Python initialization accepts supported v1 standalone and OpenSpec configurations without inspecting Git tracking state.
- Existing files and OpenSpec artifacts remain byte-for-byte unchanged.
- Focused tests cover provider-aware messaging, exact immediate inventory, lazy local paths and safe retry behavior.

## Verification

- Run: `python3 -m unittest tests.test_init_usw -v`
- Expect: all initialization tests pass with no Git privacy enforcement expectations.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
