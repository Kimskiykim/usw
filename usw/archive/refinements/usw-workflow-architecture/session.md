# Refinement session: USW workflow architecture

- ID: `usw-workflow-architecture`
- Status: ready
- Updated: 2026-07-20T18:23:15+03:00
- Target: USW workflow and artifact architecture
- Current case: None — all scoped decision cases are closed.

## Goal

Define a standalone USW workflow with persistent planning artifacts, optional
OpenSpec compatibility, and explicit responsibility contracts for Analysis,
Development, and Testing with internal and cross-role review gates on one
lifecycle through delivery.

## Scope

- Shared and developer-local artifact roles.
- Standalone USW and OpenSpec-compatible provider behavior.
- Skill orchestration and iterative task refinement.
- Planning and execution boundaries.
- A common lifecycle from intent discovery through delivery.
- Specification complexity assessment and decomposition.
- Per-flow input, artifact ownership, allowed writes, verdicts, transitions,
  and return loops.

## Non-scope

- Implementing the complete provider, change, planning, and execution flows in
  this refinement session.

## Confirmed context

- USW must work without OpenSpec installed.
- OpenSpec is installed in USW development environments to test compatibility.
- Shared USW artifacts use `usw/` by default; `.usw/` remains developer-local.
- Skill chains are allowed and will be described by `flow-scenario-*.md`.
- Every supported work flow follows the same lifecycle stages: receive the
  task, clarify intent and done criteria, gather project context, choose an
  approach, form and decompose the specification when needed, plan executable
  steps, execute, verify and repair, perform final verification, update
  documentation or handoff, and deliver.
- Specification complexity must be assessed before executable planning; when
  the work is too broad, the system proposes a decomposition and waits for the
  user to choose.
- Three role-oriented flows share the lifecycle: Analysis, Development, and
  Testing; Delivery is the terminal lifecycle transition rather than another
  role flow.
- A flow is a responsibility boundary and does not require a separate agent.
- Every role flow contains its own internal review before its result is offered
  to another role. Development includes writing implementation-adjacent tests
  before that internal review.
- A separate transition review accepts or rejects the handoff between roles,
  which may be performed by different people.
- During the pilot, people are the review gates; USW does not enforce a role
  status machine or mandatory verdict enumeration.

## Assumptions

- The final config schema and flow-scenario file contract remain to be specified.
- The initial pinned OpenSpec version will be selected and recorded when the
  compatibility test infrastructure is implemented.
- The minimum skill set will be derived only after the three role-flow and two
  review-gate contracts are explicit.

## Decision cases

- [x] `C-001` — Define the relationship between USW and OpenSpec.
- [x] `C-002` — Choose the default shared artifact root.
- [x] `C-003` — Handle an existing OpenSpec workspace during USW initialization.
- [x] `C-004` — Allow and orchestrate skill chains.
- [x] `C-005` — Define execution scope and stopping rules.
- [x] `C-006` — Define the OpenSpec compatibility test contract.
- [x] `C-007` — Finalize task, plan, evidence, and handoff authority.
- [x] `C-008` — Define what specification decomposition produces.
- [x] `C-009` — Defer minimum skill ownership until flow contracts are explicit.
- [x] `C-010` — Replace the standalone delivery-gate case with per-flow contracts.
- [x] `C-011` — Define the Analysis input contract.
- [x] `C-012` — Define Analysis-owned artifacts.
- [x] `C-013` — Define Analysis allowed writes.
- [x] `C-014` — Define Analysis exit verdicts.
- [x] `C-015` — Define Analysis transitions and return loops.
- [x] `C-016` — Define the Development input contract.
- [x] `C-017` — Define Development-owned artifacts.
- [x] `C-018` — Define Development allowed writes.
- [x] `C-019` — Define Development exit verdicts.
- [x] `C-020` — Define Development transitions and return loops.
- [x] `C-021` — Define the Testing input contract.
- [x] `C-022` — Define Testing-owned artifacts.
- [x] `C-023` — Define Testing allowed writes.
- [x] `C-024` — Define Testing exit verdicts.
- [x] `C-025` — Define Testing transitions and return loops.
- [x] `C-026` — Define the Review input contract.
- [x] `C-027` — Define Review-owned artifacts.
- [x] `C-028` — Retire standalone Review allowed-writes refinement.
- [x] `C-029` — Retire standalone Review verdict refinement.
- [x] `C-030` — Retire standalone Review transition refinement.
- [x] `C-031` — Distinguish internal review from cross-role transition review.
- [x] `C-032` — Define who owns cross-role transition review.
- [x] `C-033` — Define the pilot's human internal-review gate.
- [x] `C-034` — Keep human review decisions out of persistent runtime artifacts.
- [x] `C-035` — Separate coding-task completion from human review and Delivery.
- [x] `C-036` — Handle human findings after a coding task was checked complete.
- [x] `C-037` — Normalize routing after Review became a gate.
- [x] `C-038` — Define the OpenSpec artifact frontier after technical-design ownership moved to Development.
- [x] `C-039` — Derive the minimum flow-scenario and atomic-skill set.
- [x] `C-040` — Define the terminal Delivery contract and delivery-owner selection.
- [x] `C-041` — Persist reviewer-owned review receipts.
- [x] `C-042` — Place reviewer receipts across standalone and OpenSpec providers.

## Current case

None. The refinement outcome is ready for the planning-artifact update flow.

## Next action

Update the existing OpenSpec change coherently from `outcome.md`, confirming
each existing artifact revision before writing it; do not modify product code.

## References

- `skills/usw-refine-task/SKILL.md`
- `skills/usw-plan-small-steps/SKILL.md`
