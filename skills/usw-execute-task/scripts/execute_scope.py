#!/usr/bin/env python3
"""Development wrapper for the shared append-only evidence contract."""

from __future__ import annotations

import runpy
from pathlib import Path


CONTRACT = runpy.run_path(str(
    Path(__file__).parents[2] / "usw-initialize-project/scripts/artifact_contract.py"
))
CapabilityOutcome = CONTRACT["CapabilityOutcome"]


def append_development_evidence(
    project_root: Path,
    task_root: Path,
    *,
    evidence_id: str,
    contract_revision: str,
    source_identity: str,
    command: str,
    result: str,
    timestamp: str,
) -> CapabilityOutcome:
    return CONTRACT["append_task_evidence"](
        project_root, task_root, role="Development", evidence_id=evidence_id,
        contract_revision=contract_revision, source_identity=source_identity,
        command=command, result=result, timestamp=timestamp,
    )
