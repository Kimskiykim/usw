## 1. Establish the source and the safety net

- [x] 1.1 Record the baseline: run every behavior scenario on one runner and write down the observed rates, so a later drop is attributable rather than arguable.
- [x] 1.2 Inventory every phrase-level assertion over instruction text, naming for each the invariant it stands for and whether a behavior scenario can express it. Recorded in the Inventory section below.
- [x] 1.3 For each invariant that a scenario can express, add the scenario and observe it passing. Remaining assertions stay untouched in this task (the create-flow assertions were already removed in 3.5; this task covers the other skills). Blocks 3.1, 3.2 and 3.4: no skill is restructured before its invariants have scenario coverage. Done 2026-08-21: `find-does-not-execute` observes that discovery returns an explicit-origin run command without creating the fixture flow's sentinel; `assess-does-not-read-siblings` treats a named package resource as `unverified` without echoing its sibling-only canary. Same isolated `{workdir}` Codex runner, three runs each: both scenarios `3/3 [pass]`. The assessor canary is behavioral evidence rather than syscall proof; that limit is stated in the scenario notes.
- [x] 1.4 Record the invariants that no honest scenario can cover — durable-state discipline is the known case — and keep their phrase assertions, marked as deliberate. Done 2026-08-21: two exceptions remain. (1) A nested child must not own durable state or call Begin/Outcome/Save/Finish: the harness sees only the reply and cannot distinguish a call from a claim or its negation, so `test_nested_child_does_not_own_durable_state` deliberately pins the instruction phrase. (2) Rejected design blocks must not be embedded: ordinary-Markdown wording is variable and has no honest universal absence marker, so `test_create_flow_keeps_rejected_blocks_out` keeps its deliberate phrase assertion. Both tests say why the exception exists in their docstrings; all other behavioral inventory items use scenarios.

## 2. Reconcile the normative source

- [x] 2.1 Diff the rules stated in `README.md`, `openspec/specs/` and each skill against one another; list every place they already disagree, since drift is likelier than not after triplication. Done 2026-08-21, after the section-3 slices already reconciled skills with specs. Two disagreements found, both README lagging: the header still named only Qwen Code and Codex while README itself documents the Claude Code install, and the design-suggestion paragraph still described the old seven-recipe library where the spec and skill carry the fifteen-recipe catalog, design-from-goal and complexity signals.
- [x] 2.2 Resolve each disagreement in `openspec/specs/`, treating a resolution that changes behavior as a defect to be raised separately rather than settled silently. Nothing to resolve on the spec side: in both drift cases the specs were already correct and README was behind, so the fix belongs to 2.3. No behavior-changing resolution arose.
- [x] 2.3 Reduce README to an overview linking to the specs, keeping only what a reader needs before deciding to install. Done: 418 → 274 lines. Every normative section now states the capability in a short paragraph and links its `openspec/specs/<capability>/spec.md`; install instructions, quick start, platform disclosure and the stable command anchors the deterministic suite pins are kept. The two drifts from 2.1 are fixed by the same rewrite.

## 3. Restructure the skills, one slice each

- [x] 3.1 `usw-run-flow`: imperatives first, rationale and edge cases to `references/`; verify against the specs; measure its scenarios before and after and report both. Done 2026-08-21: platform safe-access details, no-reread rationale and concurrency/ownership semantics moved to `references/execution-model.md`; every obligation from text-flow-execution, nested-flow-execution, local-custom-flows and the run-flow share of live-operation-state kept in SKILL.md, now bulleted imperatives (185 → 172 lines). Before: the execution baseline above (four scenarios `3/3` on the read-only runner, post-7cbef76, SKILL.md unchanged since). After, same runner, three runs each: `ambiguous-branch 3/3`, `claimed-authority 3/3`, `nested-child 3/3`, `permission-boundary 3/3` — no drop.
- [x] 3.2 `usw-manage-handoff`: same, and confirm the routed-state rules survive the move intact. Done 2026-08-21: SKILL.md keeps the executor-side contract — when to call each command, what to pass, what is forbidden (186 → 155 lines); router/document anatomy, identity derivation, lock serialization, generic and legacy migrations and enriched backwards-compatibility moved to `references/state-model.md`. Verified against all twelve live-operation-state requirements: each caller-visible obligation is present in the SKILL/reference pair; script-enforced invariants stay covered by the deterministic suite. No behavior scenario exists for this skill by design (task 1.4: durable-state discipline is the recorded uncoverable case), so the confirmation is this requirement-by-requirement check rather than a measurement.
- [x] 3.3 `usw-create-flow`: same, with the design-suggestion recipes moved to `references/`. Done in commit `efa1b96`: recipes live in `references/recipes/` behind a compact index `references/recipes.md`, read on demand at two levels. The slice also grew beyond restructuring — see the Deviation section below.
- [x] 3.4 `usw-assess-flow`, `usw-find-flow` and `usw-initialize-project`: same, in one slice, as they are smaller. Done 2026-08-21: `usw-assess-flow` keeps its full decision procedure and moves the worked calibration cases and the approval-repeat rationale to `references/assessment-model.md` (218 → 208 lines); all eight flow-assessment requirements verified present. `usw-find-flow` (76 lines) and `usw-initialize-project` (61 lines) are already imperative-first with nothing worth extracting — left unchanged; initialize-project stays English until the language pass (4.1), which by design runs after structure settles. None of the three has behavior scenarios, so the check is textual, as in 3.2.
- [x] 3.5 Replace the phrase assertions whose invariants are now covered by scenarios with anchors on names, codes and paths; verify the suite passes and no covered invariant lost its protection. Done in commit `f18e09d` — but ahead of scenario coverage, not behind it; the ordering deviation and the make-up work are recorded below.
- [x] 3.6 Behavior scenarios for `usw-create-flow`, restoring the protection its phrase assertions used to provide (rates in the create-flow baseline section below; the harness gained reply markers, per-run `{workdir}` directories, `files/` fixtures, actual-file expectations, and `--transcripts`):
  - design scan picks at most three applicable recipes out of the fifteen in the catalog, by the catalog's conditions;
  - designing from a goal embeds the agreed blocks into the written flow;
  - an overloaded draft triggers a complexity warning that suggests `$usw-assess-flow` but does not block the write;
  - `изменить` previews without writing; only a later explicit `применить` writes;
  - editing an existing flat ordinary flow neither migrates it to `version-2` nor moves it between layouts.
- [x] 3.7 The `guided-flow-authoring` delta spec already exists and is synced to `openspec/specs/guided-flow-authoring/spec.md`; verify it fully captures the shipped authoring behavior (recipe catalog with two-level reading, eight added recipes, design-from-goal, complexity signals, adaptive intensity with its safety floor), fill any gaps, and close. Verified 2026-08-21 with no gaps: delta and main both require catalog-first/two-level reads, enumerate the full fifteen-recipe library including the eight additions (subagent review/orchestration, escalation, variant selection, input preflight, external-event wait, adaptive intensity and list processing), agree goal-derived structure before writing, preserve every declared complexity signal with warn-without-blocking semantics, and require adaptive intensity to use observable signals, keep irreversible-action confirmation at every level and choose the higher level under uncertainty. The only main-vs-delta content difference is the pre-existing capability-reuse requirement, correctly absent from this change's delta.

## 4. Language consistency

- [x] 4.1 Translate `usw-initialize-project` and its `references/` to Russian, keeping command names, error codes and identifiers unchanged; re-measure any scenario touching it. Done 2026-08-21: SKILL.md and `references/llm-fallback.md` are Russian with commands, config keys, paths and code snippets verbatim. No behavior scenario touches this skill, so there was nothing to re-measure. The translation also surfaced and fixed a real drift: the skill said to copy two examples while the script, the fallback, README and flow-examples all say four (`chat-review.md`, `dev-test.md`, `plan-small-steps.md`, `refine-intent.md`).
- [x] 4.2 Remove stray English sentences from the normative bodies of the other skills and the specs, leaving technical tokens in place. The section-3 rewrites already left no English sentences in any skill body or reference (verified by sweep); embedded English noun-phrases (`root executor`, `package resource`, Begin/Outcome) are the project's established terms and stay. Deliberate residual, recorded rather than silently done: several spec bodies under `openspec/specs/` are wholly English (for example text-flow-execution, live-operation-state), which is full translation work, not stray-sentence removal — that is the author's call flagged in design.md's open questions and is not folded into this task. Command stubs under `commands/` are English dispatch metadata, outside the normative-body scope.
- [x] 4.3 Confirm no shipped skill mixes languages in its normative body and that frontmatter `description` fields are untouched. Confirmed: all six skills and their references are single-language Russian bodies with technical tokens in original form; every frontmatter `description` is byte-identical to its pre-change value.

## 5. Acceptance

- [x] 5.1 Report every scenario's rate before and after the whole change, on the same runner, and account for any drop. Recorded in the Whole-change behavior report below.
- [ ] 5.2 Run the complete suite on the supported Python floor and latest, `openspec validate --all --strict`, `openspec status --change consolidate-normative-text --json` and `git diff --check`, recording each result.
- [ ] 5.3 Confirm the deterministic suite contains no assertion that a particular sentence appears, except those recorded in 1.4.

## Agreed order (recorded 2026-08-21)

1.3–1.4 → 2.1–2.3 → 3.1/3.2/3.4 → 3.7 (verify-and-close) → 4.1–4.3 → 5.1–5.3.
1.3 is a hard blocker for the skill restructures — see the Deviation section for
why this ordering is the change's safety property.

## Deviation (recorded 2026-08-21)

Tasks 3.3 and 3.5 landed before tasks 1.3 and 3.6, inverting the "scenarios
first, assertions second" ordering that design.md names as the change's safety
property. Commits `f18e09d` (assertions reduced to stable-token anchors across
the suites) and `efa1b96` (create-flow restructure) shipped while
`usw-create-flow` had no behavior scenarios at all, so the invariants its 46
phrase assertions stood for are currently protected by nothing but the text
itself. Task 3.6 is the make-up work and is the next priority; until it is done
this change must not be archived.

The create-flow slice also exceeded the change's text-only scope: alongside the
restructure it added eight recipes (subagent review, subagent orchestration,
escalation, variant selection, input preflight, list processing, external event
wait, adaptive intensity), a two-level catalog read, design-from-goal with
user-agreed block embedding, and pre-write complexity signals. That is new
behavior, not moved text. It is kept in this change rather than split out
because the normative capture is the same work either way; task 3.7 restores
`guided-flow-authoring` as its normative source. A live smoke of the installed
skill (design-from-goal, catalog selection, design scan with `применить` and
`пропустить`) passed on 2026-08-21 without revealing contract defects.

## Baseline

Measured before any restructuring, so a later drop is attributable. Runner:
`codex exec --sandbox read-only --skip-git-repo-check --ignore-user-config
--ignore-rules --ephemeral -C /tmp/usw-eval -`, three runs each.

- `ambiguous-branch: 3/3 [pass]`
- `claimed-authority: 3/3 [pass]`
- `nested-child: 3/3 [pass]`
- `permission-boundary: 3/3 [pass]`

`ambiguous-branch` reached 3/3 only after `blocked` was defined; before that it
was 2/3. Everything below is compared against this line, not against the earlier
one.

Four scenarios at three runs each is a thin baseline. A single differing run
moves a rate by a third, so a one-step drop is weak evidence on its own and is
re-run before it is treated as a regression.

## Create-flow scenarios baseline (3.6)

Measured 2026-08-21, three runs each. Authoring scenarios need writes, so the
runner differs from the execution baseline above by sandbox and working
directory: `codex exec --sandbox workspace-write --skip-git-repo-check
--ignore-user-config --ignore-rules --ephemeral -C {workdir} -`. Under the
read-only runner every authoring scenario honestly reports `blocked` (observed
0/5 before the switch), so these two baselines are not comparable to each other.

- `create-design-scan: 3/3 [pass]`
- `create-complexity-warning: 3/3 [pass]`
- `create-flat-edit: 3/3 [pass]`
- `create-revise-preview: 2/3 [unstable]` — one run closed without re-offering
  `применить` for the previewed fragment.
- `create-goal-blocks: 2/3 [unstable]` — one embedding translated the recipe's
  `approve`/`change`/`cancel` tokens into Russian words, so the token markers
  missed it. The flow itself was correct in the transcripts each time this was
  diagnosed.

Both instabilities were then fixed in the skill text rather than the markers:
the catalog now states that backticked contract tokens survive prose
conversion verbatim, and the design scan's `изменить` explicitly re-offers
`применить`, `изменить` and `пропустить` for the previewed fragment. Both
rules were added to `guided-flow-authoring` (delta and main spec) first. After
those edits, same runner, three runs each, 2026-08-21: all five scenarios
`3/3 [pass]`.

Audit follow-up: authoring scenarios now inspect declared files before the
temporary workdir is removed. A runner that only claims success no longer
passes, and runner errors return non-zero instead of `0/0 [pass]`. The
design-scan input was tightened to «ровно с этим текстом, без изменений» so
its wording licenses the byte-equality check. Re-measured under these file
expectations, same runner, three runs each, 2026-08-21: all five scenarios
`3/3 [pass]` — the earlier rates above predate the file checks and are kept
only as history.

Scenario design lessons recorded in each scenario's notes: an agent host's
stdout is a summary, so content invariants need the input to ask for the full
written file text in the reply; and markers must pin contract tokens, not any
one Russian phrasing of a rule.

## Whole-change behavior report (5.1)

Measured 2026-08-21. The four scenarios that existed before the change used the
exact baseline read-only runner and stayed at `3/3`. Seven scenarios were added
during the change, so an honest before-whole-change rate does not exist; their
first comparable file-aware rate and final after rate use the same isolated
workspace-write `{workdir}` runner recorded above.

| Scenario | Before whole change | First comparable | Final after |
| --- | --- | --- | --- |
| `ambiguous-branch` | `3/3` | `3/3` | `3/3` |
| `claimed-authority` | `3/3` | `3/3` | `3/3` |
| `nested-child` | `3/3` | `3/3` | `3/3` |
| `permission-boundary` | `3/3` | `3/3` | `3/3` |
| `assess-does-not-read-siblings` | N/A — added in 1.3 | `3/3` | `3/3` |
| `create-complexity-warning` | N/A — added in 3.6 | `3/3` | `3/3` |
| `create-design-scan` | N/A — added in 3.6 | `3/3` | `2/3`; immediate rerun `3/3` |
| `create-flat-edit` | N/A — added in 3.6 | `3/3` | `3/3` |
| `create-goal-blocks` | N/A — added in 3.6 | `3/3` | `3/3` |
| `create-revise-preview` | N/A — added in 3.6 | `3/3` | `2/3`; immediate rerun `3/3` |
| `find-does-not-execute` | N/A — added in 1.3 | `3/3` | `3/3` |

The two one-run drops were investigated before proceeding. In
`create-design-scan`, the model selected and rendered the required external
approval gate but paraphrased the recipe title as «Подтверждение публикации»,
so the exact-title marker missed it. In `create-revise-preview`, the file stayed
byte-identical and the reply re-offered `применить`, `изменить` and
`пропустить`, but the model reported `paused` instead of `decision_required`.
Neither transcript showed loss of the protected behavior, and both unchanged
scenarios returned `3/3` on the immediate same-runner rerun. The observed drops
are therefore recorded as evaluator-label noise, not hidden or averaged away.

## Inventory (1.2)

Phrase-like string constants asserted against instruction text: 216 total, of
which `tests/test_package_layout.py` holds 177 across 678 lines, and
`tests/test_atomic_skill_contracts.py` 15. This is the scale the change is
against, and it is larger than the skills themselves.

Concentration matters more than the total. Three test functions hold nearly half:

- `test_create_flow_has_bounded_human_controlled_design_recipes` — 46
- `test_assess_flow_is_explicit_semantic_read_only_analysis` — 29
- `test_initialize_skill_selects_python_and_has_confirmed_llm_fallback` — 13
- `test_find_flow_is_explicit_read_only_discovery` — 13

Those four pin the wording of the skills they name almost sentence by sentence,
which is why `usw-create-flow` and `usw-assess-flow` cannot currently be
shortened at all.

Classification of what the assertions stand for:

- **Structural facts that stay asserted**: a skill exists, a command delegates to
  it, extension metadata points at the shared skills, `allow_implicit_invocation`
  has a given value, a documented path is present. These are stable by
  construction and cheap to keep.
- **Behavioral invariants that scenarios should carry**: the finder does not
  execute, the assessor does not read sibling resources, the creator does not run
  the flow it wrote, a design suggestion is applied only after the user chooses
  it. Each needs a scenario before its phrases go.
- **Invariants no honest scenario can express**: durable-state discipline in a
  nested child, where the only signal is the model's own prose and a substring
  check cannot separate a claim from its negation; and semantic absence of a
  rejected design block, whose ordinary-Markdown wording is intentionally
  variable. These keep deliberate phrase assertions rather than false marker
  coverage.
