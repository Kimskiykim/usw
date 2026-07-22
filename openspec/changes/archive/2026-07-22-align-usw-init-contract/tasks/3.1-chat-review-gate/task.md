# Task 3.1: Cover the `chat-review` follow-up GATE

## Artifact model

- `v1`

## Result

The custom-flow regression suite recognizes `handle-follow-up` and protects all three declared follow-up routes.

## Scope

- Update the expected `chat-review` top-level action sequence.
- Assert `iterate-findings`, `show-proposal` and `make-decision` routes.
- Preserve default whole-Markdown and experimental structured validation coverage.

## Non-scope

- Changing `chat-review` behavior or adding result-list iteration.
- Modifying the structured runtime.

## References

- Proposal: `../../proposal.md`
- Design: `../../design.md`
- Flow: `../../../../../usw/flows/chat-review.md`

## Dependencies

- None.

## Definition of done

- The focused regression passes and fails if the third action or any route is removed.

## Verification

- Run: `python3 -m unittest tests.test_flow_scenarios.CustomFlowTests.test_chat_review_defaults_to_whole_markdown_input -v`
- Expect: the three-action and three-route contract passes.

## Contract revision

- `cr-001`

## Milestone log

| Attempt | Trigger | Contract | Source | Outcome | References |
|---|---|---|---|---|---|
| 1 | task created | `cr-001` | pending | pending | `tasks.md` |
