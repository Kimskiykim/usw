# Task 1.3: Убрать shared refinement default из инициализации

## Artifact model

- `v1`

## Result

New USW workspaces initialize clarification as developer-local state and no
longer create or advertise `usw/refinements/` as a shared managed root.

## Scope

- Remove the shared refinement root from generated default configuration and managed-directory creation.
- Keep legacy `refinement.root` parseable only for explicit compatibility diagnostics.
- Ensure `.usw` ignore/privacy initialization covers `.usw/refinements/`.
- Update initializer reports, fallback instructions and configuration tests.

## Non-scope

- A configuration schema version migration unrelated to refinement storage.
- Removing historical project directories or configuration fields automatically.
- Changing flow and review roots.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/intent-clarification/spec.md`

## Dependencies

- Task 1.2.

## Definition of done

- Fresh initialization creates no shared refinement directory.
- Local clarification storage is safely ignored and available on first use.
- Legacy configuration produces a precise diagnostic without redirecting new writes.
- Existing files remain byte-for-byte unchanged during initialization.

## Verification

- Run: `python3 -m unittest tests.test_init_usw tests.test_end_to_end -v`
- Expect: fresh, repeated, legacy-config and privacy initialization scenarios pass.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | proposal, design, intent-clarification spec |
