# Acceptance smoke evidence

Date: 2026-08-03

## Method

Each checked-in fixture was loaded through `run_flow.py inspect` with the
fixture directory as the explicit shared root. The current Codex implementation
session applied the exact repo-local `skills/usw-assess-flow/SKILL.md` semantic
scan and output contract directly to each returned immutable Markdown value.
The exact invocation boundary, loader identities and unedited model outputs are
preserved in [Raw semantic reports](semantic-reports.md). These reports are
evidence-backed semantic analysis, not machine guarantees or claims about an
installed capability catalog.

## Calibration results

| Fixture | Observed direct skill-text result | Evidence |
|---|---|---|
| [fixtures/finite.md](fixtures/finite.md) | `executable` | action reaches explicit `completed` outcome |
| [fixtures/bounded-retry.md](fixtures/bounded-retry.md) | `executable`; no blocking finding | finite retry limit ends in `failed` |
| [fixtures/unconditional-cycle.md](fixtures/unconditional-cycle.md) | `not-executable`; blocking cycle | reachable A → B → A with no exit |
| [fixtures/uncertain-retry.md](fixtures/uncertain-retry.md) | `executable-with-risks`; risk | repeat-until-success has no bound |
| [fixtures/missing-dependency.md](fixtures/missing-dependency.md) | `not-executable`; blocking dependency | mandatory missing call has no fallback |
| [fixtures/handled-missing-dependency.md](fixtures/handled-missing-dependency.md) | `executable`; dependency remains missing | missing call transitions to `decision_required` |
| [fixtures/unsafe-repeat.md](fixtures/unsafe-repeat.md) | `not-executable`; blocking `unsafe-repeat` | irreversible deploy is repeated in a reachable loop |

## Existing flow smoke

`intent-to-spec` resolved as shared identity
`usw-markdown:shared:9ba7d3bb263861ef5f5194be5bd37ddb8a692088561dffc1bcddcb95b9705bbc`.
The assessment found an existing blocking contract mismatch: the flow expects
`change.md`, while `openspec-propose` produces `proposal.md`. It also reported
the retired `--experimental-structured` selector as a risk. No fix was applied.

## Read-only proof

Before and after a fresh inspection pass on all seven checked-in fixtures:

- `.usw/HANDOFF.md` SHA-256:
  `7d3086ee281a68c1f55198c0fa0e80ac9855f34b62290dcabc0f35513b66ee65`;
- every fixture SHA-256 remained identical and matched the digest embedded in
  its `usw-markdown:shared:<sha256>` loader identity recorded in the raw report.

No inspected fixture or HANDOFF byte changed.
