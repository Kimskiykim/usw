# Refinement outcome: USW workflow architecture

- Refinement: `usw-workflow-architecture`
- Status: ready
- Updated: 2026-07-20T18:23:15+03:00
- Target: USW workflow and artifact architecture

## Goal

Provide a standalone USW workflow with persistent shared artifacts, optional
OpenSpec compatibility, composable skills, and explicit multi-skill flows.

## Agreed model

- USW works fully without OpenSpec; OpenSpec is an optional compatibility
  provider for users who already use it.
- OpenSpec is installed in USW development and CI environments to run real
  compatibility tests, not as a runtime dependency for all users.
- Shared configuration selects the artifact provider and root. Standalone USW
  uses the version-controlled `usw/` directory by default; `.usw/` remains
  ignored developer-local state.
- `/usw-init` only hints when an existing OpenSpec workspace is detected and
  never changes provider or OpenSpec files silently.
- Skill chains are allowed. A `usw-run-flow` orchestrator follows explicit
  `flow-scenario-*.md` files that own ordering, branches, write authority, and
  stop conditions.
- `usw-refine-task` handles one decision case and one user question per turn,
  persisting `session.md`, `decisions.md`, and a final `outcome.md`.
- Execution is owned by flow scenarios rather than `usw-plan-small-steps`; for
  an unqualified continuation, the flow presents valid scope options and waits
  for the user to choose instead of applying an implicit default.
- Compatibility tests use a real OpenSpec installation in development and CI;
  one pinned version is release-blocking, while a separate latest-version probe
  is visible but non-blocking.
- Each state concern has one owner: `tasks.md` owns change-task completion,
  `task.md` owns scope and definition of done, `plan.md` owns step progress,
  `evidence.md` owns verification facts, task `handoff.md` is optional shared
  transfer, and `.usw/HANDOFF.md` owns the personal resume pointer.
- All supported work follows one common lifecycle from task receipt and intent
  clarification through context, approach, specification, planning, execution,
  verification and repair, final verification, documentation or handoff, and
  delivery.
- Specification complexity is assessed after project context and approach
  selection but before executable planning; an oversized specification produces
  a proposed decomposition that requires user approval.
- Related capabilities that share one delivery and verification boundary remain
  capability specs in one change; independently deliverable and verifiable
  parts become child changes under a shared parent goal.
- Three responsibility-oriented flows—Analysis, Development, and Testing—share
  the lifecycle and transition to Delivery; they do not require separate agents.
- Every role flow contains an internal review of its own result before handoff.
  Development includes writing implementation-adjacent tests before that review.
- Cross-role handoffs have a separate transition review that accepts or rejects
  the transfer of responsibility and may involve different people. Review is a
  gate type, not a fourth end-to-end role flow.
- The receiving responsibility owns transition review: Development accepts the
  Analysis handoff, Testing accepts the Development handoff, and an explicitly
  named delivery owner accepts the Testing handoff. A rejection returns findings
  to the sender without letting the receiver repair the sender's artifacts. An
  Analysis result requiring no product change goes directly to the named
  delivery owner's transition review.
- During the pilot, people are the internal and transition review gates. USW
  does not enforce a workflow state machine or mandatory role-verdict enum; a
  human asks the owner to repair problems and explicitly permits a handoff when
  satisfied.
- Every run names its delivery scope, exact tested source, current evidence,
  unresolved observations, and delivery owner. The user is the default owner
  unless explicitly delegating that responsibility. Terminal acceptance does
  not authorize commit, push, pull request, deployment, release, or another
  external action; each requires separate explicit authority.
- Every human review attempt creates a new immutable reviewer-owned receipt with
  the gate, reviewed scope and identity, reviewer, verdict, and references to
  findings and evidence. Receipts do not copy canonical content; handoffs only
  reference the applicable accepted receipt.
- Review receipts use a provider-neutral shared collection, defaulting to
  `usw/reviews/<subject-id>/<review-id>.md`. They may reference standalone or
  OpenSpec-backed subjects but do not modify or duplicate provider artifacts.
- Skill boundaries are derived only after each flow's input, owned artifacts,
  allowed writes, exit verdicts, transitions, and return loops are explicit.
- The pilot has three role scenarios—Analysis, Development, and Testing—under
  one `usw-run-flow` orchestrator. It reuses the existing brainstorming,
  refinement, small-step planning, and handoff skills and adds only
  provider-aware artifact management, bounded task execution, and independent
  verification/evidence capabilities. Human review remains a scenario gate;
  initialization and explanation remain utilities outside the role lifecycle.
- During the pilot, Analysis accepts raw intent or flow returns with available
  canonical references and findings; it does not require a hard request schema,
  parser, or separate intake artifact.
- Analysis owns feature backlog, refinement session, decision and outcome
  artifacts, change proposal, and normative capability specifications. Pilot
  product context and complexity conclusions live in those artifacts rather
  than new file types.
- Analysis may update those artifacts, create a user-approved parent or child
  specification split, and write a minimal reference-based handoff. It cannot
  write code, tasks, plans, execution status, evidence, tests, or delivery
  status.
- Analysis readiness, decisions, split proposals, and blockers are communicated
  in plain language and resolved by people rather than serialized as required
  workflow statuses.
- Transitions and return loops route findings directly to the flow that owns the
  affected artifact: specification findings to Analysis, implementation and
  plan findings to Development, and test-evidence findings to Testing.
- Development starts from canonical specification references, Analysis
  readiness, and a user-selected scope, optionally carrying return findings,
  evidence references, worktree state, and handoff context without a hard pilot
  input schema.
- Development owns technical design, task index and contracts, executable plan,
  implementation changes, development handoff, and its own entries in canonical
  evidence; Analysis retains product proposal and specification authority.
- With the OpenSpec `spec-driven` provider, Analysis completes `proposal` and
  capability `specs` and may hand off while the aggregate change is incomplete.
  Development then creates technical `design` and `tasks` through the native
  artifact graph; role-oriented flows do not call bundled `openspec-propose`
  across that authority boundary.
- Development may update those technical artifacts, code, tests, plan progress,
  its evidence, and its coding-task checkboxes, but cannot edit product specs,
  independent Testing records, or claim terminal Delivery.
- `tasks.md` is the coding agent's journal. The agent checks a task after its
  `task.md` definition of done, plan, and required local checks are satisfied;
  this does not mean that a human reviewer, Testing, or Delivery accepted it.
- A blocking human finding within the original task contract reopens the same
  coding task from `[x]` to `[ ]`; the agent repairs, reverifies, and checks it
  again. Independent new scope becomes a separate task only after user approval.
- Development's readiness, partial scope, need for Analysis or user input, and
  blockers are communicated in plain language and gated by human review.
- After repair, the lifecycle resumes at the earliest gate whose contract or
  evidence became stale; code changes normally repeat Testing before the
  applicable transition review, while unaffected evidence remains current.
- Testing starts from the normative product contract, selected scope, exact
  tested source identity, Development readiness and evidence, and available
  handoff references. It treats technical design as context and independently
  selects its checks without requiring a hard pilot input schema or prebuilt
  test plan.
- Testing owns the independent acceptance, integration, end-to-end, and
  regression test assets it creates, together with its findings, evidence,
  verdict, and handoff. Development retains the unit and
  implementation-adjacent tests it creates; no separate test-plan or test-report
  artifact is required during the pilot.
- Testing may update only those independent test assets and its own findings,
  evidence, verdict, and handoff. It may correct a faulty check without weakening
  the accepted requirement, but it cannot change the inspected product, product
  contract, Development artifacts, other roles' records, completion, or delivery
  status.
- A human Testing gate advances successful work, returns implementation defects
  to Development and product-contract problems to Analysis, and waits on
  external blockers. Testing may carry non-blocking observations but cannot
  waive a failed requirement or accept delivery risk.

## Constraints

- Never make OpenSpec a mandatory runtime dependency for standalone USW users.
- Never switch providers or overwrite adopted artifacts implicitly.
- Never let an atomic skill independently orchestrate other skills; use the
  calling flow scenario.
- Never begin execution from an unqualified continuation until the user has
  selected an explicit scope.
- Never record planned verification as completed evidence.
- Complete a change task only when its definition of done is satisfied and
  required evidence is current and successful.

## Remaining unknowns

- Exact `usw.yaml` schema and migration/versioning policy.
- Exact `flow-scenario-*.md` contract and initial scenario set.
- Initial pinned OpenSpec version (to be selected and recorded during
  compatibility-test implementation).
- Safe replanning behavior when completed steps or evidence already exist.

## Decision references

- `D-001`
- `D-002`
- `D-003`
- `D-004`
- `D-005`
- `D-008`
- `D-009`
- `D-010`
- `D-011`
- `D-012`
- `D-013`
- `D-015`
- `D-017`
- `D-020`
- `D-021`
- `D-025`
- `D-026`
- `D-027`
- `D-032`
- `D-033`
- `D-034`
- `D-036`
- `D-038`
- `D-039`
- `D-040`
- `D-041`
- `D-042`
- `D-043`
- `D-044`

## Recommended next flow

Update the existing OpenSpec change coherently from this outcome without
modifying product code, confirming each artifact revision before writing it.
