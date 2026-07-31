"""Closed v1 mapping from scenario actions to packaged capability skills."""

ACTION_CAPABILITIES = {
    "check-inputs": "usw-run-flow",
    "confirm-scope": "usw-run-flow",
    "propose-handoff": "usw-run-flow",
    "restore-context": "usw-manage-handoff",
    "clarify-intent": "usw-refine-intent",
    "select-approach": "usw-run-flow",
    "assess-spec-complexity": "usw-plan-small-steps",
    "write-proposal-and-specs": "usw-manage-artifacts",
    "write-design-and-tasks": "usw-manage-artifacts",
    "internal-review": "usw-manage-artifacts",
    "transition-review-development": "usw-manage-artifacts",
    "transition-review-testing": "usw-manage-artifacts",
    "transition-review-delivery": "usw-manage-artifacts",
    "execute-bounded-scope": "usw-run-flow",
    "local-verification": "usw-run-flow",
    "write-development-evidence": "usw-run-flow",
    "independent-verification": "usw-run-flow",
    "write-testing-evidence": "usw-run-flow",
}
