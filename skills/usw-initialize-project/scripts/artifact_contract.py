#!/usr/bin/env python3
"""Validate USW execution artifacts and write immutable review receipts."""

from __future__ import annotations

import hashlib
import os
import re
import struct
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable, NamedTuple


CHECKBOX_RE = re.compile(r"^\s*- \[[ xX]\]", re.MULTILINE)
TASK_LINK_RE = re.compile(
    r"^- \[(?P<status>[ xX])\] (?P<id>[0-9]+(?:\.[0-9]+)*) \[[^]]+\]\((?P<path>tasks/[^)]+/task\.md)\)$",
    re.MULTILINE,
)
MODEL_RE = re.compile(r"^## Artifact model\s*\n\s*- `(?P<model>legacy|v1)`", re.MULTILINE)
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
CONTRACT_REVISION_RE = re.compile(
    r"^## Contract revision\s*\n\s*- `(?P<revision>[^`]+)`", re.MULTILINE
)
SOURCE_ID_RE = re.compile(r"^usw-source-v1:[0-9a-f]{64}$")
EVIDENCE_ROW_RE = re.compile(
    r"^\| (?P<id>[A-Za-z0-9][A-Za-z0-9._-]*) \| `(?P<contract>[^`]+)` \| "
    r"`(?P<source>usw-source-v1:[0-9a-f]{64})` \| `(?P<check>[^`]+)` \| "
    r"(?P<result>passed|failed) \|",
    re.MULTILINE,
)
REVIEW_ROLES = frozenset({"Analysis", "Development", "Testing", "Delivery owner"})
REVIEW_VERDICTS = frozenset({"accepted", "rejected"})
REQUIRED_V1_SECTIONS = (
    "Result",
    "Scope",
    "Non-scope",
    "References",
    "Dependencies",
    "Definition of done",
    "Verification",
    "Contract revision",
    "Milestone log",
)


class ContractError(OSError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class ArtifactIdentity(NamedTuple):
    path: str
    sha256: str


class SourceEntry(NamedTuple):
    path: bytes
    kind: bytes
    payload_length: int
    payload_digest: bytes


class CapabilityOutcome(NamedTuple):
    status: str
    outcome: str
    written_roles: frozenset[str]
    output_references: tuple[str, ...]
    detail: str | None = None


def _safe_segment(segment: str, label: str) -> str:
    if not SAFE_SEGMENT_RE.fullmatch(segment) or segment in {".", ".."}:
        raise ContractError("invalid_subject", f"unsafe {label}: {segment!r}")
    return segment


def receipt_subject_parts(subject: str) -> tuple[str, ...]:
    """Resolve a typed receipt subject into a collision-free directory path."""
    parts = PurePosixPath(subject).parts
    if not parts or PurePosixPath(subject).is_absolute():
        raise ContractError("invalid_subject", f"invalid subject: {subject!r}")
    expected = {"refinement": 2, "change": 2, "task": 3}
    subject_type = parts[0]
    if subject_type not in expected or len(parts) != expected[subject_type]:
        raise ContractError("invalid_subject", f"invalid typed subject: {subject!r}")
    return tuple(_safe_segment(part, "subject segment") for part in parts)


def artifact_identity(project_root: Path, artifact: Path) -> ArtifactIdentity:
    project_root = project_root.resolve()
    artifact = artifact.resolve(strict=True)
    try:
        relative = artifact.relative_to(project_root)
    except ValueError as error:
        raise ContractError("invalid_artifact", f"artifact escapes project: {artifact}") from error
    if not artifact.is_file():
        raise ContractError("invalid_artifact", f"artifact is not a file: {artifact}")
    return ArtifactIdentity(relative.as_posix(), hashlib.sha256(artifact.read_bytes()).hexdigest())


def artifact_identities(project_root: Path, artifacts: Iterable[Path]) -> tuple[ArtifactIdentity, ...]:
    identities = {artifact_identity(project_root, artifact) for artifact in artifacts}
    return tuple(sorted(identities, key=lambda identity: identity.path.encode("utf-8")))


def task_contract_identity(task_file: Path) -> str:
    """Hash stable task contract bytes while excluding the mutable Milestone log."""
    content = task_file.read_text(encoding="utf-8")
    stable = content.split("\n## Milestone log\n", 1)[0].rstrip() + "\n"
    return "sha256:" + hashlib.sha256(stable.encode("utf-8")).hexdigest()


def evidence_is_current(
    entry_contract_revision: str,
    entry_source_identity: str,
    current_contract_revision: str,
    current_source_identity: str,
) -> bool:
    return (
        entry_contract_revision == current_contract_revision
        and entry_source_identity == current_source_identity
    )


def _task_evidence_path(
    project_root: Path, task_root: Path, evidence_name: str
) -> Path:
    project = Path(project_root.absolute())
    if not project.is_dir():
        raise ValueError("project root must be an existing directory")
    candidate = task_root if task_root.is_absolute() else project / task_root
    candidate = Path(candidate.absolute())
    try:
        relative = candidate.relative_to(project)
    except ValueError as error:
        raise ValueError("task root escapes project") from error
    if any(part in {".", ".."} for part in relative.parts):
        raise ValueError("task root contains unsafe path traversal")
    current = project
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("task root traverses symbolic link")
    task_file = candidate / "task.md"
    if not candidate.is_dir() or not task_file.is_file() or task_file.is_symlink():
        raise ValueError("task root must contain a regular task.md")
    evidence_file = candidate / evidence_name
    if evidence_file.is_symlink():
        raise ValueError("evidence cannot be a symbolic link")
    return evidence_file


def append_task_evidence(
    project_root: Path,
    task_root: Path,
    *,
    role: str,
    evidence_id: str,
    contract_revision: str,
    source_identity: str,
    command: str,
    result: str,
    timestamp: str,
    finding: str | None = None,
) -> CapabilityOutcome:
    """Append one Development or Testing-owned immutable evidence entry."""
    if role not in {"Development", "Testing"}:
        return CapabilityOutcome("blocked", "invalid_evidence", frozenset(), ())
    testing = role == "Testing"
    if (
        not SAFE_SEGMENT_RE.fullmatch(evidence_id)
        or result not in {"passed", "failed"}
        or (testing and not finding)
    ):
        return CapabilityOutcome("blocked", "invalid_evidence", frozenset(), ())
    artifact_role = "testing-evidence" if testing else "development-evidence"
    try:
        evidence_file = _task_evidence_path(project_root, task_root, f"{artifact_role}.md")
    except (OSError, ValueError) as error:
        return CapabilityOutcome(
            "blocked", "invalid_evidence_path", frozenset(), (), str(error)
        )
    existing = evidence_file.read_text(encoding="utf-8") if evidence_file.exists() else ""
    if re.search(rf"^\| {re.escape(evidence_id)} \|", existing, re.MULTILINE):
        return CapabilityOutcome("blocked", "duplicate_evidence_id", frozenset(), ())
    if not existing:
        columns = [
            "Evidence ID", "Contract revision", "Source identity", "Check", "Result"
        ]
        if testing:
            columns.append("Finding")
        columns.append("Timestamp")
        existing = (
            f"# {role} evidence\n\nWriter authority: {role} only.\n\n"
            f"| {' | '.join(columns)} |\n|{'---|' * len(columns)}\n"
        )
    values = [
        evidence_id, f"`{contract_revision}`", f"`{source_identity}`",
        f"`{command}`", result,
    ]
    if testing:
        values.append(finding or "none")
    values.append(timestamp)
    evidence_file.write_text(existing + f"| {' | '.join(values)} |\n", encoding="utf-8")
    return CapabilityOutcome(
        "completed", "evidence-recorded", frozenset({artifact_role}),
        (evidence_file.as_posix(), evidence_id),
    )


def _git_visible_paths(project_root: Path) -> tuple[bytes, ...]:
    result = subprocess.run(
        [
            "git", "-C", os.fspath(project_root), "ls-files", "-z",
            "--cached", "--others", "--exclude-standard",
        ],
        check=True,
        capture_output=True,
    )
    return tuple(path for path in result.stdout.split(b"\0") if path)


def build_source_manifest(project_root: Path, excluded_roots: Iterable[str]) -> bytes:
    """Serialize the canonical USW-SOURCE-V1 full product tree manifest."""
    project_root = project_root.resolve()
    excluded = [(".git",), (".usw",)]
    for root in excluded_roots:
        parts = PurePosixPath(root.replace("\\", "/")).parts
        if not parts or PurePosixPath(root).is_absolute() or any(part in {".", ".."} for part in parts):
            raise ContractError("invalid_source_path", f"unsafe excluded root: {root!r}")
        excluded.append(parts)

    entries: list[SourceEntry] = []
    normalized_paths: dict[bytes, bytes] = {}
    for raw_path in _git_visible_paths(project_root):
        decoded = raw_path.decode("utf-8", "strict")
        original_parts = PurePosixPath(decoded).parts
        if (
            not original_parts
            or PurePosixPath(decoded).is_absolute()
            or any(part in {"", ".", ".."} for part in original_parts)
        ):
            raise ContractError("invalid_source_path", f"unsafe source path: {decoded!r}")
        if any(
            original_parts[: len(root_parts)] == root_parts
            for root_parts in excluded
        ):
            continue
        normalized = unicodedata.normalize("NFC", decoded).encode("utf-8")
        previous = normalized_paths.get(normalized)
        if previous is not None and previous != raw_path:
            raise ContractError("source_path_collision", f"normalized path collision: {decoded!r}")
        normalized_paths[normalized] = raw_path
        filesystem_path = os.fsencode(project_root) + b"/" + raw_path
        try:
            file_stat = os.lstat(filesystem_path)
        except FileNotFoundError:
            continue
        if os.path.islink(filesystem_path):
            kind = b"l"
            payload = os.readlink(filesystem_path)
            if isinstance(payload, str):
                payload = os.fsencode(payload)
        elif os.path.isfile(filesystem_path):
            kind = b"x" if file_stat.st_mode & 0o111 else b"f"
            with open(filesystem_path, "rb") as handle:
                payload = handle.read()
        else:
            raise ContractError("unsupported_source_kind", f"unsupported product entry: {decoded}")
        entries.append(SourceEntry(normalized, kind, len(payload), hashlib.sha256(payload).digest()))

    manifest = bytearray(b"USW-SOURCE-V1\0")
    for entry in sorted(entries, key=lambda item: item.path):
        manifest.extend(struct.pack(">I", len(entry.path)))
        manifest.extend(entry.path)
        manifest.extend(entry.kind)
        manifest.extend(struct.pack(">Q", entry.payload_length))
        manifest.extend(entry.payload_digest)
    return bytes(manifest)


def source_identity(project_root: Path, excluded_roots: Iterable[str]) -> str:
    manifest = build_source_manifest(project_root, excluded_roots)
    return "usw-source-v1:" + hashlib.sha256(manifest).hexdigest()


def reopen_task(
    tasks_file: Path,
    task_file: Path,
    *,
    task_id: str,
    finding_scope: str,
    contract_identity: str,
    source_identity_value: str,
    receipt_reference: str,
) -> str:
    """Reopen the same v1 task for an in-contract blocking finding."""
    if finding_scope != "in_scope":
        return "user_approval_required_for_new_task"
    index = tasks_file.read_text(encoding="utf-8")
    pattern = re.compile(rf"^- \[x\] {re.escape(task_id)} (?=\[)", re.MULTILINE)
    updated, count = pattern.subn(f"- [ ] {task_id} ", index, count=1)
    if count != 1:
        raise ContractError("task_not_complete", f"task {task_id} is not completed")
    contract = task_file.read_text(encoding="utf-8")
    if "\n## Milestone log\n" not in contract:
        raise ContractError("missing_milestone_log", f"task {task_id} is not a v1 contract")
    attempts = re.findall(r"^\| ([0-9]+) \|", contract, re.MULTILINE)
    attempt = max((int(value) for value in attempts), default=0) + 1
    row = (
        f"| {attempt} | blocking finding | `{contract_identity}` | "
        f"`{source_identity_value}` | reopened | {receipt_reference} |\n"
    )
    tasks_file.write_text(updated, encoding="utf-8")
    with task_file.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(row)
    return "reopened"


def _section(content: str, name: str) -> str:
    match = re.search(
        rf"^## {re.escape(name)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    return match.group("body") if match else ""


def _validate_completed_v1_task(
    task_id: str,
    task_file: Path,
    content: str,
    current_source_identity: str | None,
) -> None:
    if not current_source_identity or not SOURCE_ID_RE.fullmatch(current_source_identity):
        raise ContractError(
            "missing_current_source",
            f"completed v1 task {task_id} requires the current source identity",
        )
    revision_match = CONTRACT_REVISION_RE.search(content)
    if not revision_match:
        raise ContractError(
            "invalid_v1_task", f"completed v1 task {task_id} lacks a contract revision"
        )
    required_checks = tuple(
        re.findall(r"^- Run: `([^`]+)`$", _section(content, "Verification"), re.MULTILINE)
    )
    if not required_checks:
        raise ContractError(
            "invalid_v1_task", f"completed v1 task {task_id} has no mandatory checks"
        )
    evidence_file = task_file.with_name("development-evidence.md")
    if not evidence_file.is_file() or evidence_file.is_symlink():
        raise ContractError(
            "missing_development_evidence",
            f"completed v1 task {task_id} lacks regular Development evidence",
        )
    rows = tuple(EVIDENCE_ROW_RE.finditer(evidence_file.read_text(encoding="utf-8")))
    revision = revision_match.group("revision")
    for command in required_checks:
        if not any(
            row.group("contract") == revision
            and row.group("source") == current_source_identity
            and row.group("check") == command
            and row.group("result") == "passed"
            for row in rows
        ):
            raise ContractError(
                "stale_or_missing_development_evidence",
                f"completed v1 task {task_id} lacks current successful evidence for {command!r}",
            )


def validate_change_tasks(
    change_root: Path,
    frozen_legacy_ids: Iterable[str],
    *,
    current_source_identity: str | None = None,
) -> None:
    """Validate task links, models, required v1 sections, and checkbox ownership."""
    tasks_file = change_root / "tasks.md"
    tasks_content = tasks_file.read_text(encoding="utf-8")
    links = list(TASK_LINK_RE.finditer(tasks_content))
    checkbox_lines = tuple(CHECKBOX_RE.finditer(tasks_content))
    if len(links) != len(checkbox_lines):
        raise ContractError(
            "invalid_task_index",
            "every tasks.md checkbox must be a linked task with a stable ID",
        )
    ids = [match.group("id") for match in links]
    if len(ids) != len(set(ids)):
        raise ContractError("duplicate_task_id", "task IDs must be unique")
    frozen = set(frozen_legacy_ids)
    for markdown in change_root.rglob("*.md"):
        if markdown != tasks_file and CHECKBOX_RE.search(markdown.read_text(encoding="utf-8")):
            raise ContractError("checkbox_authority", f"checkbox outside tasks.md: {markdown}")
    for match in links:
        task_id = match.group("id")
        task_file = change_root / match.group("path")
        if not task_file.is_file():
            raise ContractError("missing_task", f"missing task contract: {task_file}")
        content = task_file.read_text(encoding="utf-8")
        model_match = MODEL_RE.search(content)
        if not model_match:
            raise ContractError("missing_artifact_model", f"task {task_id} has no model")
        model = model_match.group("model")
        if model == "legacy" and task_id not in frozen:
            raise ContractError("invalid_legacy_task", f"task {task_id} is not frozen legacy")
        if model == "v1":
            for section in REQUIRED_V1_SECTIONS:
                if f"## {section}" not in content:
                    raise ContractError("invalid_v1_task", f"task {task_id} lacks {section}")
            if task_id in frozen:
                raise ContractError("invalid_artifact_model", f"frozen task {task_id} must be legacy")
            if match.group("status").lower() == "x":
                _validate_completed_v1_task(
                    task_id, task_file, content, current_source_identity
                )


def _validate_receipt_fields(
    gate: str,
    owner_role: str,
    subject: str,
    reviewed_scope: str,
    reviewer: str,
    verdict: str,
    artifacts: tuple[Path, ...],
    artifact_model: str | None,
    contract_identity: str | None,
    source_identity: str | None,
    evidence_references: tuple[str, ...],
    findings: tuple[str, ...],
    sender: str | None,
    receiver: str | None,
) -> None:
    if gate not in {"internal", "transition"}:
        raise ContractError("invalid_receipt", f"unsupported gate: {gate}")
    if owner_role not in REVIEW_ROLES:
        raise ContractError("invalid_receipt", f"unsupported owner role: {owner_role}")
    if verdict not in REVIEW_VERDICTS:
        raise ContractError("invalid_receipt", f"unsupported verdict: {verdict}")
    if not reviewed_scope.strip() or not reviewer.strip():
        raise ContractError("invalid_receipt", "reviewed scope and reviewer are required")
    if not artifacts:
        raise ContractError("invalid_receipt", "review receipt requires reviewed artifacts")
    if verdict == "rejected" and not findings:
        raise ContractError("invalid_receipt", "rejected receipt requires findings")
    if gate == "internal" and (sender or receiver):
        raise ContractError("invalid_receipt", "internal receipt cannot contain sender/receiver")
    if gate == "transition" and not (sender and receiver):
        raise ContractError("invalid_receipt", "transition receipt requires sender and receiver")
    if gate == "transition" and (
        sender not in REVIEW_ROLES or receiver not in REVIEW_ROLES or owner_role != receiver
    ):
        raise ContractError(
            "invalid_receipt",
            "transition receipt must be owned by a supported receiving role",
        )
    is_task = receipt_subject_parts(subject)[0] == "task"
    if not is_task:
        if artifact_model or contract_identity or source_identity:
            raise ContractError(
                "invalid_receipt", "non-task receipt cannot contain task-specific fields"
            )
        return
    if artifact_model not in {"legacy", "v1"} or not contract_identity:
        raise ContractError("invalid_receipt", "task receipt requires model and contract identity")
    task_files = tuple(path for path in artifacts if path.name == "task.md")
    if len(task_files) != 1:
        raise ContractError(
            "invalid_receipt", "task receipt requires exactly one reviewed task.md"
        )
    task_file = task_files[0].resolve(strict=True)
    task_content = task_file.read_text(encoding="utf-8")
    if artifact_model == "v1" and (not source_identity or not evidence_references):
        raise ContractError("invalid_receipt", "v1 task receipt requires source and evidence IDs")
    if artifact_model == "v1":
        revision = CONTRACT_REVISION_RE.search(task_content)
        if not revision or contract_identity != revision.group("revision"):
            raise ContractError(
                "invalid_receipt", "v1 receipt contract identity does not match task.md"
            )
        if not SOURCE_ID_RE.fullmatch(source_identity or ""):
            raise ContractError("invalid_receipt", "invalid v1 product source identity")
        evidence_rows = []
        for artifact in artifacts:
            if artifact.name in {"development-evidence.md", "testing-evidence.md"}:
                evidence_rows.extend(
                    EVIDENCE_ROW_RE.finditer(artifact.read_text(encoding="utf-8"))
                )
        for evidence_id in evidence_references:
            matching = [row for row in evidence_rows if row.group("id") == evidence_id]
            if not matching or not any(
                row.group("contract") == contract_identity
                and row.group("source") == source_identity
                and (verdict != "accepted" or row.group("result") == "passed")
                for row in matching
            ):
                raise ContractError(
                    "invalid_receipt",
                    f"evidence {evidence_id!r} is absent or stale for the reviewed task",
                )
    if artifact_model == "legacy" and (source_identity or not evidence_references):
        raise ContractError(
            "invalid_receipt",
            "legacy task receipt requires observed verification and no v1 source identity",
        )
    if artifact_model == "legacy":
        expected = "sha256:" + hashlib.sha256(task_file.read_bytes()).hexdigest()
        if contract_identity != expected:
            raise ContractError(
                "invalid_receipt", "legacy contract identity does not match task.md"
            )


def _ensure_project_directory(project_root: Path, directory: Path) -> None:
    """Create a project-local directory without following symbolic links."""
    project_root = project_root.resolve()
    absolute = (directory if directory.is_absolute() else project_root / directory).resolve(
        strict=False
    )
    try:
        relative = absolute.relative_to(project_root)
    except ValueError as error:
        raise ContractError("invalid_review_root", f"review root escapes project: {directory}") from error
    current = project_root
    for part in relative.parts:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            os.mkdir(current)
            continue
        if os.path.islink(current):
            raise ContractError("invalid_review_root", f"review root traverses symlink: {current}")
        if not os.path.isdir(current):
            raise ContractError("invalid_review_root", f"review root traverses non-directory: {current}")


def write_receipt(
    project_root: Path,
    review_root: Path,
    *,
    receipt_id: str,
    gate: str,
    owner_role: str,
    subject: str,
    reviewed_scope: str,
    reviewer: str,
    verdict: str,
    artifacts: Iterable[Path],
    artifact_model: str | None = None,
    contract_identity: str | None = None,
    source_identity: str | None = None,
    evidence_references: Iterable[str] = (),
    previous: str = "none",
    findings: Iterable[str] = (),
    sender: str | None = None,
    receiver: str | None = None,
    timestamp: datetime | None = None,
) -> Path:
    """Create one immutable reviewer-owned receipt."""
    _safe_segment(receipt_id, "receipt ID")
    artifact_paths = tuple(artifacts)
    evidence = tuple(evidence_references)
    finding_references = tuple(findings)
    _validate_receipt_fields(
        gate,
        owner_role,
        subject,
        reviewed_scope,
        reviewer,
        verdict,
        artifact_paths,
        artifact_model,
        contract_identity,
        source_identity,
        evidence,
        finding_references,
        sender,
        receiver,
    )
    identities = artifact_identities(project_root, artifact_paths)
    created_at = timestamp or datetime.now(timezone.utc)
    lines = [
        f"# Review receipt: {receipt_id}",
        "",
        f"- Gate: `{gate}`",
        f"- Owner role: `{owner_role}`",
        f"- Subject: `{subject}`",
        f"- Reviewed scope: {reviewed_scope}",
        f"- Previous attempt or receipt: {previous}",
        f"- Reviewer: {reviewer}",
        f"- Verdict: `{verdict}`",
        f"- Timestamp: {created_at.isoformat(timespec='seconds')}",
    ]
    if artifact_model:
        lines.append(f"- Artifact model: `{artifact_model}`")
    if contract_identity:
        lines.append(f"- Contract identity: `{contract_identity}`")
    if source_identity:
        lines.append(f"- Product source identity: `{source_identity}`")
    lines.append("- Evidence IDs or observed verification: " + (", ".join(evidence) or "none"))
    lines.append("- Findings: " + (", ".join(finding_references) or "none"))
    if gate == "transition":
        lines.extend((f"- Sender: `{sender}`", f"- Receiver: `{receiver}`"))
    lines.extend(("", "## Reviewed artifact identities", "", "| Path | SHA-256 |", "|---|---|"))
    lines.extend(f"| `{identity.path}` | `{identity.sha256}` |" for identity in identities)
    content = "\n".join(lines) + "\n"

    destination = review_root.joinpath(*receipt_subject_parts(subject), f"{receipt_id}.md")
    _ensure_project_directory(project_root, destination.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(destination, flags, 0o644)
    except FileExistsError as error:
        raise ContractError("immutable_receipt", f"receipt already exists: {destination}") from error
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return destination


def receipt_is_current(project_root: Path, receipt: Path) -> bool:
    """Return whether every planning artifact still matches the receipt digest."""
    content = receipt.read_text(encoding="utf-8")
    rows = re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", content, re.MULTILINE)
    if not rows:
        return False
    for relative, expected in rows:
        artifact = project_root / relative
        if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != expected:
            return False
    return True
