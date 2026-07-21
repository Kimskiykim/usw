---
name: usw-manage-artifacts
description: Create or update one role-authorized planning artifact or immutable reviewer receipt through the configured USW provider. Use only as an atomic action inside a validated USW flow.
---

# Manage USW artifacts

- Inputs: validated `usw.yaml`, one artifact role, exact target/reference set,
  content or receipt decision, and scenario Write authority.
- Permitted writes: the one authorized planning artifact, or one new receipt
  under provider-neutral `reviews.root`.
- Outputs: structured action outcome with written roles and output references.
- Return point: after one write or one pre-write error; never choose or invoke
  the next skill.

Use `scripts/provider_artifacts.py`. V1 adapters are internal implementation
details, not a public plugin API. Built-in `standalone` and `openspec` planning
adapters are supported; OpenSpec operations require an explicit configured
provider, change context, and available OpenSpec CLI. An unavailable adapter or
unsupported operation returns `unsupported_provider_operation` before writing
and never falls back to standalone. Receipt storage is shared and
provider-neutral for both providers.
