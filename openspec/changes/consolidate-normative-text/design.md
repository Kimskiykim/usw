## Context

The same paragraphs carry three defects, which is why this is one change: fixing
them separately means rewriting the same text three times.

Density: six shipped skills, 2820 lines of normative text across skills, README
and specs. `usw-assess-flow` is 218 lines, `usw-create-flow` 202,
`usw-manage-handoff` 186, with almost every sentence carrying MUST weight and no
signal of what matters most.

Pinned wording: `tests/test_atomic_skill_contracts.py` asserts literal sentences
inside those files. Rewriting an instruction more clearly fails a test even when
the meaning is unchanged. The test design defends the density.

Triplication: README, `openspec/specs/` and the skills each state the same rules.
Drift is invisible precisely where it hurts most — in the file the executor reads.

Mixed language: one entirely English skill among Russian ones, and English terms
inside Russian sentences.

What changed recently and makes this tractable: behavior evaluation exists. An
invariant can now be protected by measuring whether a model observes it, instead
of by asserting that a sentence describing it is present.

## Goals / Non-Goals

**Goals:**

- One normative source, with skills derived from it.
- Skills that lead with the imperative.
- Tests that pin stable anchors, with meaning covered by scenarios.
- One language in the normative layer, consistently.
- No behavior change.

**Non-Goals:**

- Changing what any skill does. *(Breached once, deliberately: the create-flow
  slice shipped new authoring behavior alongside the restructure — see the
  Deviation notes here and in tasks.md; task 3.7 gives that behavior a
  normative home in `guided-flow-authoring`.)*
- Choosing the project's language. Russian is decided; this change only makes it
  consistent.
- Removing every substring assertion.

## Decisions

### Scenarios first, assertions second

No phrase assertion is removed until a behavior scenario covers the invariant it
stood for. This ordering is the safety property of the whole change: it is the
difference between replacing a weak check with a real one and simply deleting a
check. It also front-loads the work that can fail — writing a scenario may reveal
that an invariant was never actually testable.

*Deviation, recorded 2026-08-21:* the create-flow slice inverted this ordering —
its phrase assertions were reduced to stable-token anchors together with the
restructure, before any create-flow scenario existed. The debt is explicit:
tasks.md 3.6 lists the scenarios that restore coverage, and the change is not
archivable until they exist. The ordering rule stands for every remaining slice.

### Specs are the source, skills are derived

Alternatives considered. Making the skill the source was rejected: skills are
addressed to an executor, so they must be able to omit and simplify, which is
exactly what a normative source must not do. Making README the source was
rejected for the same reason plus its audience. Specs already carry scenarios and
are validated by tooling.

### One skill at a time, measured on both sides

Each skill is restructured as its own slice with its scenarios measured before
and after. A rate that drops stops the slice. Rewriting all six and then
measuring would leave no way to attribute a regression.

### Russian throughout, and frontmatter left alone

The language is the author's call and it is Russian. What this change fixes is
not the choice but the inconsistency: one skill is written in English while the
rest are Russian, and English terms are scattered through Russian sentences.
Mixing costs instruction-following quality whichever language wins.

Command names, error codes and identifiers keep their original form. They are
tokens the runner and the user both type; translating them would break the thing
the sentence is about.

Frontmatter `description` fields stay untouched. They are harness metadata used
to decide when a skill triggers, not normative body, and changing them would
alter selection behavior that this change has no way to measure. Excluding them
keeps a text change from silently becoming a behavior change.

## Risks / Trade-offs

- **A rewrite silently drops a rule.** → Specs are the source and change first;
  each skill is then checked against them rather than against memory.
- **Scenarios cannot cover some invariants**, particularly ones about not writing
  durable state, where the only signal is the model's own prose. → Where no
  honest scenario exists, the phrase assertion stays and the gap is recorded
  rather than papered over.
- **Measurement is noisy**: rates come from a handful of runs, so a small drop
  may be chance. → Compare on the same runner, re-run before concluding, and
  record observed rates rather than verdicts.
- **Scope is large enough to stall.** → Slices are independently shippable; the
  change is useful even if it stops after two skills.
- **Translation changes meaning by accident.** → Language moves last, per skill,
  after that skill's structure is settled and its scenarios pass.

## Migration Plan

Nothing to migrate: no format, path, command or behavior changes. Users see
clearer instructions. Rollback is reverting the text.

## Open Questions

- Whether every invariant currently pinned by a phrase can be expressed as a
  scenario is unknown until each is attempted; the answer decides how many
  assertions actually go away.
- Whether Russian README plus English skills is the right split for this
  project's audience is the author's call, not a technical one.
