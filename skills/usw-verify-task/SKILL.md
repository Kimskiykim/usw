---
name: usw-verify-task
description: Independently verify one exact source against the normative product contract and append Testing-owned evidence or findings. Use only inside a validated Testing scenario.
---

# Independently verify a task

- Inputs: explicit scope, normative contract, exact canonical source identity,
  current Development evidence, and one independent check.
- Permitted writes: independent tests, Testing findings, `testing-evidence`, and
  `local-checkpoint` only.
- Outputs: structured action outcome with evidence/finding references.
- Return point: after one independent check; never repair inspected
  implementation, edit Development evidence/specifications, or invoke another
  skill.

Use `scripts/verify_scope.py`, passing the validated project root and task root;
the writer derives `testing-evidence.md` and rejects external, symlinked, or
non-task paths. Every entry records a finding or explicit `none`.
