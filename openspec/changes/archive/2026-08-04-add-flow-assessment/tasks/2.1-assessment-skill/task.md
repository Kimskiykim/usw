# Task 2.1: Assessment skill and command

## Scope

- Add failing package contract tests for selector parsing, safe inspection,
  report fields, verdict precedence, dependency uncertainty, termination
  analysis, optional scenario tracing and the read-only boundary.
- Add `usw-assess-flow` skill metadata and a public delegating command.
- Specify the concrete semantic checklist and output layout in the skill.

## Non-scope

- Machine parsing, graph persistence, automatic repair or execution.
- Recursive semantic assessment of child flows.
- Automatic invocation from create or run capabilities.

## Dependencies

- Task 1.1.

## Definition of Done

- The skill is explicitly invoked and accepts local/shared selectors, one safe
  name and optional scenario input.
- The report contains the four verdicts, terminal paths, dependency ledger,
  evidence-backed findings and optional scenario trace.
- The skill cannot read/write HANDOFF, execute capabilities or change files.

## Proof of completion

```text
python3 -m unittest tests.test_package_layout.PackageLayoutTests.test_assess_flow_is_explicit_semantic_read_only_analysis -v
python3 -m unittest tests.test_package_layout -v
```
