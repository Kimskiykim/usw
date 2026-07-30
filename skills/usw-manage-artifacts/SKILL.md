---
name: usw-manage-artifacts
description: Create or update one role-authorized planning artifact or immutable reviewer receipt. Use only as an atomic action inside a validated USW flow.
---

# Manage USW artifacts

- Inputs: validated `usw.yaml`, one artifact role, exact target/reference set,
  content or receipt decision, and scenario Write authority.
- Permitted writes: the one authorized planning artifact, or one new receipt
  under `reviews.root`.
- Outputs: structured action outcome with written roles and output references.
- Return point: after one write or one pre-write error; never choose or invoke
  the next skill.

Use `scripts/artifact_writer.py`. It writes only beneath the configured
project-owned artifact or review root and rejects unauthorized roles, unsafe
paths and symbolic-link traversal before writing.
