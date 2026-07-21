#!/usr/bin/env python3
"""Internal provider boundary for atomic planning-artifact operations."""

from __future__ import annotations

import json
import os
import runpy
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import NamedTuple


ARTIFACT_SCRIPT = Path(__file__).parents[2] / "usw-initialize-project/scripts/artifact_contract.py"
CONTRACT = SimpleNamespace(**runpy.run_path(str(ARTIFACT_SCRIPT)))

PLANNING_ROLES = {
    "proposal", "capability-specs", "technical-design", "task-index", "task-contract"
}
OPENSPEC_ROLE_MAP = {
    "proposal": "proposal",
    "capability-specs": "specs",
    "technical-design": "design",
    "task-index": "tasks",
}


class CapabilityOutcome(NamedTuple):
    status: str
    outcome: str
    written_roles: frozenset[str]
    output_references: tuple[str, ...]
    detail: str | None = None


class ProviderDiscovery(NamedTuple):
    change: str
    statuses: dict[str, str]
    resolved_paths: dict[str, tuple[str, ...]]
    change_root: str


def _openspec_json(project_root: Path, *arguments: str) -> dict:
    executable = shutil.which("openspec")
    if executable is None:
        raise RuntimeError("unsupported_provider_operation: openspec executable is unavailable")
    result = subprocess.run(
        [executable, *arguments, "--json"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"provider_contract_error: {message}")
    return json.loads(result.stdout)


def discover_openspec(project_root: Path, change: str) -> ProviderDiscovery:
    """Read the native artifact graph without mutating the OpenSpec workspace."""
    status = _openspec_json(project_root, "status", "--change", change)
    statuses = {item["id"]: item["status"] for item in status.get("artifacts", [])}
    resolved = {}
    for artifact_id, paths in status.get("artifactPaths", {}).items():
        existing = tuple(paths.get("existingOutputPaths", []))
        resolved[artifact_id] = existing or (paths.get("resolvedOutputPath", ""),)
    return ProviderDiscovery(change, statuses, resolved, status["changeRoot"])


def openspec_frontier(discovery: ProviderDiscovery, role: str) -> CapabilityOutcome:
    """Resolve the role frontier independently of aggregate change completion."""
    statuses = discovery.statuses
    paths = discovery.resolved_paths
    if role == "Analysis":
        complete = statuses.get("proposal") == "done" and statuses.get("specs") == "done"
        design_absent = not any(path and Path(path).is_file() for path in paths.get("design", ()))
        if complete and statuses.get("design") == "ready" and design_absent and statuses.get("tasks") == "blocked":
            return CapabilityOutcome("completed", "analysis-frontier-ready", frozenset(), (), None)
        return CapabilityOutcome("blocked", "missing_required_artifact", frozenset(), (), "proposal/specs frontier is incomplete")
    if role == "Development":
        for artifact_id, role_name in (("design", "technical-design"), ("tasks", "task-index")):
            absent = not any(path and Path(path).is_file() for path in paths.get(artifact_id, ()))
            if statuses.get(artifact_id) == "ready" and absent:
                return CapabilityOutcome("completed", f"create-{artifact_id}", frozenset(), (role_name,), None)
        if statuses.get("design") == statuses.get("tasks") == "done":
            return CapabilityOutcome("completed", "development-frontier-ready", frozenset(), (), None)
        return CapabilityOutcome("blocked", "missing_required_artifact", frozenset(), (), "design/tasks frontier is incomplete")
    return CapabilityOutcome("blocked", "unsupported_provider_operation", frozenset(), (), f"role frontier is unsupported: {role}")


def resolve_openspec_artifact(
    discovery: ProviderDiscovery, artifact_id: str, *, required: bool
) -> CapabilityOutcome:
    paths = tuple(path for path in discovery.resolved_paths.get(artifact_id, ()) if path)
    existing = tuple(path for path in paths if Path(path).is_file())
    if existing:
        return CapabilityOutcome("completed", "resolved", frozenset(), existing)
    outcome = "missing_required_artifact" if required else "missing_optional_artifact"
    return CapabilityOutcome("blocked", outcome, frozenset(), paths)


def write_openspec_artifact(
    project_root: Path,
    *,
    change: str,
    role: str,
    content: str,
    relative_path: str | None = None,
) -> CapabilityOutcome:
    artifact_id = OPENSPEC_ROLE_MAP.get(role)
    if artifact_id is None:
        return CapabilityOutcome("blocked", "unsupported_provider_operation", frozenset(), (), f"OpenSpec does not support role {role}")
    try:
        discovery = discover_openspec(project_root, change)
    except (RuntimeError, OSError, json.JSONDecodeError) as error:
        message = str(error)
        outcome = "unsupported_provider_operation" if message.startswith("unsupported_provider_operation") else "provider_contract_error"
        return CapabilityOutcome("blocked", outcome, frozenset(), (), message)
    if discovery.statuses.get(artifact_id) not in {"ready", "done"}:
        return CapabilityOutcome("blocked", "missing_required_artifact", frozenset(), (), f"OpenSpec artifact is not ready: {artifact_id}")
    try:
        instructions = _openspec_json(
            project_root, "instructions", artifact_id, "--change", change
        )
    except (RuntimeError, OSError, json.JSONDecodeError) as error:
        return CapabilityOutcome("blocked", "provider_contract_error", frozenset(), (), str(error))
    if artifact_id == "specs":
        if not relative_path:
            return CapabilityOutcome("blocked", "missing_required_artifact", frozenset(), (), "capability spec path is required")
        target = (Path(discovery.change_root) / relative_path).resolve(strict=False)
        specs_root = (Path(discovery.change_root) / "specs").resolve(strict=False)
        try:
            target.relative_to(specs_root)
        except ValueError:
            return CapabilityOutcome("blocked", "invalid_artifact_path", frozenset(), (), None)
    else:
        target = Path(instructions["resolvedOutputPath"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return CapabilityOutcome("completed", "written", frozenset({role}), (target.as_posix(),))


def _safe_target(project_root: Path, artifact_root: str, relative_path: str) -> Path:
    root_relative = PurePosixPath(artifact_root)
    relative = PurePosixPath(relative_path)
    if (
        root_relative.is_absolute()
        or not root_relative.parts
        or any(part in {"", ".", ".."} for part in root_relative.parts)
        or relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ValueError("unsafe artifact path")
    project = project_root.resolve(strict=True)
    lexical_root = project.joinpath(*root_relative.parts)
    lexical_target = lexical_root.joinpath(*relative.parts)
    current = project
    for part in lexical_target.relative_to(project).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("artifact path traverses symbolic link")
    root = lexical_root.resolve(strict=False)
    target = lexical_target.resolve(strict=False)
    target.relative_to(root)
    return target


def write_planning_artifact(
    project_root: Path,
    *,
    provider: str,
    artifact_root: str,
    role: str,
    relative_path: str,
    content: str,
    permitted_roles: frozenset[str],
    change: str | None = None,
) -> CapabilityOutcome:
    if role not in PLANNING_ROLES or role not in permitted_roles:
        return CapabilityOutcome("blocked", "authority_mismatch", frozenset(), (), "role is not authorized")
    if provider == "openspec" and change:
        return write_openspec_artifact(
            project_root,
            change=change,
            role=role,
            content=content,
            relative_path=relative_path,
        )
    if provider != "standalone":
        return CapabilityOutcome(
            "blocked", "unsupported_provider_operation", frozenset(), (),
            f"planning write adapter is unavailable for provider {provider}",
        )
    target = _safe_target(project_root, artifact_root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return CapabilityOutcome("completed", "written", frozenset({role}), (target.as_posix(),))


def write_review_receipt(project_root: Path, review_root: Path, **receipt_fields) -> CapabilityOutcome:
    receipt = CONTRACT.write_receipt(project_root, review_root, **receipt_fields)
    return CapabilityOutcome(
        "completed", "receipt-written", frozenset({"review-receipt"}), (receipt.as_posix(),)
    )
