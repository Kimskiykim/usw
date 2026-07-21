# Task 2.1: Развести clarification и solution evaluation в registry

## Artifact model

- `v1`

## Result

Standard flows invoke stateful intent clarification and stateless solution
evaluation through distinct exact capability mappings.

## Scope

- Map `clarify-intent` to `usw-refine-intent`.
- Keep `select-approach` mapped to `usw-brainstorm-solutions`.
- Narrow brainstorm wording and capability inputs to a bounded problem and existing context.
- Update flow authority and atomic outcome tests for one-case clarification.

## Non-scope

- Renaming the brainstorm skill.
- Chaining clarification directly into solution evaluation.
- Changing proposal/spec writing actions.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Specification delta: `../../specs/intent-clarification/spec.md`

## Dependencies

- Task 1.1.

## Definition of done

- `clarify-intent` resolves only to the local stateful capability.
- `select-approach` resolves only to the bounded solution-evaluation capability.
- Each capability returns control after one action and never invokes the other implicitly.

## Verification

- Run: `python3 -m unittest tests.test_flow_orchestrator tests.test_atomic_skill_contracts -v`
- Expect: registry identity, write authority and one-action return contracts pass.

## Contract revision

- `cr-002`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | superseded | public name reconsidered before execution |
| 1 | contract revised | `cr-002` | pending | pending | `clarify-intent -> usw-refine-intent` |
