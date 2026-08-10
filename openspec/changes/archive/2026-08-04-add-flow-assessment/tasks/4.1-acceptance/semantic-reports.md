# Raw semantic assessment reports

Date: 2026-08-03

Invocation boundary: each checked-in fixture was loaded with
`run_flow.py inspect <project> <fixtures-root> <name> --origin shared`. The
current Codex implementation session then applied the exact
`skills/usw-assess-flow/SKILL.md` semantic scan and output contract directly to
the returned immutable Markdown, without scenario input. These are model
reports, not machine guarantees or installed-catalog invocation results.

Skill SHA-256:
`44dd4ac985c4c94ec285da692e1f11cbf96c9e90a06b13f08f63596fde138070`.

## finite

- Flow: `finite`
- Origin: `shared`
- Path: `fixtures/finite.md`
- Identity: `usw-markdown:shared:9318ee6c32a8bec10114e26231d0852140b3be01e201406fbf6fe02771e65dab`
- Verdict: `executable`
- Basis: evidence-backed semantic model analysis; not machine guarantee.

### Terminal paths

- The ordered check reaches explicit `completed`.

### Dependencies

None.

### Findings

None.

## bounded-retry

- Flow: `bounded-retry`
- Origin: `shared`
- Path: `fixtures/bounded-retry.md`
- Identity: `usw-markdown:shared:05dbfe1c249317cb96f5749a3b942ad4512d794a25b916cc671ac5a0391f1f59`
- Verdict: `executable`
- Basis: evidence-backed semantic model analysis; not machine guarantee.

### Terminal paths

- A successful attempt reaches `completed`.
- Three failed attempts reach `failed`.

### Dependencies

None.

### Findings

None.

## unconditional-cycle

- Flow: `unconditional-cycle`
- Origin: `shared`
- Path: `fixtures/unconditional-cycle.md`
- Identity: `usw-markdown:shared:67bef741426ab93721257a7d5b4fa3ded292cd7fbb36aad0a4100cc71504d439`
- Verdict: `not-executable`
- Basis: evidence-backed semantic model analysis; not machine guarantee.

### Terminal paths

- A reaches B and B unconditionally returns to A; no terminal outcome is
  reachable.

### Dependencies

None.

### Findings

- F-1 [blocking] unconditional-cycle
  - Evidence: headings `A` and `B`; “Return unconditionally to A.”
  - Impact: execution repeats forever without exit or escalation.
  - Minimal fix: add a bounded exit condition and a terminal `failed` or
    `decision_required` outcome.

## uncertain-retry

- Flow: `uncertain-retry`
- Origin: `shared`
- Path: `fixtures/uncertain-retry.md`
- Identity: `usw-markdown:shared:ece3f498b0248b2772bd0cea9e6dcbdb6346398470f4e7c9a2250b2d36a3a10f`
- Verdict: `executable-with-risks`
- Basis: evidence-backed semantic model analysis; not machine guarantee.

### Terminal paths

- Success reaches `completed`; repeated failure has no bounded terminal path.

### Dependencies

None.

### Findings

- F-1 [risk] unbounded-retry
  - Evidence: “Repeat the read-only check until it succeeds.”
  - Impact: eventual success is uncertain, so execution may never terminate.
  - Minimal fix: limit attempts and return `failed` after exhaustion.

## missing-dependency

- Flow: `missing-dependency`
- Origin: `shared`
- Path: `fixtures/missing-dependency.md`
- Identity: `usw-markdown:shared:2d4a0d918eef5382dbb906f9887c070f1bc1f3606d07c8bbe9a3f1f644c190f7`
- Verdict: `not-executable`
- Basis: evidence-backed semantic model analysis; not machine guarantee.

### Terminal paths

- The mandatory call cannot start and has no fallback; `completed` is not
  reachable.

### Dependencies

- D-1 | skill/`missing-assessment-dependency` | `missing` | absent from the
  current capability catalog; no fallback is declared.

### Findings

- F-1 [blocking] missing-mandatory-dependency
  - Evidence: `Dependencies` declares the bundled skill and the call is
    mandatory with “No fallback is available.”
  - Impact: the only declared execution path stops before its terminal outcome.
  - Minimal fix: return `decision_required` when the dependency is unavailable.

## handled-missing-dependency

- Flow: `handled-missing-dependency`
- Origin: `shared`
- Path: `fixtures/handled-missing-dependency.md`
- Identity: `usw-markdown:shared:c82651ddf4b74e89de53e54810cdbd45c64e32ba948521fc9cb666b352171392`
- Verdict: `executable`
- Basis: evidence-backed semantic model analysis; not machine guarantee.

### Terminal paths

- Available dependency and success reach `completed`.
- Unavailable dependency reaches `decision_required`.

### Dependencies

- D-1 | skill/`missing-assessment-dependency` | `missing` | absent from the
  current capability catalog and explicitly handled by `decision_required`.

### Findings

None.

## unsafe-repeat

- Flow: `unsafe-repeat`
- Origin: `shared`
- Path: `fixtures/unsafe-repeat.md`
- Identity: `usw-markdown:shared:54f0d230f452b2f91c63c3ef4fc1a9e5380dbd72e4e4d2d1ece6d1c8055f778d`
- Verdict: `not-executable`
- Basis: evidence-backed semantic model analysis; not machine guarantee.

### Terminal paths

- Successful deployment reaches `completed`; failure repeats the irreversible
  write without a bound.

### Dependencies

None.

### Findings

- F-1 [blocking] unsafe-repeat
  - Evidence: “irreversible external write” followed by “repeat the deployment
    with no attempt limit and no idempotency guarantee.”
  - Impact: a reachable loop can repeat an irreversible external mutation.
  - Minimal fix: make deployment idempotent or move the deployment and its
    approval outside the retry loop.
