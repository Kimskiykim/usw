## Context

The repository already has a plain Markdown path, but the same production skill
also carries a strict parser, typed executor graph, bindings, loop state,
parallel orchestration and JSON checkpoints. A concurrent in-progress change has
added run-scoped structured checkpoints; that work must be preserved rather than
discarded, but it conflicts with the agreed product direction.

USW is distributed as a Codex plugin, Qwen/Gigacode extension and by
`install.sh`. The `skills/` directory is therefore the production package
boundary. Anything retained only for research must live outside it and must not
be imported by production code or discovered by the main test command.

## Goals / Non-Goals

**Goals:**

- Keep one small, secure loader for every Markdown flow.
- Bind identity to the exact bytes supplied to the model.
- Make handoff optional and define every legacy/current state transition.
- Preserve current structured-runtime work as an unsupported research snapshot.
- Remove stale normative and marketing claims about machine guarantees.

**Non-Goals:**

- Building a replacement parser, compiler or generic executor abstraction.
- Guaranteeing deterministic branches, loops, parallelism or resume positions.
- Migrating or deleting `.usw/FLOW.json`.
- Reworking unrelated artifact and refinement skills.

## Decisions

### One read creates one invocation

The runner opens the selected regular file once, reads bytes once, hashes those
bytes and decodes them as UTF-8. Its JSON result contains `name`, `origin`,
`identity`, `path`, `input` and `markdown`. The model uses that returned
`markdown`; it does not reread `path`.

This is preferred to returning only a path because a path can change between
identity calculation and model execution.

### Structured Markdown is prose

`version-2` remains a useful authoring style. Its markers guide the model but
have no machine semantics. Ambiguity produces `decision_required`; malformed
prose does not produce a parser error. Flow text never grants authority beyond
the user request and platform permissions.

### Minimal compatibility shims

The runner retains only enough argument recognition to identify retired
commands and `--experimental-structured`. Each returns one migration error and
performs no validation, script execution or state mutation.

### Handoff configuration stays schema version 1

`handoff` is an optional top-level boolean. Missing means `true`; quoted values,
numbers and mappings are invalid. With `false`, init and runtime do not read,
validate, create or modify `HANDOFF.md`. Other `.usw` facilities remain usable.

### Handoff transitions are conservative

`in_progress`, `paused`, `blocked` and `decision_required` block every new flow
operation, including the same flow with new input, until explicit finish.
`failed` and `completed` remain inspectable, but the next Begin may atomically
replace them with a new operation. A permission boundary maps to
`decision_required`. An interrupted or failed Outcome write leaves
`in_progress`.

Operation identity is
`flow origin + flow identity + SHA-256(input bytes) + random invocation token`.
The token distinguishes repeated runs with identical flow and input; it is
created only by Begin and is not a machine cursor. `Current position` is
narrative text.

Every handoff read-check-write transition is serialized with an advisory lock
on the already-existing local-state directory. Outcome receives the operation
identity returned by Begin and rejects stale writers. Generic save may update
only the same recoverable operation; Begin is the sole creator of a new
`in_progress` operation from `idle` or terminal state. Save cannot change
immutable flow/input context, clear state, replace legacy state or rewrite
terminal state. Each read validates decoded Input against its digest. Exact-byte
readback after atomic replace is required; a competing valid state is preserved
and reported as write-verification failure.

Legacy role-based handoff is read-only recovery state. Resume reports its saved
context but neither invokes an executor nor rewrites it as generic state.
Explicit finish replaces it with generic idle state. This avoids a second
legacy writer.

The complete transition matrix is:

| Effective config | Existing HANDOFF | Init | New run / Begin | Resume | Outcome | Finish |
| --- | --- | --- | --- | --- | --- | --- |
| absent or `true` | missing | create generic `idle` | stop and require init | missing-state error | invalid | missing-state error |
| absent or `true` | generic `idle` | preserve | write `in_progress` Begin | report no active work | invalid | remain generic `idle` |
| absent or `true` | generic `in_progress`, `paused`, `blocked` or `decision_required` | preserve | block every new operation | show recovery without automatic mutation | allow one non-`in_progress` Outcome | replace with generic `idle` |
| absent or `true` | generic `failed` or `completed` | preserve | atomically replace with `in_progress` Begin | inspect terminal outcome | reject terminal rewrite | replace with generic `idle` |
| absent or `true` | legacy role-based | preserve | block as legacy recovery | read-only recovery | reject generic write | replace with generic `idle` |
| `false` | missing, generic or legacy | do not inspect or create | run without handoff | report disabled without reading | report disabled | report disabled |

Changing `true` to `false` leaves any file byte-for-byte untouched. Changing
`false` to `true` reuses an existing generic or legacy file according to the
table; if the file is missing, the next init creates generic `idle`. Repeating
the same flow with new input is still a new operation identity and is blocked
while a recoverable state exists.

### Legacy FLOW warning is invocation-scoped

Presence is checked without reading or following the path. At most one warning
is emitted per `$usw-run-flow` invocation. No persistent warning marker is
created.

Flow roots and local-state files are traversed descriptor-relatively with
`O_NOFOLLOW`; an earlier path check is never trusted for a later pathname open.

### Exact research migration manifest

The unsupported snapshot is rooted at `research/structured-runtime/` and
contains exactly these preserved files:

- `README.md`;
- `runtime/run_flow.py` (including the in-progress run-scoped checkpoint work);
- `runtime/capability_registry.py`;
- `runtime/flow_scenario.py`;
- `references/run-flow-version-2.md`;
- `references/create-flow-version-1.md`;
- `references/create-flow-version-2.md`;
- `tests/test_flow_orchestrator.py`;
- `tests/test_flow_scenarios.py`;
- `tests/test_end_to_end.py`;
- `tests/fixtures/flow-scenarios/flow-scenario-analysis.md`;
- `tests/fixtures/flow-scenarios/flow-scenario-development.md`;
- `tests/fixtures/flow-scenarios/flow-scenario-testing.md`;
- `specs/execution-artifacts.md`;
- `specs/flow-orchestration.md`;
- `specs/live-operation-state.md`;
- `specs/structured-flow-runtime.md`;
- `specs/validated-composite-flows.md`;
- `changes/add-result-list-iteration/.openspec.yaml`;
- `changes/add-result-list-iteration/proposal.md`;
- `changes/add-result-list-iteration/design.md`;
- `changes/add-result-list-iteration/tasks.md`;
- `changes/add-result-list-iteration/specs/result-list-iteration/spec.md`;
- `changes/add-result-list-iteration/tasks/1.1-compose-for-each/task.md`;
- `changes/add-result-list-iteration/tasks/2.1-iteration-state/task.md`;
- `changes/add-result-list-iteration/tasks/2.2-iteration-state-tests/task.md`;
- `changes/add-result-list-iteration/tasks/3.1-run-one-item/task.md`;
- `changes/add-result-list-iteration/tasks/3.2-run-iteration-tests/task.md`;
- `changes/add-result-list-iteration/tasks/4.1-e2e-regression/task.md`;
- `changes/implement-nested-flow-runtime/.openspec.yaml`;
- `changes/implement-nested-flow-runtime/proposal.md`;
- `changes/implement-nested-flow-runtime/design.md`;
- `changes/implement-nested-flow-runtime/tasks.md`;
- `changes/implement-nested-flow-runtime/specs/nested-flow-runtime/spec.md`.

Whole mixed tests are copied to preserve history; simplified production tests
are rewritten in `tests/`. The snapshot tests are not required to remain
directly runnable after relocation.

Production files must not import `research/`, and package tests assert that the
snapshot is absent from installed skill and command trees.

Installation also removes `__pycache__` and Python bytecode from the copied
target so a dirty development checkout cannot reintroduce retired modules.

## Risks / Trade-offs

- [Models may interpret the same prose differently] → State this limitation
  explicitly and stop for ambiguity or material decisions.
- [Text execution loses durable step resume] → Preserve only narrative handoff;
  build an iterator later if real use cases require it.
- [Generic handoff can become a hidden machine schema] → Keep fields
  human-readable and prohibit machine cursor semantics.
- [Legacy work may be mistaken for supported code] → Put it outside `skills/`,
  mark it unsupported and test for zero production imports.
- [Reducing tests can hide security regressions] → Retain focused resolver,
  config, handoff, packaging and migration tests in the main suite.

## Migration Plan

1. Copy the exact current structured implementation and affected artifacts to
   the research manifest.
2. Replace production runner and contracts with the text-first path.
3. Implement config and handoff transitions.
4. Rewrite normative specs, docs and package metadata.
5. Split production tests from research snapshots and run the full main suite.
6. Mark both former active changes superseded inside the research README.

Rollback is restoring the research snapshot into its original locations. User
state is not migrated or deleted, so rollback does not require data conversion.

## Open Questions

None. A future compiler and iterator require a separate proposal based on
measured text-first limitations.
