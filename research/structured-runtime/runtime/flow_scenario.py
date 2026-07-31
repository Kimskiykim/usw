#!/usr/bin/env python3
"""Structural validation for project-owned USW flow scenarios."""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple


REQUIRED_SECTIONS = (
    "Purpose",
    "Inputs",
    "Ordered actions",
    "Branches",
    "Write authority",
    "Stop conditions",
    "Outputs",
)
ROLES = {"Analysis", "Development", "Testing"}
SHARED_ACTIONS = {
    "check-inputs", "restore-context", "confirm-scope", "internal-review",
    "propose-handoff",
}
ROLE_ACTIONS = {
    "Analysis": SHARED_ACTIONS | {
        "clarify-intent", "select-approach", "write-proposal-and-specs",
        "assess-spec-complexity", "transition-review-development",
    },
    "Development": SHARED_ACTIONS | {
        "write-design-and-tasks", "execute-bounded-scope", "local-verification",
        "write-development-evidence", "transition-review-testing",
    },
    "Testing": SHARED_ACTIONS | {
        "independent-verification", "write-testing-evidence",
        "transition-review-delivery",
    },
}
ROLE_ARTIFACT_ROLES = {
    "Analysis": frozenset({
        "refinement-state", "proposal", "capability-specs", "review-receipt",
        "local-checkpoint",
    }),
    "Development": frozenset({
        "technical-design", "task-index", "task-contract", "implementation",
        "implementation-tests", "development-evidence", "review-receipt",
        "local-checkpoint",
    }),
    "Testing": frozenset({
        "independent-tests", "testing-findings", "testing-evidence",
        "review-receipt", "local-checkpoint",
    }),
}
KNOWN_ACTIONS = set().union(*ROLE_ACTIONS.values())
KNOWN_ARTIFACT_ROLES = frozenset().union(*ROLE_ARTIFACT_ROLES.values())


class ScenarioError(ValueError):
    pass


class Scenario(NamedTuple):
    role: str
    actions: tuple[str, ...]
    artifact_roles: frozenset[str]
    stops: frozenset[str]
    branches: tuple[tuple[str, str, str], ...]


def _sections(content: str) -> dict[str, str]:
    headings = list(re.finditer(r"^## (.+)$", content, re.MULTILINE))
    result: dict[str, str] = {}
    for index, match in enumerate(headings):
        name = match.group(1).strip()
        if name in result:
            raise ScenarioError(f"duplicate section: {name}")
        end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
        result[name] = content[match.end() : end].strip()
    return result


def validate_scenario(content: str) -> Scenario:
    sections = _sections(content)
    if tuple(sections) != REQUIRED_SECTIONS:
        raise ScenarioError("scenario sections must appear exactly in normative order")
    if any(not sections[name] for name in REQUIRED_SECTIONS):
        raise ScenarioError("scenario sections must not be empty")
    role_match = re.search(r"^- Role: `([^`]+)`$", sections["Purpose"], re.MULTILINE)
    if not role_match or role_match.group(1) not in ROLES:
        raise ScenarioError("scenario must declare one of three role flows")
    role = role_match.group(1)
    actions = tuple(re.findall(r"^[0-9]+\. `([^`]+)`$", sections["Ordered actions"], re.MULTILINE))
    if not actions or len(actions) != len(set(actions)):
        raise ScenarioError("ordered actions must be unique and non-empty")
    unknown_actions = set(actions) - KNOWN_ACTIONS
    if unknown_actions:
        raise ScenarioError(f"unknown action references: {sorted(unknown_actions)}")
    unauthorized_actions = set(actions) - ROLE_ACTIONS[role]
    if unauthorized_actions:
        raise ScenarioError(
            f"{role} scenario contains unauthorized actions: {sorted(unauthorized_actions)}"
        )
    artifact_roles = frozenset(re.findall(r"^- `([^`]+)`$", sections["Write authority"], re.MULTILINE))
    if not artifact_roles or artifact_roles - KNOWN_ARTIFACT_ROLES:
        raise ScenarioError("invalid Write authority artifact role")
    unauthorized_roles = artifact_roles - ROLE_ARTIFACT_ROLES[role]
    if unauthorized_roles:
        raise ScenarioError(
            f"{role} scenario contains unauthorized Write authority: {sorted(unauthorized_roles)}"
        )
    stops = frozenset(re.findall(r"^- `([^`]+)`$", sections["Stop conditions"], re.MULTILINE))
    if not stops:
        raise ScenarioError("missing stop conditions")
    branches = re.findall(r"^- `([^`:]+):([^`]+)` -> `([^`]+)`$", sections["Branches"], re.MULTILINE)
    if not branches:
        raise ScenarioError("branches must use action:outcome targets")
    for source, _outcome, target in branches:
        if source not in actions:
            raise ScenarioError(f"branch references absent action: {source}")
        if target.startswith("stop:"):
            if target.removeprefix("stop:") not in stops:
                raise ScenarioError(f"branch references absent stop: {target}")
        elif target not in actions:
            raise ScenarioError(f"branch references absent target action: {target}")
    if "internal-review" not in actions or not any(action.startswith("transition-review-") for action in actions):
        raise ScenarioError("role scenario requires internal and transition review gates")
    return Scenario(role, actions, artifact_roles, stops, tuple(branches))


def load_project_scenario(flow_root: Path, name: str) -> Scenario:
    """Load only a project-owned scenario; package fallback is forbidden."""
    if name not in {"analysis", "development", "testing"}:
        raise ScenarioError(f"unknown scenario: {name}")
    path = flow_root / f"flow-scenario-{name}.md"
    if not path.is_file():
        raise ScenarioError(f"project scenario is missing: {path}")
    scenario = validate_scenario(path.read_text(encoding="utf-8"))
    expected_role = name.capitalize()
    if scenario.role != expected_role:
        raise ScenarioError(
            f"scenario file {path.name} declares {scenario.role}, expected {expected_role}"
        )
    return scenario
