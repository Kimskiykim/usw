# Task 2.1: Make LLM initialization functionally equivalent

## Artifact model

- `v1`

## Result

The consented LLM path supports every supported v1 configuration and produces the same provider-specific created/preserved outcome as the Python path.

## Scope

- Replace default-standalone-only fallback rules with the shared v1 configuration and path contract.
- Allow safe custom roots and both supported providers without requiring Python.
- Preserve any `openspec/` directory and continue USW-owned initialization.
- Remove Git tracked/ignore enforcement from preflight and verification.
- Retain explicit user consent, create-only writes, static path checks, readback and weaker-determinism disclosure.
- Add static/package tests that pin the parity contract.

## Non-scope

- Executing OpenSpec provider operations during initialization.
- Supporting schema versions or providers outside the existing v1 closed set.
- Replacing the Python path as the preferred deterministic executor.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification: `../../specs/project-initialization/spec.md`

## Dependencies

- Task 1.1 defines the accepted Python behavior used as the parity target.

## Definition of done

- The fallback no longer rejects safe custom roots or OpenSpec presence merely because Python is absent.
- Its artifact inventory, no-overwrite boundary and reporting match the Python contract for v1.
- Tests detect future reintroduction of reduced functional scope.

## Verification

- Run: `python3 -m unittest tests.test_package_layout -v`
- Expect: initialization skill and fallback parity assertions pass.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
