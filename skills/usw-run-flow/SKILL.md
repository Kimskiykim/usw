---
name: usw-run-flow
description: Run one validated project-owned USW role-flow action or one step of a named custom Markdown flow with observable HANDOFF begin/outcome boundaries.
---

# Run a USW flow

Read `usw.yaml` and resolve `flows.root`; when configuration is absent, use the
documented standalone default `usw/flows`. Load only the selected project-owned
flow. Never use a packaged template as a runtime fallback.

## Preflight

Before any mutation:

1. Resolve exactly one scope and exactly one next action. If several are valid,
   stop for a user decision.
2. Resolve every required executor by exact name and compare its declared writes
   with flow Write authority. Missing capability or mismatch stops the flow.
3. Read `.usw/HANDOFF.md`. A non-idle state permits only the same flow and scope.
   If `.usw/FLOW.json` exists, stop for manual recovery; never merge or delete it.
4. Ask `usw-manage-handoff` to perform Begin. It must write `in_progress` and
   read it back successfully. Without a confirmed Begin, do not invoke executor.

## One action

Invoke exactly one skill or validated project-relative script. Require a
structured outcome with status, outcome, written artifact roles, output
references, actual changed areas, verification references, and any blocker,
decision, or permission boundary.

Compare reported writes with executor declarations and flow authority. Then ask
`usw-manage-handoff` to record Outcome before selecting another action:

- `completed`: append one compact journal row and advance the cursor;
- `failed`, `blocked`, `decision_required`, or permission boundary: keep the
  cursor on the same step and stop;
- contract violation: record `failed` and stop.

Return control after this single action. Never launch the following step in the
same invocation.

## Resume

Read only the HANDOFF summary first. Resume only the same flow identity and
scope. `in_progress` without result is a possible interruption inside executor:
inspect current state as needed and never retry mutation automatically. A stale
or unknown source requires explicit reconciliation.

## Standard role flow

Preserve the existing Analysis, Development, Testing, review, and Delivery
branches. Human review executors create their own receipts. At Delivery report
scope, tested source identity, current evidence, observations, and delivery
owner. Commit, push, PR, deploy, and release always require separate permission.

## Named custom flow

A custom flow is Markdown with three required sections:

```markdown
# Flow: plan-check

## Контракт

- Версия: `1`

## Порядок действий

1. Скилл: `usw-plan-small-steps`
   - Пишет: `task-index`
2. Скрипт: `scripts/check_plan`
   - Аргументы: `--strict`
   - Пишет: нет

## Полномочия записи

- `task-index`
```

Validate the executable subset directly from the document:

- name is kebab-case and maps only to `<flows.root>/<name>.md`;
- contract version is exactly `1`;
- steps are consecutive and linear;
- each target is an exact skill name or safe project-relative executable;
- arguments are separate literal values with no shell semantics;
- every declared write is inside `Полномочия записи`.

Execute one numbered step only after the common Preflight and HANDOFF Begin.
The saved HANDOFF flow cursor replaces any new custom-flow checkpoint file.
