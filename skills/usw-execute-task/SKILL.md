---
name: usw-execute-task
description: Execute one explicitly selected Development scope, record bounded local checkpoint facts, run named local verification, and append Development-owned evidence. Use only inside a validated Development scenario.
---

# Execute a bounded task

- Inputs: one explicit step/task/change scope, current task contract revision,
  canonical product source identity, and required local checks.
- Permitted writes: implementation, implementation-adjacent tests,
  `development-evidence`, task checkbox/contract when authorized, and
  `local-checkpoint`.
- Outputs: structured action outcome and evidence/reference IDs.
- Return point: after exactly one bounded operation or check; never expand scope,
  edit Testing evidence, claim human acceptance, or invoke the next skill.

Use `scripts/execute_scope.py` for append-only Development evidence, passing the
validated project root and task root; the writer derives
`development-evidence.md` and rejects external, symlinked, or non-task paths.
Planned checks are not evidence; append only commands actually run against the
named contract/source identities.
