#!/usr/bin/env python3
"""Validate, checkpoint, and reconcile developer-local USW handoffs."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import runpy
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, Literal


ACTIVE_STATUSES = {"in_progress", "paused", "blocked"}
ACTIVE_SECTIONS = (
    "Done",
    "Changed areas",
    "Verification",
    "Risks / blockers",
    "Next action",
    "References",
)
SOURCE_SECTION = "Source snapshot"
SOURCE_SCHEMA = "usw-source-v1"
_DIGEST_PREFIX = "sha256:"
_HASH_CHUNK_SIZE = 1024 * 1024
_HASH_RETRIES = 2
_RESERVED_EXACT_PATHS = {b".usw/HANDOFF.md", b".usw/HANDOFF.next.md"}
V1_METADATA_HEADER = "| Subject | Role | Attempt | Current operation | Status | Updated |"
SKILLS_ROOT = Path(__file__).parents[2]
CONFIG = SimpleNamespace(**runpy.run_path(str(
    SKILLS_ROOT / "usw-initialize-project/scripts/init_usw.py"
)))
CONTRACT = SimpleNamespace(**runpy.run_path(str(
    SKILLS_ROOT / "usw-initialize-project/scripts/artifact_contract.py"
)))


class HandoffError(ValueError):
    """Raised when developer-local handoff state is invalid."""


class SnapshotUnavailable(Exception):
    """Expected operational inability to produce a reliable snapshot."""


@dataclass(frozen=True)
class SourceSnapshot:
    schema: str
    state: Literal["complete", "unavailable"]
    branch: str | None
    head: str | None
    index_digest: str | None
    tracked_filesystem_digest: str | None
    untracked_filesystem_digest: str | None
    submodules_digest: str | None
    source_digest: str | None
    problem: str | None


@dataclass(frozen=True)
class DriftReport:
    freshness: Literal["fresh", "stale", "unknown"]
    branch_changed: bool | None
    changed_components: tuple[str, ...]
    reason: str | None


@dataclass(frozen=True)
class _IndexRecord:
    mode: bytes
    oid: bytes
    stage: int
    path: bytes


@dataclass(frozen=True)
class _GitState:
    head: str
    branch: str | None
    index_records: tuple[_IndexRecord, ...]
    intent_to_add: frozenset[bytes]
    tracked_paths: tuple[bytes, ...]
    untracked_paths: tuple[bytes, ...]


def find_project_root(start: Path) -> Path:
    """Return the nearest Git root, or the supplied directory if none exists."""
    start = start.expanduser().resolve()
    if not start.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {start}")

    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def handoff_path(project: Path) -> Path:
    """Return the initialized handoff path for a project."""
    return find_project_root(project) / ".usw" / "HANDOFF.md"


def _canonical_product_identity(project: Path) -> str:
    project_root = CONFIG.find_project_root(project)
    config = CONFIG.load_config(project_root)
    return CONTRACT.source_identity(
        project_root, tuple(config.managed_roots.values())
    )


def render_idle(updated_at: datetime | None = None) -> str:
    """Render an idle developer-local handoff."""
    timestamp = updated_at or datetime.now(timezone.utc)
    return (
        "# Developer Handoff\n\n"
        f"- Updated: {timestamp.isoformat(timespec='seconds')}\n"
        "- Status: idle\n\n"
        "## Active work\n\n"
        "No active work.\n"
    )


def render_v1_idle(updated_at: datetime | None = None) -> str:
    return CONFIG.render_handoff(updated_at)


def _v1_table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _validate_v1_handoff(content: str) -> str:
    lines = content.splitlines()
    try:
        header_index = lines.index(V1_METADATA_HEADER)
    except ValueError as error:
        raise HandoffError("Missing v1 handoff metadata table") from error
    if header_index + 2 >= len(lines):
        raise HandoffError("Incomplete v1 handoff metadata table")
    values = _v1_table_cells(lines[header_index + 2])
    if len(values) != 6:
        raise HandoffError("V1 metadata row must contain six fields")
    subject, role, attempt, operation, status, updated = values
    if status not in {*ACTIVE_STATUSES, "idle"}:
        raise HandoffError(f"Unsupported Status '{status}'")
    _validate_timestamp(updated)
    if status == "idle":
        if (subject, role, attempt, operation) != ("none", "none", "none", "none"):
            raise HandoffError("Idle v1 handoff must not name active work")
    else:
        if not re.fullmatch(r"(?:refinement|change)/[^/]+|task/[^/]+/[^/]+", subject):
            raise HandoffError("Active v1 handoff requires a typed Subject")
        if role not in {"Analysis", "Development", "Testing"}:
            raise HandoffError("Active v1 handoff requires a role")
        if not attempt or not operation:
            raise HandoffError("Active v1 handoff requires attempt and operation")
    order, sections = _sections(lines)
    expected = [
        "Session journal", "Verification", "Next action", "References",
        "Trusted source snapshot",
    ]
    if order != expected:
        raise HandoffError("V1 checkpoint sections must appear in normative order")
    if len(sections["Next action"]) != 1:
        raise HandoffError("Next action must contain exactly one non-empty line")
    if not sections["Session journal"] or not sections["Verification"]:
        raise HandoffError("V1 checkpoint tables must not be empty")
    identity = [line for line in sections["Trusted source snapshot"] if line.startswith("- Identity: ")]
    freshness = [line for line in sections["Trusted source snapshot"] if line.startswith("- Freshness: ")]
    if len(identity) != 1 or len(freshness) != 1:
        raise HandoffError("Trusted source snapshot requires identity and freshness")
    return status


def _metadata(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.startswith("## "):
            break
        if not line.startswith("- ") or ": " not in line:
            continue
        key, value = line[2:].split(": ", 1)
        if key in values:
            raise HandoffError(f"Duplicate metadata field: {key}")
        values[key] = value.strip()
    return values


def _validate_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise HandoffError("Updated must be an ISO 8601 timestamp") from error
    if parsed.tzinfo is None:
        raise HandoffError("Updated timestamp must include a timezone")


def _sections(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    order: list[str] = []
    content: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        if line.startswith("## "):
            current = line[3:].strip()
            if current in content:
                raise HandoffError(f"Duplicate section: {current}")
            order.append(current)
            content[current] = []
        elif current is not None and line.strip():
            content[current].append(line.strip())
    return order, content


def _source_section_fields(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in lines:
        if not line.startswith("- ") or ": " not in line:
            raise HandoffError("Source snapshot fields must be bullets")
        key, value = line[2:].split(": ", 1)
        if key in fields:
            raise HandoffError(f"Duplicate Source snapshot field: {key}")
        if not value.strip():
            raise HandoffError(f"Source snapshot field '{key}' must not be empty")
        fields[key] = value.strip()
    return fields


def validate_handoff(content: str) -> str:
    """Validate the Markdown envelope and return its status.

    A source section, when present, is expected last. Its v1 field semantics are
    checked separately when reading stored state, because a candidate-supplied
    section is deliberately discarded before save.
    """
    lines = content.splitlines()
    if not lines or lines[0] != "# Developer Handoff":
        raise HandoffError("Expected '# Developer Handoff' as the first line")
    if any(line.startswith("# ") for line in lines[1:]):
        raise HandoffError("Handoff must contain exactly one top-level heading")
    if V1_METADATA_HEADER in lines:
        return _validate_v1_handoff(content)
    metadata = _metadata(lines)
    required_metadata = {"Updated", "Status"}
    missing_metadata = required_metadata - metadata.keys()
    if missing_metadata:
        missing = ", ".join(sorted(missing_metadata))
        raise HandoffError(f"Missing metadata: {missing}")
    _validate_timestamp(metadata["Updated"])

    status = metadata["Status"]
    order, sections = _sections(lines)
    if status == "idle":
        if set(metadata) != required_metadata:
            raise HandoffError("Idle handoff may contain only Updated and Status")
        if order != ["Active work"]:
            raise HandoffError("Idle handoff must contain only 'Active work'")
        if sections["Active work"] != ["No active work."]:
            raise HandoffError("Idle handoff must say 'No active work.'")
        return status

    if status not in ACTIVE_STATUSES:
        allowed = ", ".join(sorted((*ACTIVE_STATUSES, "idle")))
        raise HandoffError(f"Unsupported Status '{status}'; expected one of: {allowed}")
    if not metadata.get("Task"):
        raise HandoffError("Active handoff requires a non-empty Task")
    if set(metadata) != {"Updated", "Status", "Task"}:
        raise HandoffError("Active handoff metadata must be Updated, Status, and Task")

    expected = list(ACTIVE_SECTIONS)
    expected_with_source = [*expected, SOURCE_SECTION]
    if order not in (expected, expected_with_source):
        rendered = ", ".join(expected_with_source)
        raise HandoffError(f"Active sections must appear exactly in order: {rendered}")
    for section in ACTIVE_SECTIONS:
        if not sections[section]:
            raise HandoffError(f"Section '{section}' must not be empty")
    if SOURCE_SECTION in sections and not sections[SOURCE_SECTION]:
        raise HandoffError("Source snapshot must not be empty")
    if len(sections["Next action"]) != 1:
        raise HandoffError("Next action must contain exactly one non-empty line")
    for section in ACTIVE_SECTIONS:
        if section == "Next action":
            continue
        if any(not line.startswith("- ") for line in sections[section]):
            raise HandoffError(f"Section '{section}' must contain a bullet list")
    for result in sections["Verification"]:
        if result == "- Not run.":
            continue
        if not (result.endswith(" -> passed") or result.endswith(" -> failed")):
            raise HandoffError(
                "Verification entries must end with '-> passed' or '-> failed'"
            )
    return status


def _strip_candidate_snapshot(content: str) -> str:
    """Remove one candidate-supplied snapshot without interpreting its fields."""
    lines = content.splitlines(keepends=True)
    source_indices = [
        index
        for index, line in enumerate(lines)
        if line.startswith("## ") and line[3:].strip() == SOURCE_SECTION
    ]
    if len(source_indices) > 1:
        raise HandoffError("Duplicate section: Source snapshot")
    if not source_indices:
        return content

    source_start = source_indices[0]
    source_end = len(lines)
    for index in range(source_start + 1, len(lines)):
        if lines[index].startswith("## "):
            source_end = index
            break
    return "".join([*lines[:source_start], *lines[source_end:]])


def _unquote_snapshot_value(value: str, field: str) -> str:
    if len(value) < 2 or not (value.startswith("`") and value.endswith("`")):
        raise HandoffError(f"Source snapshot field '{field}' must use backticks")
    return value[1:-1]


def _valid_oid(value: str) -> bool:
    return len(value) in (40, 64) and all(char in "0123456789abcdef" for char in value)


def _parse_v1_snapshot(lines: list[str]) -> SourceSnapshot:
    fields = _source_section_fields(lines)
    state = fields.get("State")
    if state == "complete":
        required = (
            "Schema",
            "State",
            "Branch",
            "HEAD",
            "Index",
            "Tracked filesystem",
            "Untracked filesystem",
            "Submodules",
            "Source",
        )
        if tuple(fields) != required:
            raise HandoffError("Malformed usw-source-v1 complete snapshot")
        branch_value = fields["Branch"]
        branch = (
            None
            if branch_value == "detached"
            else _unquote_snapshot_value(branch_value, "Branch")
        )
        if branch is not None and not branch.startswith("refs/"):
            raise HandoffError("Source snapshot Branch must be a Git ref or detached")
        head = _unquote_snapshot_value(fields["HEAD"], "HEAD")
        if head != "unborn" and not _valid_oid(head):
            raise HandoffError("Source snapshot HEAD must be an object ID or unborn")
        digests: list[str] = []
        for field in (
            "Index",
            "Tracked filesystem",
            "Untracked filesystem",
            "Submodules",
            "Source",
        ):
            digest = _unquote_snapshot_value(fields[field], field)
            if not _valid_digest(digest):
                raise HandoffError(f"Source snapshot {field} must be a SHA-256 digest")
            digests.append(digest)
        return SourceSnapshot(
            schema=SOURCE_SCHEMA,
            state="complete",
            branch=branch,
            head=head,
            index_digest=digests[0],
            tracked_filesystem_digest=digests[1],
            untracked_filesystem_digest=digests[2],
            submodules_digest=digests[3],
            source_digest=digests[4],
            problem=None,
        )

    if state == "unavailable":
        required = ("Schema", "State", "Branch", "HEAD", "Source", "Problem")
        if tuple(fields) != required:
            raise HandoffError("Malformed usw-source-v1 unavailable snapshot")
        branch = None
        if fields["Branch"] != "detached":
            branch = _unquote_snapshot_value(fields["Branch"], "Branch")
            if not branch.startswith("refs/"):
                raise HandoffError("Source snapshot Branch must be a Git ref or detached")
        head_value = fields["HEAD"]
        if head_value == "unavailable":
            head = None
        else:
            head = _unquote_snapshot_value(head_value, "HEAD")
            if head != "unborn" and not _valid_oid(head):
                raise HandoffError("Source snapshot HEAD must be an object ID or unborn")
        if fields["Source"] != "unavailable":
            raise HandoffError("Unavailable Source snapshot must set Source to unavailable")
        return SourceSnapshot(
            schema=SOURCE_SCHEMA,
            state="unavailable",
            branch=branch,
            head=head,
            index_digest=None,
            tracked_filesystem_digest=None,
            untracked_filesystem_digest=None,
            submodules_digest=None,
            source_digest=None,
            problem=fields["Problem"],
        )
    raise HandoffError("Source snapshot State must be complete or unavailable")


def source_snapshot_from_handoff(content: str) -> SourceSnapshot | None:
    """Return the stored snapshot, rejecting malformed known-v1 state."""
    lines = content.splitlines()
    order, sections = _sections(lines)
    if SOURCE_SECTION not in sections:
        return None
    if not sections[SOURCE_SECTION]:
        raise HandoffError("Source snapshot must not be empty")
    fields = _source_section_fields(sections[SOURCE_SECTION])
    schema_value = fields.get("Schema")
    if schema_value is None:
        raise HandoffError("Source snapshot requires Schema")
    schema = _unquote_snapshot_value(schema_value, "Schema")
    if schema != SOURCE_SCHEMA:
        return SourceSnapshot(
            schema=schema,
            state="unavailable",
            branch=None,
            head=None,
            index_digest=None,
            tracked_filesystem_digest=None,
            untracked_filesystem_digest=None,
            submodules_digest=None,
            source_digest=None,
            problem="unsupported schema",
        )
    return _parse_v1_snapshot(sections[SOURCE_SECTION])


def _valid_digest(value: str) -> bool:
    return value.startswith(_DIGEST_PREFIX) and len(value) == len(_DIGEST_PREFIX) + 64 and all(
        char in "0123456789abcdef" for char in value[len(_DIGEST_PREFIX) :]
    )


def render_source_snapshot(snapshot: SourceSnapshot) -> str:
    """Render a compact, script-generated source snapshot section."""
    if snapshot.schema != SOURCE_SCHEMA:
        raise HandoffError(f"Cannot render unsupported source schema: {snapshot.schema}")
    branch = f"`{snapshot.branch}`" if snapshot.branch is not None else "detached"
    head = f"`{snapshot.head}`" if snapshot.head is not None else "unavailable"
    prefix = (
        "## Source snapshot\n\n"
        f"- Schema: `{snapshot.schema}`\n"
        f"- State: {snapshot.state}\n"
        f"- Branch: {branch}\n"
        f"- HEAD: {head}\n"
    )
    if snapshot.state == "unavailable":
        return (
            prefix
            + "- Source: unavailable\n"
            f"- Problem: {snapshot.problem or 'source capture unavailable'}\n"
        )
    components = (
        ("Index", snapshot.index_digest),
        ("Tracked filesystem", snapshot.tracked_filesystem_digest),
        ("Untracked filesystem", snapshot.untracked_filesystem_digest),
        ("Submodules", snapshot.submodules_digest),
        ("Source", snapshot.source_digest),
    )
    if any(value is None for _, value in components):
        raise HandoffError("Complete Source snapshot is missing a component digest")
    return prefix + "".join(f"- {name}: `{value}`\n" for name, value in components)


def _git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name in {
            "GIT_DIR",
            "GIT_WORK_TREE",
            "GIT_INDEX_FILE",
            "GIT_COMMON_DIR",
            "GIT_CONFIG",
            "GIT_CONFIG_PARAMETERS",
        } or name.startswith("GIT_CONFIG_"):
            environment.pop(name, None)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    return environment


def _run_git(
    project: Path,
    *arguments: str,
    acceptable_returncodes: frozenset[int] = frozenset({0}),
) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            ["git", "-C", str(project), "-c", "core.fsmonitor=false", *arguments],
            check=False,
            capture_output=True,
            env=_git_environment(),
        )
    except OSError as error:
        raise SnapshotUnavailable(f"could not run Git: {error.strerror or error}") from error
    if result.returncode not in acceptable_returncodes:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise SnapshotUnavailable(f"Git capture failed: {message or 'unexpected exit status'}")
    return result


def _git_project_root(project: Path) -> Path | None:
    project = project.expanduser().resolve()
    if not project.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {project}")
    result = _run_git(
        project,
        "rev-parse",
        "--show-toplevel",
        acceptable_returncodes=frozenset({0, 128}),
    )
    if result.returncode == 128:
        return None
    root = result.stdout.decode("utf-8", "surrogateescape").strip()
    if not root:
        raise SnapshotUnavailable("Git did not report a worktree root")
    return Path(root).resolve()


def _parse_index_records(output: bytes) -> tuple[_IndexRecord, ...]:
    records: list[_IndexRecord] = []
    for entry in output.split(b"\0"):
        if not entry:
            continue
        try:
            header, path = entry.split(b"\t", 1)
            mode, oid, stage_raw = header.split(b" ")
            stage = int(stage_raw)
        except (ValueError, UnicodeError) as error:
            raise HandoffError("Could not parse git ls-files --stage output") from error
        if not path or stage not in (0, 1, 2, 3):
            raise HandoffError("Unsupported index entry in git ls-files output")
        if len(mode) != 6 or not mode.isdigit() or not oid:
            raise HandoffError("Malformed index entry in git ls-files output")
        _validate_git_path(path)
        records.append(_IndexRecord(mode=mode, oid=oid, stage=stage, path=path))
    return tuple(sorted(records, key=lambda record: (record.path, record.stage, record.mode, record.oid)))


def _intent_to_add_paths(project: Path) -> frozenset[bytes]:
    output = _run_git(
        project,
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=no",
    ).stdout
    paths: set[bytes] = set()
    for entry in output.split(b"\0"):
        if not entry or not entry.startswith(b"1 "):
            continue
        fields = entry.split(b" ", 8)
        if len(fields) != 9:
            raise HandoffError("Could not parse Git porcelain v2 output")
        xy, index_oid, path = fields[1], fields[7], fields[8]
        if xy == b".A":
            if not index_oid or any(byte != ord("0") for byte in index_oid):
                raise SnapshotUnavailable("unsupported intent-to-add status record")
            _validate_git_path(path)
            paths.add(path)
    return frozenset(paths)


def _untracked_paths(project: Path) -> tuple[bytes, ...]:
    output = _run_git(project, "ls-files", "--others", "--exclude-standard", "-z").stdout
    paths = {path for path in output.split(b"\0") if path and not _reserved_path(path)}
    for path in paths:
        _validate_git_path(path)
    return tuple(sorted(paths))


def _head_and_branch(project: Path) -> tuple[str, str | None]:
    head_result = _run_git(
        project,
        "rev-parse",
        "--verify",
        "-q",
        "HEAD",
        acceptable_returncodes=frozenset({0, 1, 128}),
    )
    if head_result.returncode == 0:
        head = head_result.stdout.decode("ascii", "strict").strip()
        if not _valid_oid(head):
            raise HandoffError("Git returned an invalid HEAD object ID")
    else:
        head = "unborn"
    branch_result = _run_git(
        project,
        "symbolic-ref",
        "-q",
        "HEAD",
        acceptable_returncodes=frozenset({0, 1}),
    )
    if branch_result.returncode == 0:
        branch = branch_result.stdout.decode("utf-8", "surrogateescape").strip()
        if not branch.startswith("refs/"):
            raise HandoffError("Git returned an invalid symbolic HEAD ref")
    else:
        branch = None
    return head, branch


def _capture_git_state(project: Path) -> _GitState:
    head, branch = _head_and_branch(project)
    index_records = _parse_index_records(
        _run_git(project, "ls-files", "--stage", "-z").stdout
    )
    intents = _intent_to_add_paths(project)
    tracked_paths = tuple(
        sorted({record.path for record in index_records if not _reserved_path(record.path)})
    )
    return _GitState(
        head=head,
        branch=branch,
        index_records=index_records,
        intent_to_add=intents,
        tracked_paths=tracked_paths,
        untracked_paths=_untracked_paths(project),
    )


def _validate_git_path(path: bytes) -> None:
    parts = path.split(b"/")
    if path.startswith(b"/") or not path or any(part in (b"", b".", b"..") for part in parts):
        raise HandoffError("Unsupported Git path in source snapshot")


def _reserved_path(path: bytes) -> bool:
    if path in _RESERVED_EXACT_PATHS:
        return True
    return path.startswith(b".usw/.HANDOFF.md.") and path.endswith(b".tmp")


def _encode_parts(*parts: bytes) -> bytes:
    encoded = bytearray()
    for part in parts:
        encoded.extend(len(part).to_bytes(8, "big"))
        encoded.extend(part)
    return bytes(encoded)


def _digest_records(records: Iterable[tuple[bytes, bytes]]) -> str:
    digest = hashlib.sha256()
    for tag, payload in sorted(records):
        digest.update(_encode_parts(tag, payload))
    return f"{_DIGEST_PREFIX}{digest.hexdigest()}"


def _index_digest(state: _GitState) -> str:
    records: list[tuple[bytes, bytes]] = []
    for record in state.index_records:
        if _reserved_path(record.path):
            continue
        records.append(
            (
                b"index-entry",
                _encode_parts(
                    record.mode,
                    record.oid,
                    str(record.stage).encode("ascii"),
                    record.path,
                ),
            )
        )
    records.extend(
        (b"intent-to-add", _encode_parts(path))
        for path in state.intent_to_add
        if not _reserved_path(path)
    )
    return _digest_records(records)


def _stable_stat(stat_result: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        stat_result.st_mode,
        stat_result.st_dev,
        stat_result.st_ino,
        stat_result.st_size,
        stat_result.st_mtime_ns,
        stat_result.st_ctime_ns,
        stat_result.st_nlink,
    )


def _hash_regular_file(path: bytes, before: os.stat_result) -> str | None:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except (FileNotFoundError, PermissionError, OSError):
        return None
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or _stable_stat(opened) != _stable_stat(before):
            return None
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, _HASH_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
        after_open = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after_path = os.lstat(path)
    except OSError:
        return None
    if _stable_stat(after_open) != _stable_stat(before) or _stable_stat(after_path) != _stable_stat(before):
        return None
    return digest.hexdigest()


def _physical_record(root: Path, raw_path: bytes) -> bytes:
    path = os.path.join(os.fsencode(root), raw_path)
    for _ in range(_HASH_RETRIES):
        try:
            before = os.lstat(path)
        except FileNotFoundError:
            try:
                os.lstat(path)
            except FileNotFoundError:
                return _encode_parts(raw_path, b"missing")
            continue
        except PermissionError as error:
            raise SnapshotUnavailable(f"unreadable path: {os.fsdecode(raw_path)}") from error

        if stat.S_ISREG(before.st_mode):
            digest = _hash_regular_file(path, before)
            if digest is not None:
                kind = b"executable" if before.st_mode & 0o111 else b"regular"
                return _encode_parts(
                    raw_path,
                    kind,
                    oct(stat.S_IMODE(before.st_mode)).encode("ascii"),
                    digest.encode("ascii"),
                )
            continue
        if stat.S_ISLNK(before.st_mode):
            try:
                target = os.readlink(path)
                after = os.lstat(path)
            except (FileNotFoundError, PermissionError, OSError):
                continue
            if _stable_stat(before) == _stable_stat(after):
                return _encode_parts(
                    raw_path,
                    b"symlink",
                    oct(stat.S_IMODE(before.st_mode)).encode("ascii"),
                    hashlib.sha256(target).hexdigest().encode("ascii"),
                )
            continue
        raise SnapshotUnavailable(f"unsupported filesystem object: {os.fsdecode(raw_path)}")
    raise SnapshotUnavailable(f"file changed while snapshot was being computed: {os.fsdecode(raw_path)}")


def _filesystem_digest(root: Path, paths: Iterable[bytes], component: bytes) -> str:
    return _digest_records(
        (component, _physical_record(root, path)) for path in sorted(set(paths))
    )


def _submodules_digest(
    project: Path,
    index_records: Iterable[_IndexRecord],
    ancestors: frozenset[Path],
) -> str:
    records: list[tuple[bytes, bytes]] = []
    gitlinks = sorted(
        (
            record
            for record in index_records
            if record.stage == 0 and record.mode == b"160000" and not _reserved_path(record.path)
        ),
        key=lambda record: record.path,
    )
    for gitlink in gitlinks:
        path = os.path.join(os.fsencode(project), gitlink.path)
        try:
            path_stat = os.lstat(path)
        except FileNotFoundError:
            records.append((b"submodule", _encode_parts(gitlink.path, gitlink.oid, b"missing")))
            continue
        except PermissionError as error:
            raise SnapshotUnavailable(f"unreadable submodule: {os.fsdecode(gitlink.path)}") from error
        if not stat.S_ISDIR(path_stat.st_mode):
            raise SnapshotUnavailable(f"invalid submodule filesystem object: {os.fsdecode(gitlink.path)}")
        submodule_path = Path(os.fsdecode(path))
        child_root = _git_project_root(submodule_path)
        if child_root is None:
            if (submodule_path / ".git").exists():
                raise SnapshotUnavailable(f"invalid submodule: {os.fsdecode(gitlink.path)}")
            records.append(
                (b"submodule", _encode_parts(gitlink.path, gitlink.oid, b"uninitialized"))
            )
            continue
        if child_root in ancestors:
            raise SnapshotUnavailable(f"recursive submodule cycle: {os.fsdecode(gitlink.path)}")
        child = _capture_complete(child_root, ancestors | {child_root})
        records.append(
            (
                b"submodule",
                _encode_parts(
                    gitlink.path,
                    gitlink.oid,
                    b"complete",
                    (child.source_digest or "").encode("ascii"),
                ),
            )
        )
    return _digest_records(records)


def _same_capture_state(first: _GitState, second: _GitState) -> bool:
    return (
        first.head == second.head
        and first.index_records == second.index_records
        and first.intent_to_add == second.intent_to_add
        and first.tracked_paths == second.tracked_paths
        and first.untracked_paths == second.untracked_paths
    )


def _capture_complete(project: Path, ancestors: frozenset[Path]) -> SourceSnapshot:
    before = _capture_git_state(project)
    index_digest = _index_digest(before)
    tracked_paths = [
        path
        for path in before.tracked_paths
        if not any(
            record.path == path and record.mode == b"160000"
            for record in before.index_records
        )
    ]
    tracked_digest = _filesystem_digest(project, tracked_paths, b"tracked")
    untracked_digest = _filesystem_digest(
        project,
        before.untracked_paths,
        b"untracked",
    )
    submodules_digest = _submodules_digest(project, before.index_records, ancestors)
    after = _capture_git_state(project)
    if not _same_capture_state(before, after):
        raise SnapshotUnavailable("HEAD, index, or path state changed during source capture")

    source_digest = _digest_records(
        (
            (b"schema", SOURCE_SCHEMA.encode("ascii")),
            (b"head", before.head.encode("ascii")),
            (b"index", index_digest.encode("ascii")),
            (b"tracked-filesystem", tracked_digest.encode("ascii")),
            (b"untracked-filesystem", untracked_digest.encode("ascii")),
            (b"submodules", submodules_digest.encode("ascii")),
        )
    )
    return SourceSnapshot(
        schema=SOURCE_SCHEMA,
        state="complete",
        branch=after.branch,
        head=before.head,
        index_digest=index_digest,
        tracked_filesystem_digest=tracked_digest,
        untracked_filesystem_digest=untracked_digest,
        submodules_digest=submodules_digest,
        source_digest=source_digest,
        problem=None,
    )


def capture_source_snapshot(project: Path) -> SourceSnapshot:
    """Capture a read-only full physical source manifest for a Git worktree."""
    try:
        root = _git_project_root(project)
        if root is None:
            raise SnapshotUnavailable("not a Git worktree")
        return _capture_complete(root, frozenset({root}))
    except SnapshotUnavailable as error:
        return SourceSnapshot(
            schema=SOURCE_SCHEMA,
            state="unavailable",
            branch=None,
            head=None,
            index_digest=None,
            tracked_filesystem_digest=None,
            untracked_filesystem_digest=None,
            submodules_digest=None,
            source_digest=None,
            problem=str(error),
        )
    except (PermissionError, OSError) as error:
        return SourceSnapshot(
            schema=SOURCE_SCHEMA,
            state="unavailable",
            branch=None,
            head=None,
            index_digest=None,
            tracked_filesystem_digest=None,
            untracked_filesystem_digest=None,
            submodules_digest=None,
            source_digest=None,
            problem=str(error),
        )


def compare_source_snapshots(
    saved: SourceSnapshot | None,
    current: SourceSnapshot,
) -> DriftReport:
    """Classify checkpoint freshness without treating branch as source identity."""
    if saved is None:
        return DriftReport("unknown", None, (), "saved snapshot missing")
    if saved.schema != SOURCE_SCHEMA:
        return DriftReport("unknown", None, (), "unsupported schema")
    if saved.state != "complete":
        return DriftReport("unknown", None, (), "saved snapshot unavailable")
    if current.state != "complete":
        return DriftReport(
            "unknown",
            None,
            (),
            f"current snapshot unavailable: {current.problem or 'unknown problem'}",
        )
    if saved.source_digest is None or current.source_digest is None:
        raise HandoffError("Complete Source snapshot is missing Source digest")

    branch_changed = saved.branch != current.branch
    if saved.source_digest == current.source_digest:
        return DriftReport("fresh", branch_changed, (), None)

    components = (
        ("HEAD", saved.head, current.head),
        ("Index", saved.index_digest, current.index_digest),
        (
            "Tracked filesystem",
            saved.tracked_filesystem_digest,
            current.tracked_filesystem_digest,
        ),
        (
            "Untracked filesystem",
            saved.untracked_filesystem_digest,
            current.untracked_filesystem_digest,
        ),
        ("Submodules", saved.submodules_digest, current.submodules_digest),
    )
    changed = tuple(name for name, old, new in components if old != new)
    return DriftReport("stale", branch_changed, changed, None)


def replace_candidate_snapshot(content: str, snapshot: SourceSnapshot) -> str:
    """Remove a candidate-supplied source section and append the trusted one."""
    candidate_without_snapshot = _strip_candidate_snapshot(content)
    status = validate_handoff(candidate_without_snapshot)
    if status == "idle":
        return candidate_without_snapshot
    return candidate_without_snapshot.rstrip("\n") + "\n\n" + render_source_snapshot(snapshot)


def _require_real_directory(path: Path, description: str) -> None:
    """Require a directory without following symbolic links."""
    try:
        path_stat = os.lstat(path)
    except FileNotFoundError as error:
        raise HandoffError(f"{description} not found at {path}; run /usw-init first") from error
    if stat.S_ISLNK(path_stat.st_mode):
        raise HandoffError(f"{description} must not be a symbolic link: {path}")
    if not stat.S_ISDIR(path_stat.st_mode):
        raise HandoffError(f"{description} is not a directory: {path}")


def _require_regular_file(path: Path, description: str) -> None:
    """Require a regular file without following symbolic links."""
    try:
        path_stat = os.lstat(path)
    except FileNotFoundError as error:
        raise HandoffError(f"{description} not found: {path}") from error
    if stat.S_ISLNK(path_stat.st_mode):
        raise HandoffError(f"{description} must not be a symbolic link: {path}")
    if not stat.S_ISREG(path_stat.st_mode):
        raise HandoffError(f"{description} must be a regular file: {path}")


def require_initialized_handoff(project: Path) -> Path:
    """Return an existing handoff path without requiring valid contents."""
    project_root = find_project_root(project)
    usw_directory = project_root / ".usw"
    _require_real_directory(usw_directory, "USW local-state directory")
    path = usw_directory / "HANDOFF.md"
    try:
        os.lstat(path)
    except FileNotFoundError as error:
        raise HandoffError(f"Handoff not found at {path}; run /usw-init first") from error
    _require_regular_file(path, "Handoff")
    return path


def read_handoff(project: Path) -> tuple[Path, str, str]:
    """Read and validate initialized handoff, including known-v1 snapshot fields."""
    path = require_initialized_handoff(project)
    content = path.read_text(encoding="utf-8")
    status = validate_handoff(content)
    source_snapshot_from_handoff(content)
    return path, content, status


def reconcile_handoff(project: Path, content: str | None = None) -> tuple[str, DriftReport]:
    """Read stored handoff and compare its checkpoint with the current source."""
    if content is None:
        _, content, _ = read_handoff(project)
    if V1_METADATA_HEADER in content:
        match = re.search(r"^- Identity: (.+)$", content, re.MULTILINE)
        saved_identity = match.group(1) if match else "none"
        if saved_identity == "none":
            return content, DriftReport("unknown", None, (), "saved snapshot missing")
        try:
            current_identity = _canonical_product_identity(project)
        except (OSError, ValueError) as error:
            return content, DriftReport("unknown", None, (), str(error))
        freshness = "fresh" if saved_identity == current_identity else "stale"
        return content, DriftReport(freshness, None, () if freshness == "fresh" else ("Product tree",), None)
    saved = source_snapshot_from_handoff(content)
    if saved is None:
        return content, DriftReport("unknown", None, (), "saved snapshot missing")
    if saved.schema != SOURCE_SCHEMA:
        return content, DriftReport("unknown", None, (), "unsupported schema")
    if saved.state != "complete":
        return content, DriftReport("unknown", None, (), "saved snapshot unavailable")
    current = capture_source_snapshot(project)
    return content, compare_source_snapshots(saved, current)


def _atomic_write(path: Path, content: str) -> None:
    _require_real_directory(path.parent, "USW local-state directory")
    if path.exists():
        _require_regular_file(path, "Handoff")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def save_handoff(project: Path, candidate: Path) -> tuple[Path, str]:
    """Atomically save validated Markdown with a script-generated snapshot."""
    target = require_initialized_handoff(project)
    supplied_candidate = candidate.expanduser()
    candidate = supplied_candidate.parent.resolve() / supplied_candidate.name
    expected_candidate = target.with_name("HANDOFF.next.md")
    if candidate != expected_candidate:
        raise HandoffError(f"Candidate handoff must be written to {expected_candidate}")
    _require_regular_file(candidate, "Candidate handoff")
    supplied_content = candidate.read_text(encoding="utf-8")
    if V1_METADATA_HEADER in supplied_content:
        status = validate_handoff(supplied_content)
        identity = _canonical_product_identity(project)
        saved_content = re.sub(
            r"^- Identity: .+$", f"- Identity: {identity}", supplied_content,
            count=1, flags=re.MULTILINE,
        )
        saved_content = re.sub(
            r"^- Freshness: .+$", "- Freshness: fresh", saved_content,
            count=1, flags=re.MULTILINE,
        )
        validate_handoff(saved_content)
        _atomic_write(target, saved_content)
        candidate.unlink()
        return target, status
    candidate_without_snapshot = _strip_candidate_snapshot(supplied_content)
    status = validate_handoff(candidate_without_snapshot)
    snapshot = capture_source_snapshot(project)
    saved_content = replace_candidate_snapshot(candidate_without_snapshot, snapshot)
    validate_handoff(saved_content)
    source_snapshot_from_handoff(saved_content)
    _atomic_write(target, saved_content)
    candidate.unlink()
    return target, status


def finish_handoff(project: Path) -> Path:
    """Replace initialized handoff state with an idle state."""
    target = require_initialized_handoff(project)
    _atomic_write(target, render_v1_idle())
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    show = subparsers.add_parser("show", help="Validate and print current handoff")
    show.add_argument("project", nargs="?", default=".", type=Path)

    save = subparsers.add_parser("save", help="Validate and save candidate handoff")
    save.add_argument("project", type=Path)
    save.add_argument("candidate", type=Path)

    finish = subparsers.add_parser("finish", help="Clear active handoff state")
    finish.add_argument("project", nargs="?", default=".", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "show":
            path, handoff_content, status = read_handoff(args.project)
            content, report = reconcile_handoff(args.project, content=handoff_content)
            print(content, end="")
            message = f"Validated: {path} (status: {status}; freshness: {report.freshness})"
            if report.reason:
                message += f"; {report.reason}"
            if report.branch_changed:
                message += "; warning: branch/ref changed"
            print(message, file=sys.stderr)
        elif args.command == "save":
            path, status = save_handoff(args.project, args.candidate)
            print(f"Saved: {path} (status: {status})")
        else:
            path = finish_handoff(args.project)
            print(f"Finished: {path} (status: idle)")
    except (OSError, HandoffError) as error:
        print(f"USW handoff failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
