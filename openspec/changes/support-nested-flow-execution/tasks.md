## 1. Router model and safe paths

- [x] 1.1 Add a validated empty/multi-entry HANDOFF router model and render it
  deterministically without duplicating mutable operation status. Done when
  valid routers round-trip, duplicate identities and malformed entries fail,
  and the current generic and legacy formats remain distinguishable. Check:
  `python3 -m unittest discover -s tests -p 'test_handoff_state.py'`.
- [x] 1.2 Derive every operation filename only from a validated operation ID
  and add descriptor-relative regular-directory/file checks for
  `.usw/handoffs/`. Done when traversal, arbitrary router paths, symlinked
  directories/files and identity/path mismatches fail without changing local
  state. Check:
  `python3 -m unittest discover -s tests -p 'test_handoff_state.py'`.

## 2. Initialization and migration

- [x] 2.1 Change enabled project initialization to create an empty router while
  keeping `.usw/handoffs/` lazy, and preserve the hard `handoff: false`
  boundary. Done when new, repeated, partial-write and disabled initialization
  cases preserve the create-only contract. Check:
  `python3 -m unittest discover -s tests -p 'test_init_usw.py'`.
- [x] 2.2 Migrate valid generic idle state to an empty router and valid generic
  non-idle state to its exact routed operation without losing recovery bytes.
  Done when handled failure leaves the original HANDOFF authoritative and a
  retry completes deterministically. Check:
  `python3 -m unittest discover -s tests -p 'test_handoff_state.py'`.
- [x] 2.3 Preserve legacy HANDOFF as read-only recovery until explicit Finish,
  then replace it with an empty router. Done when legacy Show/Resume remain
  byte-preserving, Begin is blocked and Finish performs no automatic generic
  migration. Check:
  `python3 -m unittest discover -s tests -p 'test_handoff_state.py'`.

## 3. Independently addressed state transitions

- [x] 3.1 Route Begin through a unique operation document and register it only
  after exact-byte verification. Done when model execution cannot start before
  registration, handled partial failure removes only its candidate, and two
  concurrent Begin calls retain both distinct routes. Check:
  `python3 -m unittest discover -s tests -p 'test_handoff_state.py'`.
- [x] 3.2 Address Outcome to one exact registered operation and update only its
  document. Done when concurrent Outcomes preserve both routes and stale,
  missing, terminal and identity-mismatched targets fail without cross-operation
  mutation. Check:
  `python3 -m unittest discover -s tests -p 'test_handoff_state.py'`.
- [x] 3.3 Replace the global Save candidate with an operation-scoped candidate
  and preserve immutable flow/input context. Done when concurrent candidates
  cannot collide and queued, cross-operation, legacy, terminal and tampered
  candidates are rejected independently. Check:
  `python3 -m unittest discover -s tests -p 'test_handoff_state.py'`.
- [x] 3.4 Add exact-ID Show and Resume plus zero/one/many discovery behavior.
  Done when an empty router reports no work, a sole route is selected, multiple
  validated routes return a choice list, and `in_progress` never triggers
  automatic mutation replay. Check:
  `python3 -m unittest discover -s tests -p 'test_handoff_state.py'`.
- [x] 3.5 Address Finish to one exact route, unregister it before removing only
  its operation files and preserve every competing operation. Done when
  zero/one/many selection, terminal cleanup, queued Save/Outcome and
  post-unregistration orphan cases are covered. Check:
  `python3 -m unittest discover -s tests -p 'test_handoff_state.py'`.

## 4. Routed nested execution

- [x] 4.1 Add read-only `assert-current` for an exact registered recoverable
  parent operation. Done when matching `in_progress`, `paused`, `blocked` and
  `decision_required` states succeed while absent, mismatched, terminal,
  legacy, unsafe and disabled states fail without byte changes. Check:
  `python3 -m unittest discover -s tests -p 'test_handoff_state.py'`.
- [x] 4.2 Extend `usw-run-flow` with internal root and nested execution context:
  use the registered Begin identity when handoff is enabled, use an ephemeral
  identity when disabled, safely resolve every child and forbid child state
  mutation. Done when ordinary input cannot select nested mode and a stale
  parent stops before child model execution. Check:
  `python3 -m unittest discover -s tests -p 'test_flow_orchestrator.py'`.
- [x] 4.3 Aggregate child identities, statuses and factual results into only
  their root operation, preserving permission boundaries and prohibiting
  automatic retry. Done when sequential children, two parallel children under
  one root and children under two concurrent roots complete without cross-root
  Outcome writes. Check:
  `python3 -m unittest discover -s tests -p 'test_flow_scenarios.py'` and
  `python3 -m unittest discover -s tests -p 'test_end_to_end.py'`.

## 5. User-facing contracts

- [x] 5.1 Update `usw-manage-handoff`, `usw-run-flow` and initialization skill
  contracts for router layout, exact-ID commands, selection, migration,
  disabled handoff and nested ownership. Done when contract tests reject the
  removed single-operation assumptions and protect the new routing boundaries.
  Check:
  `python3 -m unittest discover -s tests -p 'test_atomic_skill_contracts.py'`
  and `python3 -m unittest discover -s tests -p 'test_flow_scenarios.py'`.
- [x] 5.2 Update README with one concise two-chat example, nested-flow
  composition, explicit terminal cleanup, rollback guidance and the lack of
  product-file isolation. Done when documentation distinguishes concurrent
  roots from nested children without promising scheduling or conflict
  detection. Check:
  `python3 -m unittest discover -s tests -p 'test_package_layout.py'`.

## 6. Integrated verification

- [x] 6.1 Run the full project test suite and strict OpenSpec validation. Done
  when `python3 -m unittest discover -s tests` and
  `openspec validate support-nested-flow-execution --strict` both pass, with no
  unrelated worktree files modified by this change.
