# Cookbook: selective Superpowers practices

Status: draft

Checked against: repository commit `19b834b`, 2026-08-11. The baseline includes
the USW text-first entrypoints, `usw.yaml` schema version 1, current packaged
templates and the repository-local OpenSpec specifications at that commit.

Superpowers practices are optional techniques for a concrete risk or need. They
are not an always-running framework and do not become a second workflow system.
This recipe is guidance only: it does not invoke a technique, run a flow or
change a skill automatically.

## Three layers, one source of truth for each purpose

- **OpenSpec is the durable layer** for accepted behavior, contract changes,
  product decisions and their implementation scope. A decision that must remain
  authoritative after the current run belongs in `openspec/`.
- **USW flows and cookbooks are the normal operational layer.** They describe
  how recurring work is performed, reviewed and handed off. The
  [text-first contract](../../README.md#text-first-execution) keeps that process
  readable and project-owned.
- **Superpowers practices are temporary working techniques.** Use one only when
  its trigger is present, then return its useful evidence or decision to the
  existing USW/OpenSpec path. Do not create competing plans, task state or
  specifications.

The layers may cooperate without nesting every task inside all three. For
example, an OpenSpec change may be implemented through a USW flow while TDD is
used only for its riskiest business rule.

## Choose the smallest applicable path

| Situation | Default response | Why |
| --- | --- | --- |
| Ordinary small work with clear behavior | Use the normal USW flow or direct project practice | The operational path is already sufficient. |
| A behavior, public contract or durable product decision must be made | Create or update OpenSpec; use [intent-to-spec](../flows/intent-to-spec.md) when its decision process is useful | The decision needs an authoritative, durable home. |
| A bug, regression or test failure has an unclear cause | Use systematic debugging until the cause is evidenced | Diagnosis is the risk; guessing at fixes is premature. |
| Business logic is risky, subtle or costly to regress | Use TDD for that behavior | Executable examples reduce implementation and regression risk. |
| A substantial change needs isolation from current work | Use a worktree | Isolation protects unrelated work and makes scope easier to inspect. |
| A risky commit is about to be created | Run proportionate verification for the affected contracts | Evidence should match the likely impact; exhaustive ritual is not the goal. |
| An approved implementation has several dependent steps | Use plan execution and review where they improve coordination or catch mistakes | The technique helps maintain agreed order and independent checks. |

More than one trigger may apply. Select only the techniques that address an
observed risk. Absence of a trigger means the ordinary USW path remains the
default.

## Practical recipe

1. Classify the work using the table. If a durable behavior or contract choice
   is unresolved, settle it in OpenSpec before treating implementation as
   approved.
2. Name the concrete risk: unknown cause, regression-prone logic, unsafe
   overlap, multi-step coordination or commit impact.
3. Apply only the matching technique and keep its scope narrow. TDD may cover
   one rule; a worktree may isolate one substantial change; verification may
   target only affected contracts.
4. Keep workflow state in its existing owner. USW owns operational progress;
   OpenSpec owns durable decisions and change scope. Technique-specific notes
   are evidence, not a parallel backlog or specification.
5. Stop using the technique when its trigger is resolved. Report the evidence,
   remaining uncertainty and next normal USW/OpenSpec action.

## When Superpowers is excessive

Do not require Superpowers practices in these cases:

- mandatory invocation on every task regardless of risk;
- forced brainstorming or planning for a trivial, already-decided change;
- duplicated checklists, plans, task status or decision logs alongside USW and
  OpenSpec;
- an automatic pipeline that applies every technique for completeness;
- replacing OpenSpec as the durable specification layer;
- replacing USW flows and cookbooks as the normal operational layer.

The test is practical: if removing the technique would not materially increase
uncertainty, regression risk, isolation risk or coordination risk, omit it.

## Freshness and validation

USW and OpenSpec evolve, so this recipe must not be trusted indefinitely from
memory. Run a proportionate check periodically when the recipe is actively
maintained, or before changing a related flow or skill. Do not turn the check
into a mandatory scheduled service or a gate on every task.

### Cheap structural check

1. Record an ISO date and reproducible baseline: commit or ref, relevant dirty
   state, `usw.yaml` schema version, and any project-local OpenSpec version or
   template identity that exists.
2. Inspect the current entrypoints rather than relying on this recipe:
   [README](../../README.md), [`usw.yaml`](../../usw.yaml),
   [`usw-create-flow`](../../skills/usw-create-flow/SKILL.md),
   [`usw-run-flow`](../../skills/usw-run-flow/SKILL.md),
   [intent-to-spec](../flows/intent-to-spec.md), current packaged templates and
   the repository-local [`openspec/specs`](../../openspec/specs/) tree.
3. Resolve every referenced path and command. Validate claims about ownership,
   versions, selectors, templates and contracts against current primary source.
4. If structure and contracts still match, update `Checked against` with the
   new baseline and date. If anything differs, report the exact mismatch and
   mark the recipe `needs-refresh` or `stale`; do not silently apply the old
   guidance.

A link checker or small repository test can cover missing paths and headings.
That proves only structural consistency, not that upstream meaning is
unchanged.

### Human semantic review

Request a focused human review when current USW or OpenSpec source changes the
meaning of an entrypoint, lifecycle, authority boundary, template or contract,
even if every link still resolves. The reviewer compares the decision table and
layer ownership above with current source, decides whether the recipe remains
valid, and records the new baseline or a mismatch. Until that decision, treat
affected guidance as stale rather than adapting it silently.

## Criterion of readiness

The recipe is ready for optional reuse when:

- OpenSpec, USW and optional techniques have distinct ownership;
- every table row has a concrete trigger and proportionate response;
- no technique is mandatory without its trigger;
- referenced paths and contract claims match the recorded baseline;
- mismatches become an explicit refresh or decision, never automatic behavior.
