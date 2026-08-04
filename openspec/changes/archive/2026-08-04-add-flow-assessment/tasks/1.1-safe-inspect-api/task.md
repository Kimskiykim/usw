# Task 1.1: Safe inspect API

## Scope

- Add failing subprocess tests for an `inspect` command that needs no
  execution input and returns exact flow metadata and Markdown.
- Refactor the runner CLI to expose `inspect` while preserving `resolve`.
- Cover local-first and explicit origin selection through the shared safe
  loader boundary.

## Non-scope

- Semantic assessment or dependency analysis.
- Changes to root/nested execution, HANDOFF or legacy state warnings.

## Dependencies

None.

## Definition of Done

- `inspect` returns `name`, `origin`, `identity`, `path`, exact `markdown` and
  `warnings` without an input field.
- Inspection does not probe `.usw/FLOW.json` or HANDOFF.
- Existing `resolve` JSON and retired-command behavior remain compatible.

## Proof of completion

```text
python3 -m unittest tests.test_flow_orchestrator.TextFlowRunnerTests.test_cli_inspect_returns_exact_markdown_without_execution_input -v
python3 -m unittest tests.test_flow_orchestrator -v
```
