## Context

USW's runtime guarantees are produced by a model reading `SKILL.md` and acting on
it. The repository verifies the filesystem boundary thoroughly and the model
boundary not at all. The nearest thing to model-facing verification,
`tests/test_atomic_skill_contracts.py`, asserts that particular sentences appear
in the instruction files, for example `assertIn("несколько routes без selector",
manage)`. That is a check on wording: it passes when the sentence is present and
fails when the sentence is rephrased, regardless of whether any model behaves
correctly in either case. It therefore also raises the cost of the instruction
simplification the project needs.

Constraints this design must respect:

- The repository is standard-library only, with no runtime dependency and no
  credential handling anywhere in it.
- The deterministic suite is fast, offline and reproducible, and CI was just
  built on that property. Evaluation is none of those things.
- USW is executed by third-party hosts (Qwen Code, Codex), not by this
  repository, so the true execution environment is not reproducible here.
- The project's stated character is honesty about non-guarantees. A harness that
  overstated its results would damage the thing it is meant to protect.

## Goals / Non-Goals

**Goals:**

- Produce evidence about instruction compliance where today there is none.
- Measure the invariants instructions exist to enforce: permission boundaries,
  ambiguity stops, nested-child state discipline, status vocabulary, and refusal
  to honour authority claimed by flow text or user input.
- Report observed rates over repeated runs, since a single sample from a
  stochastic system is not a measurement.
- Stay dependency-free, credential-free, and provider-agnostic.
- Keep the deterministic suite and required CI exactly as fast and reliable as
  they are now.
- Make the harness itself deterministically testable.

**Non-Goals:**

- Not a gate. No release, merge or claim depends on an evaluation result.
- Not a guarantee, proof or certification, and not a substitute for the
  permission boundaries enforced by the host.
- Not a model benchmark or a comparison between providers.
- Not a reproduction of a real host environment; see the fidelity risk below.
- Not a judge-model harness in this change.

## Decisions

### Model access is an external command, not an SDK

The harness invokes a command supplied by the developer through
`USW_EVAL_RUNNER`, writes the prompt to its stdin and reads its stdout. The
repository never learns a provider, endpoint, model name or key.

Alternatives considered. Embedding a provider SDK was rejected: it introduces the
first runtime dependency, puts credential handling into a repository that has
none, and hard-codes one vendor into a tool meant to outlive vendors. Driving
`qwen` or `codex` headlessly is the most faithful option and is *not* excluded by
this decision — such a wrapper is simply one possible value of `USW_EVAL_RUNNER`
— but making it the only supported path in this change would tie the harness to
two CLIs, their authentication, and their release cadence before the harness has
proven useful.

### Absent configuration skips, and never fails

With no runner configured the harness reports every scenario as skipped and exits
zero. A tool that fails when unconfigured trains people to ignore it, and it
would make the harness unusable from an ordinary clone.

### The scenario is a directory of plain files

Each scenario is `evals/scenarios/<name>/` holding the instruction files under
test, `flow.md`, `input.txt` and `expect.json`. JSON is used for expectations
because it is unambiguous and in the standard library; the flow and input stay in
their natural formats so a scenario reads like the situation it describes.

Alternative considered: a single Markdown file per scenario with labelled
sections. Rejected because it would require a parser for test data in a project
that deliberately removed its parser, for no gain over separate files.

### Expectations are evaluated deterministically, with a required result line

The prompt asks the model to end with one machine-readable line reporting the
terminal status it reached and whether it performed an external action. The
harness asserts on that line and on the surrounding text; it does not ask a model
to judge another model.

This is the design's sharpest trade-off and is recorded honestly: requiring the
line changes the task slightly from what a real host asks. It is accepted because
the line requests a *report* of what the model did rather than any change in what
it does, and because the alternative — a judge model — would add a second
unmeasured component to a harness whose entire purpose is measurement. A scenario
whose model output claims one thing in prose and another in the result line is
recorded as a failure, not resolved in the model's favour.

### Runs are repeated, and runner errors are not behavior data

Each scenario runs N times (default 3). The report separates observed passes,
behavior failures and runner errors, so a flaky network cannot masquerade as a
compliance signal, and disagreement across runs is surfaced as instability rather
than averaged into a verdict.

### Isolation from the deterministic suite is structural, not conventional

The harness lives in `evals/`, outside the `tests/` discovery root, so
`unittest discover -s tests` cannot collect it by construction rather than by a
skip decorator someone can remove. Its own deterministic tests live in `tests/`
and drive it with a stub runner. `install.sh` and the package-layout tests
continue to exclude development-only trees, alongside `dev/` and `research/`.

### CI runs evaluation only on demand

Evaluation is a separate, manually triggered, non-blocking workflow that needs a
configured secret. The required jobs added in `.github/workflows/ci.yml` stay
deterministic and offline.

## Risks / Trade-offs

- **Fidelity: the harness is not a real host.** Qwen Code and Codex wrap
  instructions in their own system prompts and expose real tools; the harness
  supplies text and reads text. → Treat results as a lower bound on
  instruction quality rather than a prediction of host behavior, state the
  approximation in the report, and keep the runner contract open so a real-CLI
  wrapper can be plugged in later without changing scenarios.
- **The required result line perturbs the measurement.** → Keep it a report of
  outcome rather than an instruction about conduct; treat prose/line
  contradiction as failure; revisit if scenarios start failing on format rather
  than behavior.
- **Cost and non-determinism discourage use.** → Default to a small scenario set
  and N=3, keep it off the required path, and make a full run explicitly
  invoked.
- **A green evaluation invites overclaiming.** → The spec forbids guarantee
  wording, the report always carries runner identity and run count, and no gate
  consumes the result.
- **Scenarios can rot against edited instructions.** → A scenario names the
  shipping instruction files by repository-relative path instead of carrying a
  copy of them, so it always evaluates the text that actually ships and a missing
  or renamed file fails the scenario loudly. Copying the instructions into the
  scenario was considered and rejected for the opposite reason: a stale copy
  would keep passing while the real instructions drifted away from it.

## Migration Plan

Purely additive: a new tree, new deterministic tests, and one optional workflow.
Nothing existing changes behavior, so rollback is deletion of `evals/`, its tests
and the optional workflow. The change is deliberately sequenced before the
instruction-simplification work in `R2`, so that rewriting `SKILL.md` files has
some behavioral evidence to lean on rather than only substring assertions.

## Open Questions

- Which runner becomes the documented default example — a thin API wrapper or a
  headless `codex`/`qwen` invocation — is left to the first real use, since it
  depends on what the maintainer already authenticates against.
- Whether nested-child and parallel-branch behavior can be evaluated meaningfully
  without a tool surface is unresolved; the initial scenario asserts only the
  reported result and durable-state claim, and may prove too weak.
