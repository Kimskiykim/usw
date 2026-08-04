# Task 3.1: Package and document assessment

## Scope

- Add the new skill and command to standalone installation.
- Extend Qwen, GigaCode and Codex package-surface checks.
- Document syntax, output, semantic guarantees and non-goals in README and
  plugin descriptions.

## Non-scope

- A new package dependency or release-version change.
- Automatic preflight integration.

## Dependencies

- Task 2.1.

## Definition of Done

- Default and forced installation copy the skill and command for both agents.
- All manifests still expose valid package roots.
- Documentation states that assessment is model-semantic, read-only and not a
  machine proof.

## Proof of completion

```text
python3 -m unittest tests.test_install -v
python3 -m unittest tests.test_package_layout -v
```
