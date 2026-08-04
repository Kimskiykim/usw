## Context

USW executes ordinary and `version-2` Markdown as model-readable text, not a
machine DSL. The existing runner already enforces safe path containment,
no-symlink traversal, UTF-8 and exact-byte identity, but its CLI currently
requires execution input even for read-only inspection.

## Goals / Non-Goals

**Goals:**

- Explicitly assess one named local or shared flow without changing it.
- Find evidence-backed logical, dependency and termination defects.
- Preserve exact Markdown identity and return a stable conservative report.

**Non-Goals:** parser/DSL, persistent graph, execution or repair, automatic
preflight, recursive child-flow assessment, or mathematical termination proof.

## Decisions

### 1. Separate explicit capability

Add `usw-assess-flow` with implicit invocation disabled and syntax:

```text
$usw-assess-flow [--local|-l|--shared] <flow-name> [<scenario-input>]
```

Only leading tokens are selectors; remaining text is opaque scenario input.
No selector means local-first. Invalid selectors yield `insufficient-data`.
Assessment is not embedded in create/run because semantic false positives must
not silently block authoring or execution.

### 2. Exact read-only loader

Add `inspect` beside compatible `resolve`. It accepts project/shared roots,
name and optional origin, uses the existing safe resolver, and returns `name`,
`origin`, `identity`, `path`, exact `markdown` and `warnings`. It requires no
execution input and does not inspect HANDOFF, `.usw/FLOW.json` or runtime state.
The skill analyzes returned Markdown without reopening `path`.

### 3. One bounded LLM-native analysis

Build only a transient reasoning map of steps, gates, returns, terminal states
and data dependencies. Check reachability, error paths, use-before-produce,
explicit/implicit cycles, exit or escalation, observable progress, repeated
side effects and dependency contracts. Do not persist or emit a runtime graph.

### 4. Conservative verdicts

Precedence is: proven blocking defect → `not-executable`; inadequate semantics
→ `insufficient-data`; risk/materially unverified dependency →
`executable-with-risks`; otherwise `executable`.

Blocking is limited to a reachable dead end, definite unbounded cycle,
contradictory mandatory actions, missing mandatory dependency without handling,
or repeated irreversible side effect without idempotency protection. A proven
contract-invalid mandatory invocation without handled fallback is one concrete
reachable-dead-end case. Approval before a loop does not make repeated side
effects safe: absent idempotency, keep the irreversible action and its approval
outside the loop. Uncertain eventual success is a risk. Each finding has ID,
severity, exact evidence, impact and a minimal unapplied Markdown fix.

### 5. Dependency checks stay non-recursive

Inspect declared dependencies and named skill/command/flow calls without
executing them. Use `confirmed`/`missing` only with authoritative evidence and
otherwise `unverified`. A child flow may be safely resolved for availability,
but its body is not assessed. Explicit `blocked`, `failed` or
`decision_required` handling prevents absence alone from becoming blocking.

### 6. Scenario trace is subordinate

Optional scenario input traces one likely path while remaining separate from
immutable Markdown. It never removes findings on other declared paths.

### 7. Reproducible semantic acceptance evidence

Keep the fixture Markdown and raw model reports used by semantic smoke checks
inside the change. The summary distinguishes expected mappings from actually
observed reports and records the invocation boundary. If the assessment skill
was not executed, the result remains expected-only and acceptance is not
reported as observed.

## Risks / Trade-offs

- Model misclassification → exact evidence, conservative thresholds and a
  no-machine-guarantee disclaimer.
- Catalog variance → preserve `unverified` unless presence/absence is proven.
- Hidden cross-flow cycles → state the non-recursive boundary.
- Non-deterministic model output → preserve exact fixtures, raw reports and the
  evidence-backed basis for each observed verdict.
- CLI regression → focused subprocess tests cover legacy `resolve` forms.

## Migration Plan

1. Add and verify `inspect` while preserving `resolve`.
2. Add explicit skill/command, then installer surfaces and documentation.
3. Run focused and full-suite checks.
4. Run semantic smoke checks from checked-in fixtures and preserve raw reports.

Rollback removes the new command, skill and `inspect` branch; flows and runtime
state require no migration. Numeric scoring, recursion and automatic preflight
remain future changes.
