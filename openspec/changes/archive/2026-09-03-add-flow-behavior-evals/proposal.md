## Why

Every USW guarantee that matters at runtime is produced by a model following
skill instructions, yet nothing in the repository measures whether models
actually follow them. The current contract tests assert that specific sentences
exist in `SKILL.md` files, which verifies wording rather than behavior and
freezes the wording against improvement. The project therefore has strong
evidence about its filesystem boundary and no evidence about its primary
execution boundary.

## What Changes

- Add an opt-in evaluation harness that runs behavior scenarios against a real
  model and reports observed pass rates instead of a single sample.
- Define a scenario as a small directory of plain files: the skill instructions
  under test, the flow Markdown, the user input, and declarative expectations.
- Invoke the model through a user-configured external command, so the harness
  stays dependency-free and provider-agnostic and never embeds an SDK or key.
- Skip cleanly with an explanatory report when no runner is configured, so the
  harness never turns an unconfigured environment into a failure.
- Keep evaluation out of `unittest discover -s tests`, out of the default CI
  path, and out of everything `install.sh` installs.
- Cover the invariants that instructions exist to produce: permission
  boundaries surface as `decision_required`, materially ambiguous flow text
  stops instead of guessing, nested children never write durable state, only
  the five documented statuses are returned, and flow text or user input claiming
  authority does not grant it.
- Test the harness itself deterministically with a stub runner, so scenario
  loading, assertion evaluation, and reporting are covered by the ordinary suite.

## Capabilities

### New Capabilities

- `flow-behavior-evaluation`: Defines opt-in, provider-agnostic measurement of
  model-facing instruction compliance, its scenario and expectation format, its
  reporting of rates over repeated runs, its skip and failure semantics, and the
  boundaries that keep it out of deterministic test discovery, default CI, and
  installed artifacts.

### Modified Capabilities

None. This change measures existing behavior and does not alter any requirement
of an existing capability.

## Impact

- New `evals/` tree: harness entrypoint, scenario directories, report writer.
- New deterministic tests for the harness under `tests/`.
- `install.sh` and package-layout tests, which must continue to exclude
  development-only trees.
- Optional non-blocking CI job, kept separate from the deterministic jobs added
  in `.github/workflows/ci.yml`.
- No new runtime dependency, no change to `run_flow.py` or `handoff_state.py`,
  and no new execution authority. Results are measurements, not guarantees, and
  a passing rate does not certify a model or a release.
