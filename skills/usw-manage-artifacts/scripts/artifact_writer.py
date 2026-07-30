#!/usr/bin/env python3
"""Atomic planning-artifact and review-receipt writes."""

from __future__ import annotations

import os
import runpy
import tempfile
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import NamedTuple


ARTIFACT_SCRIPT = Path(__file__).parents[2] / "usw-initialize-project/scripts/artifact_contract.py"
CONTRACT = SimpleNamespace(**runpy.run_path(str(ARTIFACT_SCRIPT)))

PLANNING_ROLES = {
    "proposal", "capability-specs", "technical-design", "task-index", "task-contract"
}


class CapabilityOutcome(NamedTuple):
    status: str
    outcome: str
    written_roles: frozenset[str]
    output_references: tuple[str, ...]
    detail: str | None = None


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
    artifact_root: str,
    role: str,
    relative_path: str,
    content: str,
    permitted_roles: frozenset[str],
) -> CapabilityOutcome:
    if role not in PLANNING_ROLES or role not in permitted_roles:
        return CapabilityOutcome(
            "blocked", "authority_mismatch", frozenset(), (),
            "role is not authorized",
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
    return CapabilityOutcome(
        "completed", "written", frozenset({role}), (target.as_posix(),)
    )


def write_review_receipt(
    project_root: Path, review_root: Path, **receipt_fields
) -> CapabilityOutcome:
    receipt = CONTRACT.write_receipt(
        project_root, review_root, **receipt_fields
    )
    return CapabilityOutcome(
        "completed", "receipt-written", frozenset({"review-receipt"}),
        (receipt.as_posix(),),
    )
