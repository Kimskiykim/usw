## Why

Three problems in the same text, which is why they are one change rather than
three: fixing them separately means rewriting the same paragraphs three times.

**The instructions are dense.** `usw-assess-flow` is 218 lines, `usw-create-flow`
202, `usw-manage-handoff` 186, and nearly every sentence carries MUST weight with
no hierarchy of importance. The executor is a model, and Qwen-class models — a
declared target — follow dense normative prose worse than short imperatives.

**The tests pin the wording.** `tests/test_atomic_skill_contracts.py` asserts
literal Russian phrases inside those files, for example
`assertIn("несколько routes без selector", manage)`. Any attempt to say the same
thing more briefly fails a test even when the meaning is preserved, so the test
design actively defends the density. These two problems must be fixed together
or not at all.

**The same rules live in three places** — `README.md`, `openspec/specs/*` and
`skills/*/SKILL.md` — so they drift, and drift is hardest to spot exactly where
it matters most, in the file the executor reads.

**And the layer mixes languages.** Bodies are mostly Russian, but
`usw-initialize-project` is entirely English and English terms sit inside Russian
sentences. Mixing costs instruction-following quality regardless of which
language is chosen.

Behavior evaluation now exists, so meaning-level invariants can be checked by
measurement instead of by asserting that a sentence is present.

## What Changes

- Make `openspec/specs/` the single normative source; reduce README to an
  overview that links to it, and keep skills derived and minimal.
- Restructure each skill: imperatives first, with rationale, edge cases and
  recipes moved into `references/` read on demand.
- Replace phrase-level contract tests with anchors that are actually stable —
  command names, error codes, file paths — and move meaning-level invariants to
  behavior scenarios.
- Make the normative layer consistently Russian, translating the one skill
  written in English. Frontmatter `description` fields stay as they are: they are
  harness metadata used to select a skill, not normative body, and changing them
  would alter triggering in a way this change cannot measure.
- Add behavior scenarios covering each invariant that a substring test currently
  stands in for, before that test is removed.

## Capabilities

### Modified Capabilities

- `flow-behavior-evaluation`: Scenarios become the mechanism that protects
  meaning-level invariants when phrase-level assertions are withdrawn.

## Impact

- All six shipped `skills/*/SKILL.md` and their `references/`.
- `tests/test_atomic_skill_contracts.py` and the phrase assertions in
  `tests/test_platform_support.py` and `tests/test_package_layout.py`.
- `README.md` and `openspec/specs/*`.
- `evals/scenarios/`, which gains scenarios before assertions are removed.
- No change to any runtime behavior, permission boundary, or file format.

## Non-Goals

- Changing what any skill does. This change moves and rewrites text; a behavior
  difference found during it is a defect, not an improvement.
- Changing the project's language. Russian is the author's decision; this change
  only makes it consistent.
- Touching frontmatter `description` fields, which drive skill selection.
- Removing every substring assertion. Names, codes and paths are stable anchors
  and stay asserted.
