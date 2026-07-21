# Refinement decisions: USW workflow architecture

## `D-001` — Keep USW independent from OpenSpec

- Case: `C-001`
- Status: accepted
- Decided: 2026-07-20
- Decision: USW provides a complete standalone workflow; OpenSpec is an optional
  compatibility provider for users who already use it.
- Basis: users without OpenSpec must still be able to use all core USW features.
- Consequences: OpenSpec is a development and compatibility-test dependency,
  not a USW runtime dependency.
- Supersedes: None.
- Follow-up cases: `C-006`.

## `D-002` — Configure the artifact provider and root

- Case: `C-002`
- Status: accepted
- Decided: 2026-07-20
- Decision: select artifact behavior through shared configuration and use
  `usw/` as the default shared artifact root.
- Basis: provider choice must be deterministic and consistent for the team.
- Consequences: `usw/` is version-controlled while `.usw/` remains ignored and
  developer-local.
- Supersedes: None.
- Follow-up cases: None.

## `D-003` — Only hint when OpenSpec is detected

- Case: `C-003`
- Status: accepted
- Decided: 2026-07-20
- Decision: `/usw-init` reports an existing OpenSpec workspace but does not
  switch providers or modify OpenSpec artifacts automatically.
- Basis: initialization must not silently change the team's selected workflow.
- Consequences: adopting OpenSpec requires an explicit configuration change or
  dedicated flow.
- Supersedes: None.
- Follow-up cases: `C-006`.

## `D-004` — Orchestrate composable skills through flow scenarios

- Case: `C-004`
- Status: accepted
- Decided: 2026-07-20
- Decision: allow skill chains and define their ordered actions in
  `flow-scenario-*.md`, coordinated by a `usw-run-flow` skill.
- Basis: overlapping skills need explicit sequencing rather than mutual
  exclusion.
- Consequences: atomic skills perform one capability; flow scenarios own
  ordering, branches, write authority, and stop conditions.
- Supersedes: None.
- Follow-up cases: `C-005`.

## `D-005` — Persist iterative task refinement

- Case: `C-004`
- Status: accepted
- Decided: 2026-07-20
- Decision: add `usw-refine-task` to discuss one decision case per turn and
  persist session, decisions, and outcome artifacts.
- Basis: long questionnaire-style planning must survive multiple turns and feed
  later change or planning flows.
- Consequences: refinement state is shared under `usw/refinements/` by default;
  the skill does not implement the target work.
- Supersedes: None.
- Follow-up cases: `C-005`, `C-006`, `C-007`.

## `D-006` — Execute one complete task by default

- Case: `C-005`
- Status: superseded
- Decided: 2026-07-20
- Decision: the proposal was to infer explicit `step`, `task`, or `change`
  scope from the user's request and execute the current task for an unqualified
  continuation.
- Basis: this recommendation was recorded before the user explicitly confirmed
  it and therefore is not authoritative.
- Consequences: `C-005` is open again and requires one user decision.
- Supersedes: None.
- Follow-up cases: None.

## `D-007` — Pin the guaranteed OpenSpec compatibility version

- Case: `C-006`
- Status: superseded
- Decided: 2026-07-20
- Decision: the proposal was to make one pinned OpenSpec version
  release-blocking and run a separate latest-version compatibility probe.
- Basis: the user confirmed real OpenSpec installation for compatibility tests,
  but did not confirm this versioning and release policy.
- Consequences: `C-006` remains open for the exact supported-version contract.
- Supersedes: None.
- Follow-up cases: None.

## `D-008` — Give each state concern one authoritative artifact

- Case: `C-007`
- Status: accepted
- Decided: 2026-07-20
- Decision: store change-task completion in `tasks.md`, the task contract in
  `task.md`, step progress in `plan.md`, verification facts in `evidence.md`,
  optional shared transfer in task `handoff.md`, and the personal resume pointer
  in `.usw/HANDOFF.md`.
- Basis: different kinds of state need distinct owners without duplicating the
  same fact across files.
- Consequences: flows update only the artifact that owns the state they change;
  task completion requires the task definition of done and current successful
  evidence.
- Supersedes: None.
- Follow-up cases: None.

## `D-009` — Test compatibility against a real OpenSpec installation

- Case: `C-006`
- Status: accepted
- Decided: 2026-07-20
- Decision: install real OpenSpec in USW development and test environments to
  verify compatibility while keeping it out of standalone USW runtime
  dependencies.
- Basis: compatibility cannot be established by testing only USW-owned
  templates, and standalone users must not be required to install OpenSpec.
- Consequences: integration tests exercise an actual OpenSpec installation;
  the exact supported-version and release policy still requires a decision.
- Supersedes: `D-007`.
- Follow-up cases: `C-006`.

## `D-010` — Require the user to choose an execution scope

- Case: `C-005`
- Status: accepted
- Decided: 2026-07-20
- Decision: when a continuation request does not identify a step, task, or
  change scope, the execution flow presents the available scope options and
  waits for the user to choose; it does not apply an implicit default.
- Basis: the user must retain control over how much work an execution flow is
  authorized to perform.
- Consequences: flow scenarios must define how to discover and present valid
  scope options, and execution cannot begin until the user selects one.
- Supersedes: `D-006`.
- Follow-up cases: None.

## `D-011` — Gate releases on one pinned OpenSpec version

- Case: `C-006`
- Status: accepted
- Decided: 2026-07-20
- Decision: test one pinned OpenSpec version as a release-blocking compatibility
  guarantee and run a separate visible latest-version probe that does not block
  USW releases.
- Basis: a pinned version keeps release verification reproducible, while the
  latest probe reveals upcoming compatibility work without making upstream
  releases destabilize the USW release process.
- Consequences: the pinned version must be selected explicitly, recorded in
  test infrastructure, and updated deliberately; latest-version failures must
  remain visible and be triaged even though they are non-blocking.
- Supersedes: `D-007`.
- Follow-up cases: None.

## `D-012` — Use one common lifecycle with a specification complexity gate

- Case: `C-008`
- Status: accepted
- Decided: 2026-07-20
- Decision: all supported work flows follow one common lifecycle from receiving
  a task through intent and done criteria, project context, approach selection,
  specification formation, executable planning, step execution, verification
  and repair, final verification, documentation or handoff, and delivery. Before
  executable planning, the flow assesses specification complexity and proposes
  a decomposition when the work is too broad.
- Basis: every task needs the same observable safety gates even when optional
  stages are short or skipped, and oversized specifications must be detected
  before they become oversized implementation plans.
- Consequences: the lifecycle is the shared contract across flows; a proposed
  specification split is not applied until the user selects or approves it.
- Supersedes: None.
- Follow-up cases: `C-008`, `C-009`, `C-010`.

## `D-013` — Decompose specifications adaptively

- Case: `C-008`
- Status: accepted
- Decided: 2026-07-20
- Decision: keep related capabilities that share one delivery and verification
  boundary as capability specs within one change, and create separate child
  changes only for parts that can be delivered and verified independently.
- Basis: capability specs preserve cohesion without coordination overhead,
  while independently valuable work needs its own lifecycle and completion
  gate.
- Consequences: complexity assessment proposes a parent goal, capability or
  child boundaries, dependencies, and acceptance boundaries; no split is
  materialized until the user approves it.
- Supersedes: None.
- Follow-up cases: `C-009`.

## `D-014` — Define role flows before deriving skills

- Case: `C-009`
- Status: superseded
- Decided: 2026-07-20
- Decision: use four responsibility-oriented flows—Analysis, Development,
  Testing, and Review—on one lifecycle ending in Delivery. A flow is an
  authority boundary rather than an agent identity. Testing and Review record
  findings and verdicts without modifying their own object of inspection by
  default. Derive the number and boundaries of skills only after each flow's
  input, owned artifacts, allowed writes, verdicts, transitions, and return
  loops are explicit.
- Basis: counting skills before responsibility contracts are known either maps
  every stage to a skill or combines incompatible authority prematurely.
- Consequences: the earlier five-versus-six-skill choice and standalone final
  delivery-gate case are replaced by sequential contract refinement, starting
  with Analysis.
- Supersedes: None.
- Follow-up cases: `C-011`, `C-012`, `C-013`, `C-014`, `C-015`.
- Replaced by: `D-032`.

## `D-015` — Pilot Analysis without a hard input schema

- Case: `C-011`
- Status: accepted
- Decided: 2026-07-20
- Decision: during the technology pilot, Analysis accepts raw user intent or a
  return from another flow with whatever canonical references and findings are
  available. It requires enough context to proceed without losing the original
  request or return evidence, but does not require a versioned request envelope,
  parser, or separate intake artifact.
- Basis: a hard schema before real workflow usage would create side development
  and encode assumptions that the pilot has not validated.
- Consequences: flow examples document expected input information
  descriptively; recurring stable fields may become a versioned contract only
  after pilot evidence demonstrates the need.
- Supersedes: None.
- Follow-up cases: `C-012`.

## `D-016` — Reuse existing analytical and specification artifacts

- Case: `C-012`
- Status: superseded
- Decided: 2026-07-20
- Decision: Analysis owns refinement `session.md`, `decisions.md`, and
  `outcome.md`, plus change `proposal.md`, optional `design.md`, and capability
  specification artifacts. During the pilot, project context, complexity
  assessment, and decomposition rationale are recorded in those artifacts
  instead of new `context.md`, `complexity.md`, or request files.
- Basis: these artifacts already separate decisions from normative
  specification and work in both the current workflow and OpenSpec-compatible
  planning without adding side-development schemas.
- Consequences: executable task indexes, plans, implementation evidence, and
  delivery status are not Analysis-owned artifacts.
- Supersedes: None. Replaced by `D-021`.
- Follow-up cases: `C-013`.

## `D-017` — Limit Analysis writes to owned artifacts and references

- Case: `C-013`
- Status: accepted
- Decided: 2026-07-20
- Decision: Analysis may create and update its refinement and specification
  artifacts, materialize user-approved parent or child specification artifacts,
  and write the minimum reference-based handoff needed to transfer control. It
  must not modify product code, task indexes or contracts, executable plans,
  execution status, verification evidence, test results, or delivery status.
- Basis: a minimal handoff allows the pilot to run without a separate transition
  store while preserving the boundary between specification and execution.
- Consequences: handoffs reference canonical artifacts rather than copying them;
  Development owns all executable planning and implementation writes.
- Supersedes: None.
- Follow-up cases: `C-014`, `C-015`.

## `D-018` — Use explicit Analysis verdicts on a small state lifecycle

- Case: `C-014`
- Status: superseded
- Decided: 2026-07-20
- Decision: a newly created work item starts at `new`; when Analysis begins it
  becomes `active`, and it may become `waiting`, `blocked`, or `completed`.
  Analysis emits one of `ready-for-development`, `decision-required`,
  `split-proposed`, `blocked`, or `no-change-required` as the reason for the
  state transition. These are descriptive pilot labels rather than a versioned
  serialized schema.
- Basis: separating lifecycle state from exit reason makes the current position
  visible while preserving actionable role-specific outcomes.
- Consequences: decision and split verdicts wait for the user and resume the
  same Analysis flow; blockers resume after their condition clears; completed
  verdicts transfer control according to the transition contract.
- Supersedes: None.
- Follow-up cases: `C-015`.
- Replaced by: `D-034`.

## `D-019` — Route flow returns by artifact ownership

- Case: `C-015`
- Status: superseded
- Decided: 2026-07-20
- Decision: route a finding directly to the flow that owns the affected
  canonical artifact. `ready-for-development` advances from Analysis to
  Development; decision, split, and blocker outcomes pause and resume Analysis;
  `no-change-required` goes to Review for independent confirmation before
  Delivery. Specification or product-decision findings return to Analysis,
  implementation or plan findings to Development, and test-evidence findings to
  Testing.
- Basis: owner routing avoids sending a defect through flows that are not
  allowed to repair the affected artifact while keeping every transition tied
  to an explicit verdict and canonical references.
- Consequences: the lifecycle graph permits direct return edges rather than only
  adjacent transitions; Review routes each finding according to the artifact it
  concerns.
- Supersedes: None.
- Follow-up cases: `C-016`, `C-020`.
- Replaced by: `D-039`.

## `D-020` — Start Development from canonical specification and selected scope

- Case: `C-016`
- Status: accepted
- Decided: 2026-07-20
- Decision: Development starts from canonical proposal, optional design, and
  capability-spec references, an Analysis `ready-for-development` verdict, and
  a user-selected execution scope. A re-entry may also include canonical
  Testing or Review findings, evidence references, current worktree state, and
  a minimal handoff. No hard serialized input schema is required during the
  pilot.
- Basis: Development needs authoritative requirements but must retain ownership
  of executable task and plan creation; raw intent alone would bypass Analysis.
- Consequences: if specification references are missing or scope remains
  ambiguous, Development does not begin implementation and returns to the
  applicable decision or Analysis boundary.
- Supersedes: None.
- Follow-up cases: `C-017`.

## `D-021` — Split product specification from technical design ownership

- Case: `C-017`
- Status: accepted
- Decided: 2026-07-20
- Decision: Analysis owns feature backlog, refinement state, `proposal.md`, and
  normative capability specs. Development owns technical `design.md`,
  `tasks.md`, granular `task.md`, `plan.md`, implementation source changes,
  development handoff, and only Development-authored entries in canonical
  `evidence.md`. Testing owns independent test entries and findings.
- Basis: domain Analysis determines what and why, while Development uses code
  and system knowledge to determine how. OpenSpec `design.md` documents the
  technical implementation approach rather than business requirements.
- Consequences: Development may begin with technical design before executable
  planning. A design discovery that changes product behavior returns to
  Analysis; the same agent may perform both flows sequentially but must switch
  authority boundaries.
- Supersedes: `D-016`.
- Follow-up cases: `C-018`.

## `D-022` — Allow technical writes without Development self-approval

- Case: `C-018`
- Status: superseded
- Decided: 2026-07-20
- Decision: Development may create and update technical design, task indexes and
  contracts, executable plans, implementation code, plan-step progress,
  Development-authored evidence entries, and development handoff. It must not
  edit product proposal/specs, independent Testing or Review records, final task
  completion, or delivery status.
- Basis: implementation must adapt technical artifacts as system knowledge
  improves, but the same responsibility must not change product requirements or
  approve its own result through later gates.
- Consequences: Development may declare a result ready for the next flow but
  final completion is written only after applicable Testing and Review gates;
  product-contract changes return to Analysis.
- Supersedes: None.
- Follow-up cases: `C-019`, `C-020`.
- Replaced by: `D-036`.

## `D-023` — Use explicit Development verdicts for bounded execution

- Case: `C-019`
- Status: superseded
- Decided: 2026-07-20
- Decision: Development emits `ready-for-testing` when the selected task is
  implemented and locally verified, `scope-complete` when only the explicitly
  authorized intermediate scope is finished, `analysis-required` when product
  proposal/specification must change, `decision-required` when the current
  technical work needs user choice, and `blocked` when an external condition
  prevents progress.
- Basis: selected step completion must not be confused with an implementation
  ready for independent Testing or with final delivery completion.
- Consequences: `scope-complete` waits for another user-selected scope;
  `ready-for-testing` advances to Testing; Analysis, decision, and blocker
  verdicts follow their dedicated return or resume paths.
- Supersedes: None.
- Follow-up cases: `C-020`.
- Replaced by: `D-034`.

## `D-024` — Resume at the earliest gate invalidated by a repair

- Case: `C-020`
- Status: superseded
- Decided: 2026-07-20
- Decision: after a finding returns to its artifact owner and is repaired, mark
  only affected evidence stale and resume at the earliest gate invalidated by
  the change. Code changes normally repeat Testing before Review; documentation
  changes that do not affect code or acceptance evidence may return directly to
  Review; product-spec changes pass through Analysis, Development, affected
  Testing, and Review.
- Basis: this preserves current evidence where valid without allowing repaired
  code to bypass independent verification.
- Consequences: every repair handoff identifies changed artifacts and affected
  evidence; a reporting flow does not automatically become the next flow if an
  earlier gate has become stale.
- Supersedes: None.
- Follow-up cases: `C-021`, `C-025`.
- Replaced by: `D-039`.

## `D-037` — Advance OpenSpec only to the active role's artifact frontier

- Case: `C-017`
- Status: superseded
- Decided: 2026-07-20
- Decision: role completion is independent from aggregate OpenSpec change
  completion. Under the `spec-driven` provider, Analysis creates `proposal`,
  optional `design`, and capability `specs`, then may emit
  `ready-for-development` while `tasks` is only `ready` and OpenSpec reports
  `isComplete: false`. Development owns creation of `tasks.md` and advances the
  change to apply-ready. Role-oriented flows do not invoke bundled
  `openspec-propose`, which crosses both artifact frontiers.
- Basis: the native artifact graph already exposes a safe dependency frontier,
  so USW can preserve role authority without a custom schema, parser, or draft
  task ownership convention during the pilot.
- Consequences: Analysis and Development request artifact instructions
  individually from OpenSpec; native `openspec-propose` remains an explicit
  convenience path outside the role-oriented flow. `C-017` remains open for
  Development ownership of plans, handoff, and role-scoped evidence entries.
- Supersedes: None.
- Follow-up cases: `C-017`.
- ID note: this entry originally duplicated `D-021`; it was assigned `D-037`
  before refinement finalization. Its Analysis-owned optional `design.md`
  assumption was replaced by `D-021`.
- Replaced by: `D-040`.

## `D-025` — Start Testing from the product contract and tested source identity

- Case: `C-021`
- Status: accepted
- Decided: 2026-07-20
- Decision: Testing starts from canonical `proposal.md` and normative capability
  specs, the selected test scope, the exact tested source or worktree identity,
  Development's `ready-for-testing` verdict, Development-authored evidence, and
  available handoff references. On re-entry it also receives prior defects and
  Testing evidence. Technical `design.md` is context, not product truth.
- Basis: independent Testing must evaluate a known implementation against the
  authoritative product contract rather than merely repeat Development's test
  command or accept Development's verification as proof.
- Consequences: Testing selects and records its own checks. A prebuilt test plan,
  versioned input envelope, and hard parser are not required during the pilot.
- Supersedes: None.
- Follow-up cases: `C-022`.

## `D-026` — Give Testing role-scoped ownership of independent test assets

- Case: `C-022`
- Status: accepted
- Decided: 2026-07-20
- Decision: Testing owns the independent acceptance, integration, end-to-end,
  and regression test cases, scripts, fixtures, and suites that it creates, as
  well as Testing-authored findings and `evidence.md` entries, its verdict, and
  its reference-based handoff. Development retains ownership of the unit and
  implementation-adjacent tests it creates.
- Basis: independent automated checks need a durable owner, while tests coupled
  to implementation details remain part of Development's local verification
  responsibility.
- Consequences: ownership follows the purpose and authoring role of a test, not
  merely its file extension or directory. The pilot does not require separate
  `test-plan.md` or `test-report.md` artifacts.
- Supersedes: None.
- Follow-up cases: `C-023`.

## `D-027` — Restrict Testing writes to its checks and records

- Case: `C-023`
- Status: accepted
- Decided: 2026-07-20
- Decision: Testing may create and correct its own independent test assets and
  append or update only Testing-authored findings, evidence entries, verdict,
  and reference-based handoff. It may repair a faulty check and rerun it, but
  must not edit product code, product proposal or specs, Development-owned tests
  or planning artifacts, other roles' evidence, task completion, or delivery
  status.
- Basis: Testing needs write authority over reproducible independent checks but
  must remain independent from the product implementation it evaluates.
- Consequences: a test correction must preserve the accepted requirement rather
  than weaken the check to match current behavior. Product defects return to
  their owning flow for repair.
- Supersedes: None.
- Follow-up cases: `C-024`.

## `D-028` — Use owner-routed Testing verdicts without waivers

- Case: `C-024`
- Status: superseded
- Decided: 2026-07-20
- Decision: Testing emits `ready-for-review` when all required checks are current
  and successful with no unresolved acceptance-breaking finding,
  `defects-found` for implementation failures, `analysis-required` for a missing,
  contradictory, or untestable product contract, and `blocked` when an external
  condition prevents a valid result.
- Basis: owner-specific outcomes preserve a small vocabulary while identifying
  the next responsible flow more precisely than generic pass or fail.
- Consequences: non-blocking observations accompany the evidence, but Testing
  cannot waive a failed requirement or accept delivery risk. Only
  `ready-for-review` represents a successful Testing exit.
- Supersedes: None.
- Follow-up cases: `C-025`.
- Replaced by: `D-034`.

## `D-029` — Route Testing outcomes directly to the responsible owner

- Case: `C-025`
- Status: superseded
- Decided: 2026-07-20
- Decision: `ready-for-review` advances to Review; `defects-found` returns to
  Development; `analysis-required` returns to Analysis; and `blocked` resumes
  the same Testing flow after its external condition clears. A repair repeats
  affected Testing checks, while a changed product contract passes through
  Development before Testing.
- Basis: direct owner routing avoids unnecessary intermediaries while the
  earliest-invalidated-gate rule prevents repaired work from bypassing affected
  verification.
- Consequences: Testing hands Review the exact tested source identity, current
  evidence, and unresolved non-blocking observations. Affected evidence becomes
  stale after repair; unaffected successful evidence remains current.
- Supersedes: None.
- Follow-up cases: `C-026`.
- Replaced by: `D-039`.

## `D-030` — Start Review from canonical delivery-candidate references

- Case: `C-026`
- Status: superseded
- Decided: 2026-07-20
- Decision: Review starts from references to the selected delivery scope,
  proposal and specs, applicable design, tasks, and plan, exact candidate diff
  or source identity, upstream verdicts, current Development and Testing
  evidence, open observations, and handoff. For Analysis `no-change-required`,
  it instead receives the original intent, Analysis rationale, and supporting
  references, with absent implementation and Testing evidence explicitly
  explained by that verdict.
- Basis: an independent final assessment needs the complete canonical context,
  while a copied review dossier would duplicate state and prematurely harden the
  pilot format.
- Consequences: Review selects its own checks and follows canonical references;
  a diff plus test result alone is insufficient. No hard serialized Review input
  schema is required during the pilot.
- Supersedes: None.
- Follow-up cases: `C-027`.
- Replaced by: `D-032`.

## `D-031` — Give Review ownership only of its independent assessment

- Case: `C-027`
- Status: superseded
- Decided: 2026-07-20
- Decision: Review owns only Review-authored findings and evidence entries, its
  verdict, and its reference-based handoff. It does not own proposal or specs,
  technical artifacts, implementation code, test assets, other roles' evidence,
  or delivery state.
- Basis: the final assessment must remain independent and auditable without
  overwriting upstream facts or duplicating the canonical artifact set.
- Consequences: the pilot introduces no mandatory `review.md` or
  `review-report.md`; Review records are role-scoped entries in existing
  evidence and handoff mechanisms. Final task-completion authority is decided
  separately from artifact ownership.
- Supersedes: None.
- Follow-up cases: `C-028`.
- Replaced by: `D-032`.

## `D-032` — Separate role-internal review from cross-role transition review

- Case: `C-031`
- Status: accepted
- Decided: 2026-07-20
- Decision: use three role flows—Analysis, Development, and Testing. Every role
  flow contains an internal review of its own result before handoff; Development
  includes writing implementation-adjacent tests before that review. A separate
  transition review accepts or rejects the handoff between responsibility
  boundaries and may involve different people. Review is therefore a gate type,
  not a fourth end-to-end role flow. Delivery remains the terminal transition.
- Basis: self-checking work within a role and accepting work from another role
  answer different questions and require different authority.
- Consequences: earlier Analysis, Development, and Testing contracts remain the
  role contracts, but their successful exits now pass through transition review.
  Standalone Review input, ownership, write, verdict, and transition cases are
  retired and replaced by common internal-review and transition-review
  contracts. The minimum skill set will be derived from this corrected model.
- Supersedes: `D-014`, `D-030`, `D-031`.
- Follow-up cases: `C-032`, `C-033`, `C-034`.

## `D-033` — Make the receiving role own transition review

- Case: `C-032`
- Status: accepted
- Decided: 2026-07-20
- Decision: the receiving responsibility owns each cross-role transition review.
  Development accepts the Analysis handoff, Testing accepts the Development
  handoff, and an explicitly named delivery owner accepts the Testing handoff at
  the terminal boundary. The receiver either accepts responsibility or returns
  findings; it does not repair the sender's artifacts during acceptance.
- Basis: internal readiness belongs to the sender, while only the receiver can
  determine whether the supplied contract, artifacts, and evidence are
  sufficient to take responsibility for the next stage.
- Consequences: an accepted handoff transfers responsibility to the receiver. A
  rejected handoff returns to the sender's owning flow, which repairs its work,
  repeats internal review, and offers the handoff again. The terminal boundary
  must name a delivery owner rather than rely on an implicit fourth Review role.
- Supersedes: None.
- Follow-up cases: `C-033`, `C-034`.

## `D-034` — Use people as pilot review gates instead of a status machine

- Case: `C-033`
- Status: accepted
- Decided: 2026-07-20
- Decision: internal and cross-role reviews are explicit human decisions during
  the technology pilot. USW does not enforce `new`/`active`/`blocked` state
  lifecycles, mandatory role-verdict enums, or an automated approval machine. A
  human reviews the current candidate, asks its owning role to repair problems,
  and explicitly permits the handoff when satisfied.
- Basis: the pilot must validate whether the responsibility flow is useful
  before investing in workflow-state infrastructure. People can exercise
  judgment where the contracts are still evolving.
- Consequences: earlier Analysis, Development, and Testing verdict names may be
  used as plain-language routing descriptions but are not required statuses or
  serialized fields. Internal review may be performed by the same person or
  another person acting within the role; transition review remains owned by the
  receiver. The minimum durable trace is decided separately.
- Supersedes: `D-018`, `D-023`, `D-028` as mandatory pilot status systems.
- Follow-up cases: `C-034`, `C-035`.

## `D-035` — Keep pilot review decisions in conversation only

- Case: `C-034`
- Status: superseded
- Decided: 2026-07-20
- Decision: during the pilot, internal and transition review approvals and
  returns are not copied into `handoff.md`, evidence, approval fields, or a new
  review artifact. The people involved communicate the decision and findings in
  the active conversation.
- Basis: the immediate goal is to exercise the responsibility flow with minimal
  process machinery and learn which persistent review information is actually
  needed.
- Consequences: the pilot does not guarantee an audit trail or resumability for
  review decisions across conversations. If real usage exposes that need, the
  team may add the smallest proven record later rather than predesigning it now.
- Supersedes: None.
- Follow-up cases: `C-035`.
- Replaced by: `D-043`.

## `D-036` — Treat tasks.md as the coding agent's completion journal

- Case: `C-035`
- Status: accepted
- Decided: 2026-07-20
- Decision: Development owns technical design, task indexes and contracts,
  executable plans, implementation code, implementation-adjacent tests, plan
  progress, Development evidence and handoff, and its task checkboxes. A coding
  agent checks its task in `tasks.md` after satisfying the linked `task.md`
  definition of done, completing its plan, and passing required local checks.
  The checkbox does not represent later human review, Testing acceptance, or
  Delivery.
- Basis: `tasks.md` is a journal of executable coding work and must be useful to
  the coding agent without depending on a person who may join only after the
  implementation flow has finished.
- Consequences: human reviewers inspect an already completed coding result and
  communicate acceptance or findings in conversation. Development still cannot
  edit product proposal/specs, independent Testing artifacts or records, or
  claim terminal Delivery. How blocking human findings affect an already checked
  task is decided separately.
- Supersedes: `D-022`.
- Follow-up cases: `C-036`.

## `D-038` — Reopen coding tasks for findings within their original contract

- Case: `C-036`
- Status: accepted
- Decided: 2026-07-20
- Decision: when human review shows that an already checked coding task does not
  satisfy its original `task.md` result, scope, or definition of done, the coding
  agent changes `[x]` back to `[ ]`, repairs the task, reruns the required checks,
  and checks it again. A suggestion that adds independent scope becomes a new
  proposed task only after user approval.
- Basis: `tasks.md` is the coding agent's current journal and must remain truthful
  without turning every correction into a new task or hiding incomplete original
  work behind a checked box.
- Consequences: the pilot uses Git history for chronology and adds no reopen
  status or review record. Blocking in-scope findings reopen the same task;
  independent improvements follow normal scope-selection authority.
- Supersedes: None.
- Follow-up cases: None.

## `D-039` — Route handoffs through receiving-role transition review

- Case: `C-037`
- Status: accepted
- Decided: 2026-07-20
- Decision: preserve direct routing to the owner of the affected canonical
  artifact and replace the former standalone Review destination with the
  applicable receiving-role transition review. Development accepts an Analysis
  change handoff, Testing accepts a Development handoff, and the named delivery
  owner accepts a successful Testing handoff. An Analysis `no-change-required`
  result goes directly to the named delivery owner's transition review. A
  rejection returns findings to the sender or affected artifact owner; after
  repair, the lifecycle resumes at the earliest gate invalidated by the change.
- Basis: receiving-role gates preserve independent acceptance of responsibility
  without restoring Review as a fourth role or weakening owner-routed repair.
- Consequences: flow scenarios share one routing invariant; earlier verdict
  names remain optional plain-language descriptions rather than serialized
  states. Repair keeps unaffected evidence current and repeats every affected
  internal or transition gate.
- Supersedes: `D-019`, `D-024`, `D-029`.
- Follow-up cases: `C-038`, `C-040`.

## `D-040` — Split the OpenSpec frontier between Analysis and Development

- Case: `C-038`
- Status: accepted
- Decided: 2026-07-20
- Decision: under the OpenSpec `spec-driven` provider, Analysis completes
  `proposal` and capability `specs`, then may offer its handoff while the
  aggregate change remains incomplete, `design` is ready, and `tasks` is
  blocked. Development accepts that handoff, creates the technical `design`,
  and then creates `tasks` when the native artifact graph makes it ready.
  Role-oriented flows request artifact instructions individually and do not use
  bundled `openspec-propose` across the Analysis–Development boundary.
- Basis: `specs` and `design` independently follow `proposal`, while `tasks`
  depends on both. The native graph therefore supports the accepted ownership
  split without provisional artifacts or a custom schema.
- Consequences: Analysis never writes technical design merely to advance the
  provider state; Development owns both implementation approach and executable
  task decomposition. Native OpenSpec convenience flows remain available only
  outside USW's role-oriented scenarios.
- Supersedes: `D-037`.
- Follow-up cases: `C-039`.

## `D-041` — Use three role scenarios with capability-oriented atomic skills

- Case: `C-039`
- Status: accepted
- Decided: 2026-07-20
- Decision: define exactly three initial role scenarios—Analysis, Development,
  and Testing—and coordinate them through one `usw-run-flow` orchestrator.
  Reuse `usw-brainstorm-solutions`, `usw-refine-task`,
  `usw-plan-small-steps`, and `usw-manage-handoff` as atomic lifecycle
  capabilities. Add only the missing provider-aware artifact-management,
  bounded task-execution, and independent verification/evidence capabilities.
  Internal and transition review remain declared human gate actions inside
  scenarios during the pilot rather than standalone skills or a fourth flow.
- Basis: capability-oriented skills remain reusable and independently testable
  while scenarios retain visible authority over order, branching, gates, and
  stopping behavior.
- Consequences: `usw-initialize-project` and `usw-explain-me` remain utility
  entrypoints outside the role lifecycle. A lifecycle stage does not receive a
  dedicated skill unless implementation proves that it is an independently
  reusable capability.
- Supersedes: None.
- Follow-up cases: `C-040`.

## `D-042` — Use a per-run terminal Delivery contract

- Case: `C-040`
- Status: accepted
- Decided: 2026-07-20
- Decision: before the terminal transition, identify the selected delivery
  scope, exact tested source, current evidence, unresolved non-blocking
  observations, and delivery owner for that run. The user is the delivery owner
  by default and may explicitly delegate the responsibility. Delivery acceptance
  confirms the named candidate and transfer of responsibility only; commit,
  push, pull request, deployment, release, and other external actions each
  require their own explicit authorization.
- Basis: terminal acceptance and permission to mutate external state are
  different authorities and must not be inferred from one another.
- Consequences: Testing success alone does not claim Delivery. A flow without an
  accepted terminal handoff stops with the candidate and evidence ready for the
  named owner; project-wide delivery policy remains deferred until pilot usage
  demonstrates a stable need.
- Supersedes: None.
- Follow-up cases: `C-041`.

## `D-043` — Persist immutable reviewer-owned receipts

- Case: `C-041`
- Status: accepted
- Decided: 2026-07-20
- Decision: every human internal-review and transition-review attempt creates a
  new shared reviewer-owned `reviews/<review-id>.md` receipt. The receipt records
  the gate, reviewed scope and exact source or artifact identity, reviewer,
  verdict, finding references, evidence references, and timestamp without
  copying canonical content. A repeated review creates another receipt rather
  than rewriting the earlier result; the applicable handoff references the
  current accepted receipt.
- Basis: a durable reviewer artifact preserves resumability, transfer, and audit
  context without mixing independent review authority into implementation
  evidence or handoff prose.
- Consequences: review remains a human gate rather than a fourth role or an
  automated approval state machine, but its result is no longer confined to one
  conversation. The configured storage location and provider mapping for the
  review collection require a follow-up decision because Analysis review may
  occur before a task directory exists.
- Supersedes: `D-035`.
- Follow-up cases: `C-042`.

## `D-044` — Store review receipts in a provider-neutral shared collection

- Case: `C-042`
- Status: accepted
- Decided: 2026-07-20
- Decision: store reviewer receipts under a configured provider-neutral shared
  review root, defaulting to `usw/reviews/<subject-id>/<review-id>.md`. Each
  receipt identifies and references its reviewed refinement, standalone change,
  OpenSpec change, task, source, and evidence as applicable without copying or
  modifying those canonical artifacts.
- Basis: one shared collection is discoverable before task creation and works
  for both standalone and OpenSpec-backed subjects without extending the
  third-party OpenSpec artifact tree.
- Consequences: review receipts remain USW-owned shared state even when OpenSpec
  supplies planning artifacts. Subject identifiers must be stable and
  collision-free, and configuration validation must keep the review root inside
  the project under the same safe-path rules as other shared roots.
- Supersedes: None.
- Follow-up cases: None.
