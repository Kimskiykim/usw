# Task 4.1: Acceptance and regression

## Scope

- Exercise the skill contract against finite, bounded-retry, unconditional
  cycle, uncertain retry, missing dependency and unsafe-repeat examples.
- Perform a read-only semantic smoke assessment of `intent-to-spec`.
- Run the complete production test and OpenSpec validation commands.

## Non-scope

- Fixing findings in the assessed `intent-to-spec` flow.
- Archiving or syncing the OpenSpec change.

## Dependencies

- Tasks 1.1, 2.1 and 3.1.

## Definition of Done

- Expected verdict/severity mappings are evidenced without modifying assessed
  flows or HANDOFF.
- Full unittest discovery, diff validation and strict change validation pass.
- The OpenSpec apply checklist contains no incomplete tasks.

## Proof of completion

Scenario and read-only evidence: [smoke.md](smoke.md).

```text
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
openspec validate add-flow-assessment --strict
```
