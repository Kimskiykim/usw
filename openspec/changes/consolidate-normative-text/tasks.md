## 1. Establish the source and the safety net

- [x] 1.1 Record the baseline: run every behavior scenario on one runner and write down the observed rates, so a later drop is attributable rather than arguable.
- [ ] 1.2 Inventory every phrase-level assertion over instruction text, naming for each the invariant it stands for and whether a behavior scenario can express it.
- [ ] 1.3 For each invariant that a scenario can express, add the scenario and observe it passing. Assertions stay untouched in this task.
- [ ] 1.4 Record the invariants that no honest scenario can cover — durable-state discipline is the known case — and keep their phrase assertions, marked as deliberate.

## 2. Reconcile the normative source

- [ ] 2.1 Diff the rules stated in `README.md`, `openspec/specs/` and each skill against one another; list every place they already disagree, since drift is likelier than not after triplication.
- [ ] 2.2 Resolve each disagreement in `openspec/specs/`, treating a resolution that changes behavior as a defect to be raised separately rather than settled silently.
- [ ] 2.3 Reduce README to an overview linking to the specs, keeping only what a reader needs before deciding to install.

## 3. Restructure the skills, one slice each

- [ ] 3.1 `usw-run-flow`: imperatives first, rationale and edge cases to `references/`; verify against the specs; measure its scenarios before and after and report both.
- [ ] 3.2 `usw-manage-handoff`: same, and confirm the routed-state rules survive the move intact.
- [ ] 3.3 `usw-create-flow`: same, with the design-suggestion recipes moved to `references/`.
- [ ] 3.4 `usw-assess-flow`, `usw-find-flow` and `usw-initialize-project`: same, in one slice, as they are smaller.
- [ ] 3.5 Replace the phrase assertions whose invariants are now covered by scenarios with anchors on names, codes and paths; verify the suite passes and no covered invariant lost its protection.

## 4. Language consistency

- [ ] 4.1 Translate `usw-initialize-project` and its `references/` to Russian, keeping command names, error codes and identifiers unchanged; re-measure any scenario touching it.
- [ ] 4.2 Remove stray English sentences from the normative bodies of the other skills and the specs, leaving technical tokens in place.
- [ ] 4.3 Confirm no shipped skill mixes languages in its normative body and that frontmatter `description` fields are untouched.

## 5. Acceptance

- [ ] 5.1 Report every scenario's rate before and after the whole change, on the same runner, and account for any drop.
- [ ] 5.2 Run the complete suite on the supported Python floor and latest, `openspec validate --all --strict`, `openspec status --change consolidate-normative-text --json` and `git diff --check`, recording each result.
- [ ] 5.3 Confirm the deterministic suite contains no assertion that a particular sentence appears, except those recorded in 1.4.

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
  check cannot separate a claim from its negation. These keep their assertions,
  recorded here as deliberate rather than overlooked.
