#!/usr/bin/env python3
"""Validate and atomically persist optional generic USW handoff state."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import runpy
import secrets
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:  # POSIX only: absent on Windows, where msvcrt provides locking instead.
    import fcntl
except ImportError:  # pragma: no cover - selected by platform
    fcntl = None

try:  # Windows only.
    import msvcrt
except ImportError:  # pragma: no cover - selected by platform
    msvcrt = None
from types import SimpleNamespace


NON_IDLE_STATUSES = {
    "in_progress",
    "paused",
    "blocked",
    "decision_required",
    "failed",
    "completed",
}
RECOVERABLE_STATUSES = {
    "in_progress",
    "paused",
    "blocked",
    "decision_required",
}
TERMINAL_STATUSES = {"failed", "completed"}
OUTCOME_STATUSES = NON_IDLE_STATUSES - {"in_progress"}
CURRENT_SECTIONS = (
    "Input",
    "Done",
    "Current position",
    "Next action",
    "Blocker",
    "Checks",
    "References",
)
SECTIONS = (*CURRENT_SECTIONS, "Workspace")
CURRENT_METADATA = {
    "Updated",
    "Status",
    "Operation",
    "Invocation",
    "Flow",
    "Origin",
    "Flow identity",
    "Input digest",
}
ENRICHED_METADATA = {*CURRENT_METADATA, "Summary", "Started"}
MAX_SUMMARY_LENGTH = 120
MAX_WORKSPACE_ITEMS = 32
MAX_WORKSPACE_ITEM_LENGTH = 240
FLOW_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
FLOW_IDENTITY = re.compile(r"^usw-markdown:(local|shared):[0-9a-f]{64}$")
INVOCATION = re.compile(r"^[0-9a-f]{32}$")
OPERATION_ID = re.compile(r"^usw-operation:([0-9a-f]{64})$")
REVISION = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
LEGACY_HEADER = "| Subject | Role | Attempt | Current operation | Status | Updated |"
ROUTER_HEADER = "# Developer Handoff Router"
ROUTER_EMPTY = "No registered operations."
ROUTER_CLEANUP = (
    "Completed and failed operations remain visible until explicit cleanup."
)
ROUTER_CLEANUP_ALL = "`/usw-handoff cleanup`"
ROUTER_CLEANUP_ONE = "`/usw-handoff finish <operation-id>`"
ROUTER_DATA_START = "<!-- usw-routes"
ROUTER_DATA_END = "-->"
ROUTER_ENTRY = re.compile(
    r"^- `(usw-operation:([0-9a-f]{64}))` -> `handoffs/([0-9a-f]{64})\.md`$"
)
ROUTER_TABLE_HEADER = "| Task | Flow | Status | Operation | Updated |"
ROUTER_TABLE_SEPARATOR = "|---|---|---|---|---|"
ROUTER_TABLE_EMPTY = "| No registered operations | — | — | — | — |"
ROUTER_TABLE_ENTRY = re.compile(
    r"^\| .+ \| `[a-z0-9]+(?:-[a-z0-9]+)*` \| "
    r"`(?:in_progress|paused|blocked|decision_required|failed|completed)` \| "
    r"\[`([0-9a-f]{8})…`\]\(handoffs/([0-9a-f]{64})\.md\) \| "
    r"`[^`\r\n]+` \|$"
)
SKILLS_ROOT = Path(__file__).parents[2]
CONFIG = SimpleNamespace(
    **runpy.run_path(
        str(SKILLS_ROOT / "usw-initialize-project" / "scripts" / "init_usw.py")
    )
)


class HandoffError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class Handoff:
    status: str
    metadata: dict[str, str]
    sections: dict[str, str]
    legacy: bool = False


@dataclass(frozen=True)
class Router:
    operations: tuple[str, ...]


def find_project_root(start: Path) -> Path:
    start = start.expanduser().resolve()
    if not start.is_dir():
        raise HandoffError("invalid_project", f"project is not a directory: {start}")
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def _enabled_root(project: Path) -> Path:
    root = find_project_root(project)
    if not CONFIG.load_config(root).handoff:
        raise HandoffError(
            "handoff_disabled",
            "handoff capability is disabled by usw.yaml; no HANDOFF.md was read or changed",
        )
    return root


LOCK_RETRY_LIMIT = 100
LOCK_RETRY_DELAY = 0.05

def load_safe_access(skills_root: Path):
    """Load the one shared safe-access module, shared across skills.

    Cached under a stable name so every skill in a process gets the same module
    object: patching or probing it in one place then holds everywhere.
    """

    name = "usw_safe_access"
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    path = skills_root / "usw-initialize-project" / "scripts" / "safe_access.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SAFE_ACCESS = load_safe_access(SKILLS_ROOT)
# Names are re-exported for annotations and isinstance checks only. Behavior is
# always reached through SAFE_ACCESS so that patching it takes effect everywhere.
_SafeDirectory = SAFE_ACCESS.SafeDirectory
_DescriptorDirectory = SAFE_ACCESS.DescriptorDirectory
_PathnameDirectory = SAFE_ACCESS.PathnameDirectory


@contextmanager
def _exclusive_lock_file(path: Path):
    """Serialize transitions where flock is unavailable.

    Locks a dedicated file rather than the state directory, which Windows cannot
    open. Retries with a bound so a stuck holder surfaces as a handoff error
    instead of hanging.
    """

    lock_path = path / ".lock"
    try:
        descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    except OSError as error:
        raise HandoffError(
            "unsafe_handoff", f"cannot open handoff lock: {lock_path}"
        ) from error

    try:
        for attempt in range(LOCK_RETRY_LIMIT):
            try:
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if attempt == LOCK_RETRY_LIMIT - 1:
                    raise HandoffError(
                        "handoff_locked",
                        f"another process holds the handoff lock: {lock_path}",
                    )
                time.sleep(LOCK_RETRY_DELAY)
        try:
            yield
        finally:
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(descriptor)


@contextmanager
def _locked_local_directory(root: Path):
    path = root / ".usw"
    try:
        directory = SAFE_ACCESS.open_safe_directory(path)
    except FileNotFoundError as error:
        raise HandoffError(
            "missing_handoff", "run /usw-init before using handoff"
        ) from error
    except OSError as error:
        raise HandoffError(
            "unsafe_handoff", f"unsafe local state directory: {path}"
        ) from error

    try:
        if not SAFE_ACCESS.supports_descriptor_relative_access():
            with _exclusive_lock_file(path):
                yield path, directory
            return
        try:
            fcntl.flock(directory.descriptor, fcntl.LOCK_EX)
            yield path, directory
        finally:
            fcntl.flock(directory.descriptor, fcntl.LOCK_UN)
    finally:
        directory.close()


def _handoff_path(root: Path) -> Path:
    return root / ".usw" / "HANDOFF.md"


def _operation_path(root: Path, operation: str) -> Path:
    return root / ".usw" / operation_relative_path(operation)


def _operation_candidate_path(root: Path, operation: str) -> Path:
    return root / ".usw" / operation_candidate_relative_path(operation)


@contextmanager
def _opened_operation_directory(
    root: Path,
    local_directory: _SafeDirectory,
    *,
    create: bool = False,
):
    local_path = root / ".usw"
    path = local_path / "handoffs"
    try:
        directory = local_directory.child_directory("handoffs")
    except FileNotFoundError as error:
        if not create:
            raise HandoffError(
                "missing_operation_state",
                f"operation state directory is missing: {path}",
            ) from error
        try:
            local_directory.make_directory("handoffs", 0o700)
        except FileExistsError:
            pass
        try:
            directory = local_directory.child_directory("handoffs")
        except OSError as open_error:
            raise HandoffError(
                "unsafe_handoff", f"unsafe operation state directory: {path}"
            ) from open_error
    except OSError as error:
        raise HandoffError(
            "unsafe_handoff", f"unsafe operation state directory: {path}"
        ) from error
    try:
        yield path, directory
    finally:
        directory.close()


def _read_regular_at(
    directory: _SafeDirectory,
    name: str,
    path: Path,
    *,
    missing_code: str,
    missing_detail: str,
) -> str:
    try:
        return directory.read_text(name)
    except FileNotFoundError as error:
        raise HandoffError(missing_code, missing_detail) from error
    except OSError as error:
        raise HandoffError("unsafe_handoff", f"unsafe file: {path}") from error


def _read_operation_at(
    root: Path,
    local_directory: int,
    operation: str,
) -> tuple[Path, str, Handoff]:
    path = _operation_path(root, operation)
    with _opened_operation_directory(
        root, local_directory
    ) as (_, operation_directory):
        content = _read_regular_at(
            operation_directory,
            operation_filename(operation),
            path,
            missing_code="missing_operation",
            missing_detail=f"operation is not registered: {operation}",
        )
    parsed = parse_handoff(content)
    if (
        parsed.legacy
        or parsed.status == "idle"
        or parsed.metadata.get("Operation") != operation
    ):
        raise HandoffError(
            "invalid_operation_state",
            "operation document identity does not match its route",
        )
    return path, content, parsed


def _timestamp(value: datetime | None = None) -> str:
    return (value or datetime.now(timezone.utc)).isoformat(timespec="seconds")


def _validate_timestamp(value: str, field_name: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise HandoffError(
            "invalid_handoff", f"{field_name} must be ISO 8601"
        ) from error
    if parsed.tzinfo is None:
        raise HandoffError(
            "invalid_handoff", f"{field_name} must include a timezone"
        )


def _summary(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise HandoffError("invalid_summary", "Summary must be non-empty")
    if len(normalized) <= MAX_SUMMARY_LENGTH:
        return normalized
    return normalized[: MAX_SUMMARY_LENGTH - 3].rstrip() + "..."


def _workspace_items(values: tuple[str, ...] | list[str], name: str) -> tuple[str, ...]:
    if len(values) > MAX_WORKSPACE_ITEMS:
        raise HandoffError(
            "invalid_workspace",
            f"{name} supports at most {MAX_WORKSPACE_ITEMS} values",
        )
    normalized = []
    for value in values:
        item = value.strip() if isinstance(value, str) else ""
        if (
            not item
            or len(item) > MAX_WORKSPACE_ITEM_LENGTH
            or "\n" in item
            or "\r" in item
        ):
            raise HandoffError(
                "invalid_workspace",
                f"{name} values must be non-empty bounded lines",
            )
        normalized.append(item)
    return tuple(normalized)


def _render_workspace(
    base_revision: str,
    expected_writes: tuple[str, ...] | list[str] = (),
    observed_changes: tuple[str, ...] | list[str] = (),
) -> str:
    if base_revision not in {"unknown", "unborn", "not-git"} and not REVISION.fullmatch(
        base_revision
    ):
        raise HandoffError("invalid_workspace", "invalid base revision")
    expected = _workspace_items(expected_writes, "Expected writes")
    observed = _workspace_items(observed_changes, "Observed changes")
    return "\n".join(
        (
            f"- Base revision: {base_revision}",
            "- Expected writes: "
            + json.dumps(expected, ensure_ascii=False, separators=(", ", ": ")),
            "- Observed changes: "
            + json.dumps(observed, ensure_ascii=False, separators=(", ", ": ")),
        )
    )


def _parse_workspace(content: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    prefixes = (
        "- Base revision: ",
        "- Expected writes: ",
        "- Observed changes: ",
    )
    lines = content.splitlines()
    if len(lines) != len(prefixes) or any(
        not line.startswith(prefix) for line, prefix in zip(lines, prefixes)
    ):
        raise HandoffError("invalid_workspace", "invalid Workspace structure")
    base_revision = lines[0][len(prefixes[0]) :]
    try:
        expected = json.loads(lines[1][len(prefixes[1]) :])
        observed = json.loads(lines[2][len(prefixes[2]) :])
    except json.JSONDecodeError as error:
        raise HandoffError(
            "invalid_workspace", "workspace values must be JSON arrays"
        ) from error
    if not isinstance(expected, list) or not isinstance(observed, list):
        raise HandoffError(
            "invalid_workspace", "workspace values must be JSON arrays"
        )
    rendered = _render_workspace(base_revision, expected, observed)
    if rendered != content:
        raise HandoffError("invalid_workspace", "Workspace must be canonical")
    return base_revision, tuple(expected), tuple(observed)


def _workspace_base(root: Path) -> str:
    if not (root / ".git").exists():
        return "not-git"
    environment = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_INDEX_FILE",
    ):
        environment.pop(name, None)
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
    except OSError:
        return "unknown"
    revision = result.stdout.strip().lower()
    if result.returncode == 0 and REVISION.fullmatch(revision):
        return revision
    if result.returncode == 0:
        return "unknown"
    try:
        symbolic = subprocess.run(
            ["git", "-C", str(root), "symbolic-ref", "-q", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
    except OSError:
        return "unknown"
    head = symbolic.stdout.strip()
    if symbolic.returncode != 0 or not head.startswith("refs/heads/"):
        return "unknown"
    try:
        reference = subprocess.run(
            ["git", "-C", str(root), "show-ref", "--verify", "--quiet", head],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
    except OSError:
        return "unknown"
    if reference.returncode == 1 and not reference.stderr.strip():
        return "unborn"
    return "unknown"


def render_idle(updated_at: datetime | None = None) -> str:
    return (
        "# Developer Handoff\n\n"
        f"- Updated: {_timestamp(updated_at)}\n"
        "- Status: idle\n\n"
        "## Active work\n\n"
        "No active work.\n"
    )


def _operation_suffix(operation: str) -> str:
    matched = OPERATION_ID.fullmatch(operation)
    if matched is None:
        raise HandoffError("invalid_operation", "invalid operation identity")
    return matched.group(1)


def operation_filename(operation: str) -> str:
    return f"{_operation_suffix(operation)}.md"


def operation_relative_path(operation: str) -> str:
    return f"handoffs/{operation_filename(operation)}"


def operation_candidate_filename(operation: str) -> str:
    return f"{_operation_suffix(operation)}.next.md"


def operation_candidate_relative_path(operation: str) -> str:
    return f"handoffs/{operation_candidate_filename(operation)}"


def render_router(operations: tuple[str, ...] | list[str] = ()) -> str:
    normalized = tuple(sorted(operations))
    if len(normalized) != len(set(normalized)):
        raise HandoffError("invalid_router", "duplicate operation identity")
    for operation in normalized:
        _operation_suffix(operation)
    body = (
        [ROUTER_EMPTY]
        if not normalized
        else [
            f"- `{operation}` -> `{operation_relative_path(operation)}`"
            for operation in normalized
        ]
    )
    return "\n".join((ROUTER_HEADER, "", "## Operations", "", *body, ""))


def render_readable_router(
    operations: tuple[dict[str, str], ...] | list[dict[str, str]] = (),
) -> str:
    normalized = tuple(sorted(operations, key=lambda item: item["operation"]))
    identities = tuple(item["operation"] for item in normalized)
    if len(identities) != len(set(identities)):
        raise HandoffError("invalid_router", "duplicate operation identity")
    body = [
        ROUTER_TABLE_HEADER,
        ROUTER_TABLE_SEPARATOR,
    ]
    if not normalized:
        body.append(ROUTER_TABLE_EMPTY)
    for item in normalized:
        operation = item["operation"]
        suffix = _operation_suffix(operation)
        summary = item["summary"].replace("\\", "\\\\").replace("|", "\\|")
        path = operation_relative_path(operation)
        body.append(
            f"| {summary} | `{item['flow']}` | `{item['status']}` | "
            f"[`{suffix[:8]}…`]({path}) | `{item['updated']}` |"
        )
    return "\n".join(
        (
            ROUTER_HEADER,
            "",
            "## Operations",
            "",
            *body,
            "",
            "## Cleanup",
            "",
            ROUTER_CLEANUP,
            "",
            f"Remove all terminal operations: {ROUTER_CLEANUP_ALL}",
            "",
            f"Remove one operation: {ROUTER_CLEANUP_ONE}",
            "",
        )
    )


def _parse_route_entries(entries: list[str]) -> Router:
    if entries == [ROUTER_EMPTY]:
        return Router(())
    if not entries or ROUTER_EMPTY in entries:
        raise HandoffError("invalid_router", "invalid HANDOFF router entries")
    operations: list[str] = []
    for line in entries:
        matched = ROUTER_ENTRY.fullmatch(line)
        if matched is None or matched.group(2) != matched.group(3):
            raise HandoffError("invalid_router", "invalid HANDOFF router entry")
        operations.append(matched.group(1))
    if operations != sorted(operations):
        raise HandoffError("invalid_router", "router entries must be sorted")
    if len(operations) != len(set(operations)):
        raise HandoffError("invalid_router", "duplicate operation identity")
    return Router(tuple(operations))


def _parse_table_entries(entries: list[str]) -> Router:
    if entries == [ROUTER_TABLE_EMPTY]:
        return Router(())
    operations = []
    for line in entries:
        matched = ROUTER_TABLE_ENTRY.fullmatch(line)
        if matched is None or matched.group(1) != matched.group(2)[:8]:
            raise HandoffError("invalid_router", "invalid HANDOFF table row")
        operations.append(f"usw-operation:{matched.group(2)}")
    if not operations or operations != sorted(operations):
        raise HandoffError("invalid_router", "router rows must be non-empty and sorted")
    if len(operations) != len(set(operations)):
        raise HandoffError("invalid_router", "duplicate operation identity")
    return Router(tuple(operations))


def parse_router(content: str) -> Router:
    lines = content.splitlines()
    if len(lines) < 5 or lines[:4] != [ROUTER_HEADER, "", "## Operations", ""]:
        raise HandoffError("invalid_router", "invalid HANDOFF router structure")
    if lines[4] == ROUTER_TABLE_HEADER and ROUTER_DATA_START not in lines:
        try:
            cleanup_index = lines.index("## Cleanup")
        except ValueError as error:
            raise HandoffError(
                "invalid_router", "invalid HANDOFF router structure"
            ) from error
        expected_cleanup = [
            "## Cleanup",
            "",
            ROUTER_CLEANUP,
            "",
            f"Remove all terminal operations: {ROUTER_CLEANUP_ALL}",
            "",
            f"Remove one operation: {ROUTER_CLEANUP_ONE}",
        ]
        if (
            len(lines) < 13
            or lines[5] != ROUTER_TABLE_SEPARATOR
            or lines[cleanup_index - 1] != ""
            or lines[cleanup_index:] != expected_cleanup
        ):
            raise HandoffError("invalid_router", "invalid HANDOFF router structure")
        return _parse_table_entries(lines[6 : cleanup_index - 1])
    if ROUTER_DATA_START not in lines:
        if "## Routes" in lines and "## Cleanup" in lines:
            routes_index = lines.index("## Routes")
            cleanup_index = lines.index("## Cleanup")
            if (
                cleanup_index <= routes_index + 2
                or lines[routes_index + 1] != ""
                or lines[cleanup_index - 1] != ""
            ):
                raise HandoffError(
                    "invalid_router", "invalid HANDOFF router structure"
                )
            return _parse_route_entries(
                lines[routes_index + 2 : cleanup_index - 1]
            )
        if any(line.startswith(("# ", "## ")) for line in lines[4:]):
            raise HandoffError("invalid_router", "invalid HANDOFF router structure")
        return _parse_route_entries(lines[4:])

    try:
        routes_index = lines.index(ROUTER_DATA_START)
        routes_end = lines.index(ROUTER_DATA_END)
        cleanup_index = lines.index("## Cleanup")
    except ValueError as error:
        raise HandoffError(
            "invalid_router", "invalid HANDOFF router structure"
        ) from error
    cleanup = lines[cleanup_index:]
    expected_cleanup = [
        "## Cleanup",
        "",
        ROUTER_CLEANUP,
        "",
        f"Remove all terminal operations: {ROUTER_CLEANUP_ALL}",
        "",
        f"Remove one operation: {ROUTER_CLEANUP_ONE}",
    ]
    if (
        routes_index < 5
        or routes_end <= routes_index + 1
        or cleanup_index != routes_end + 1
        or lines[routes_index - 1] != ""
        or cleanup != expected_cleanup
    ):
        raise HandoffError("invalid_router", "invalid HANDOFF router structure")
    return _parse_route_entries(lines[routes_index + 1 : routes_end])


def validate_router(content: str) -> tuple[str, ...]:
    return parse_router(content).operations


def handoff_format(content: str) -> str:
    if content.startswith(f"{ROUTER_HEADER}\n"):
        parse_router(content)
        return "router"
    return "legacy" if parse_handoff(content).legacy else "generic"


def _metadata(lines: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.startswith("## "):
            break
        if not line.strip():
            continue
        if not line.startswith("- ") or ": " not in line:
            raise HandoffError("invalid_handoff", "invalid metadata line")
        key, value = line[2:].split(": ", 1)
        if key in result or not value.strip():
            raise HandoffError("invalid_handoff", f"invalid metadata field: {key}")
        result[key] = value.strip()
    return result


def _sections(lines: list[str]) -> tuple[list[str], dict[str, str]]:
    order: list[str] = []
    values: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        if line.startswith("## "):
            current = line[3:].strip()
            if current in values:
                raise HandoffError("invalid_handoff", f"duplicate section: {current}")
            order.append(current)
            values[current] = []
        elif current is not None:
            values[current].append(line)
    return order, {
        name: "\n".join(content).strip() for name, content in values.items()
    }


def _legacy_handoff(lines: list[str]) -> Handoff:
    index = lines.index(LEGACY_HEADER)
    if index + 2 >= len(lines):
        raise HandoffError("invalid_legacy_handoff", "incomplete legacy metadata")
    cells = [
        value.strip()
        for value in lines[index + 2].strip().strip("|").split("|")
    ]
    if len(cells) != 6 or cells[4] not in {*NON_IDLE_STATUSES, "idle"}:
        raise HandoffError("invalid_legacy_handoff", "invalid legacy status")
    return Handoff(cells[4], {}, {}, legacy=True)


def _operation_id(
    origin: str, flow_identity: str, input_digest: str, invocation: str
) -> str:
    source = "\0".join(
        (origin, flow_identity, input_digest, invocation)
    ).encode("utf-8")
    return f"usw-operation:{hashlib.sha256(source).hexdigest()}"


def parse_handoff(content: str) -> Handoff:
    lines = content.splitlines()
    if not lines or lines[0] != "# Developer Handoff":
        raise HandoffError(
            "invalid_handoff", "expected '# Developer Handoff' as first line"
        )
    if LEGACY_HEADER in lines:
        return _legacy_handoff(lines)
    if any(line.startswith("# ") for line in lines[1:]):
        raise HandoffError("invalid_handoff", "multiple top-level headings")

    metadata = _metadata(lines)
    if not {"Updated", "Status"} <= set(metadata):
        raise HandoffError("invalid_handoff", "missing Updated or Status")
    _validate_timestamp(metadata["Updated"], "Updated")
    status = metadata["Status"]
    order, sections = _sections(lines)

    if status == "idle":
        if set(metadata) != {"Updated", "Status"}:
            raise HandoffError("invalid_handoff", "idle metadata must be minimal")
        if order != ["Active work"] or sections["Active work"] != "No active work.":
            raise HandoffError("invalid_handoff", "invalid idle handoff")
        return Handoff(status, metadata, sections)

    if status not in NON_IDLE_STATUSES:
        raise HandoffError("invalid_handoff", f"unsupported status: {status}")
    enriched = set(metadata) == ENRICHED_METADATA
    if not enriched and set(metadata) != CURRENT_METADATA:
        raise HandoffError("invalid_handoff", "invalid active metadata fields")
    if enriched:
        if metadata["Summary"] != _summary(metadata["Summary"]):
            raise HandoffError("invalid_handoff", "Summary must be canonical")
        if metadata["Started"] != "unknown":
            _validate_timestamp(metadata["Started"], "Started")
    if not FLOW_NAME.fullmatch(metadata["Flow"]):
        raise HandoffError("invalid_handoff", "unsafe flow name")
    if metadata["Origin"] not in {"local", "shared"}:
        raise HandoffError("invalid_handoff", "invalid flow origin")
    identity = FLOW_IDENTITY.fullmatch(metadata["Flow identity"])
    if identity is None or identity.group(1) != metadata["Origin"]:
        raise HandoffError("invalid_handoff", "invalid flow identity")
    if not DIGEST.fullmatch(metadata["Input digest"]):
        raise HandoffError("invalid_handoff", "invalid input digest")
    if not INVOCATION.fullmatch(metadata["Invocation"]):
        raise HandoffError("invalid_handoff", "invalid invocation token")
    expected_operation = _operation_id(
        metadata["Origin"],
        metadata["Flow identity"],
        metadata["Input digest"],
        metadata["Invocation"],
    )
    if metadata["Operation"] != expected_operation:
        raise HandoffError("invalid_handoff", "operation identity does not match")
    expected_sections = SECTIONS if enriched else CURRENT_SECTIONS
    if order != list(expected_sections) or any(
        not sections[name] for name in expected_sections
    ):
        raise HandoffError("invalid_handoff", "invalid active sections")
    try:
        exact_input = json.loads(sections["Input"])
    except json.JSONDecodeError as error:
        raise HandoffError(
            "invalid_handoff", "Input must be one JSON string"
        ) from error
    if not isinstance(exact_input, str) or not exact_input.strip():
        raise HandoffError("invalid_handoff", "Input must be a non-empty JSON string")
    exact_input_digest = (
        f"sha256:{hashlib.sha256(exact_input.encode('utf-8')).hexdigest()}"
    )
    if metadata["Input digest"] != exact_input_digest:
        raise HandoffError("invalid_handoff", "Input does not match input digest")
    if len(sections["Next action"].splitlines()) != 1:
        raise HandoffError("invalid_handoff", "Next action must be one line")
    if enriched:
        _parse_workspace(sections["Workspace"])
    return Handoff(status, metadata, sections)


def validate_handoff(content: str) -> str:
    return parse_handoff(content).status


def _render_active(
    *,
    metadata: dict[str, str],
    sections: dict[str, str],
) -> str:
    for name, value in sections.items():
        if any(line.startswith(("# ", "## ")) for line in value.splitlines()):
            raise HandoffError(
                "invalid_handoff", f"{name} contains a reserved Markdown heading"
            )
    lines = ["# Developer Handoff", ""]
    for key in (
        "Summary",
        "Started",
        "Updated",
        "Status",
        "Operation",
        "Invocation",
        "Flow",
        "Origin",
        "Flow identity",
        "Input digest",
    ):
        lines.append(f"- {key}: {metadata[key]}")
    for name in SECTIONS:
        lines.extend(("", f"## {name}", "", sections[name]))
    return "\n".join(lines) + "\n"


def render_begin(
    flow_name: str,
    origin: str,
    flow_identity: str,
    user_input: str,
    *,
    summary: str | None = None,
    base_revision: str = "not-git",
    expected_writes: tuple[str, ...] = (),
    updated_at: datetime | None = None,
) -> str:
    if not user_input.strip():
        raise HandoffError("invalid_input", "input must be non-empty")
    input_digest = f"sha256:{hashlib.sha256(user_input.encode('utf-8')).hexdigest()}"
    invocation = secrets.token_hex(16)
    timestamp = _timestamp(updated_at)
    metadata = {
        "Summary": _summary(summary if summary is not None else user_input),
        "Started": timestamp,
        "Updated": timestamp,
        "Status": "in_progress",
        "Operation": _operation_id(
            origin, flow_identity, input_digest, invocation
        ),
        "Invocation": invocation,
        "Flow": flow_name,
        "Origin": origin,
        "Flow identity": flow_identity,
        "Input digest": input_digest,
    }
    sections = {
        "Input": json.dumps(user_input, ensure_ascii=False),
        "Done": "Nothing yet.",
        "Current position": "Before model execution.",
        "Next action": "Execute the loaded Markdown flow.",
        "Blocker": "None.",
        "Checks": "- not-run",
        "References": "- None.",
        "Workspace": _render_workspace(base_revision, expected_writes),
    }
    content = _render_active(metadata=metadata, sections=sections)
    parse_handoff(content)
    return content


def _atomic_write(
    directory: _SafeDirectory,
    path: Path,
    content: str,
    *,
    validator=parse_handoff,
) -> None:
    temporary = f".{path.name}.{secrets.token_hex(8)}.tmp"
    directory.write_exclusive(temporary, content, 0o600)
    try:
        directory.replace(temporary, path.name)
        directory.sync()
        saved = _read_regular_at(
            directory,
            path.name,
            path,
            missing_code="missing_handoff",
            missing_detail="HANDOFF disappeared after write",
        )
        validator(saved)
        if saved != content:
            raise HandoffError(
                "write_verification",
                "HANDOFF changed before exact readback verification",
            )
    finally:
        try:
            directory.unlink(temporary)
        except FileNotFoundError:
            pass


def _read_handoff_content_locked(
    root: Path, state_directory: int
) -> tuple[Path, str]:
    path = _handoff_path(root)
    content = _read_regular_at(
        state_directory,
        path.name,
        path,
        missing_code="missing_handoff",
        missing_detail="run /usw-init before using handoff",
    )
    return path, content


def _install_operation_document(
    operation_directory: _SafeDirectory,
    path: Path,
    content: str,
    *,
    allow_existing: bool = True,
) -> bool:
    name = path.name
    try:
        operation_directory.write_exclusive(name, content, 0o600)
    except FileExistsError:
        if not allow_existing:
            raise HandoffError(
                "operation_collision",
                f"operation document already exists: {path}",
            )
        saved = _read_regular_at(
            operation_directory,
            name,
            path,
            missing_code="missing_operation",
            missing_detail=f"operation document disappeared: {path}",
        )
        parse_handoff(saved)
        if saved != content:
            raise HandoffError(
                "operation_collision",
                "existing operation document does not match migration state",
            )
        return False
    try:
        operation_directory.sync()
        saved = _read_regular_at(
            operation_directory,
            name,
            path,
            missing_code="missing_operation",
            missing_detail=f"operation document disappeared: {path}",
        )
        parse_handoff(saved)
        if saved != content:
            raise HandoffError(
                "write_verification",
                "operation document changed before exact readback verification",
            )
        return True
    except BaseException:
        try:
            operation_directory.unlink(name)
        except FileNotFoundError:
            pass
        raise


def _ensure_router_locked(
    root: Path, state_directory: int
) -> tuple[Path, Router | None, str]:
    path, content = _read_handoff_content_locked(root, state_directory)
    state_format = handoff_format(content)
    if state_format == "router":
        return path, parse_router(content), content
    if state_format == "legacy":
        return path, None, content

    current = parse_handoff(content)
    if current.status == "idle":
        candidate = render_readable_router()
        _atomic_write(
            state_directory,
            path,
            candidate,
            validator=parse_router,
        )
        return path, Router(()), candidate

    operation = current.metadata["Operation"]
    operation_path = _operation_path(root, operation)
    created = False
    try:
        with _opened_operation_directory(
            root, state_directory, create=True
        ) as (_, operation_directory):
            created = _install_operation_document(
                operation_directory, operation_path, content
            )
        candidate = render_readable_router(
            (
                {
                    "operation": operation,
                    "flow": current.metadata["Flow"],
                    "status": current.status,
                    "summary": current.metadata.get("Summary")
                    or _summary(json.loads(current.sections["Input"])),
                    "updated": current.metadata["Updated"],
                },
            )
        )
        _atomic_write(
            state_directory,
            path,
            candidate,
            validator=parse_router,
        )
        return path, Router((operation,)), candidate
    except BaseException:
        if created:
            try:
                with _opened_operation_directory(
                    root, state_directory
                ) as (_, operation_directory):
                    operation_directory.unlink(operation_path.name)
                    operation_directory.sync()
            except FileNotFoundError:
                pass
        raise


def _registered_operation_locked(
    root: Path,
    state_directory: int,
    operation: str,
) -> tuple[Path, Router, Path, str, Handoff]:
    _operation_suffix(operation)
    router_path, router, _ = _ensure_router_locked(root, state_directory)
    if router is None:
        raise HandoffError(
            "legacy_recovery_required",
            "legacy HANDOFF is read-only until explicit finish",
        )
    if operation not in router.operations:
        raise HandoffError(
            "stale_operation",
            f"operation is not registered: {operation}",
        )
    operation_path, content, current = _read_operation_at(
        root, state_directory, operation
    )
    return router_path, router, operation_path, content, current


def _write_operation_at(
    root: Path,
    state_directory: int,
    operation: str,
    content: str,
) -> Path:
    path = _operation_path(root, operation)
    parsed = parse_handoff(content)
    if (
        parsed.legacy
        or parsed.status == "idle"
        or parsed.metadata.get("Operation") != operation
    ):
        raise HandoffError(
            "invalid_operation_state",
            "operation document identity does not match its route",
        )
    with _opened_operation_directory(
        root, state_directory
    ) as (_, operation_directory):
        _atomic_write(
            operation_directory,
            path,
            content,
            validator=parse_handoff,
        )
    return path


def _read_handoff_locked(
    root: Path, state_directory: int
) -> tuple[Path, str, str]:
    path, content = _read_handoff_content_locked(root, state_directory)
    return path, content, parse_handoff(content).status


def _operation_summaries_locked(
    root: Path,
    state_directory: int,
    router: Router,
) -> tuple[dict[str, str], ...]:
    summaries = []
    for operation in router.operations:
        path, _, current = _read_operation_at(
            root, state_directory, operation
        )
        summaries.append(
            {
                "operation": operation,
                "flow": current.metadata["Flow"],
                "status": current.status,
                "summary": current.metadata.get("Summary")
                or _summary(json.loads(current.sections["Input"])),
                "started": current.metadata.get("Started", "unknown"),
                "updated": current.metadata["Updated"],
                "path": str(path),
            }
        )
    return tuple(summaries)


def _write_readable_router_locked(
    root: Path,
    state_directory: int,
    path: Path,
    router: Router,
) -> str:
    candidate = render_readable_router(
        _operation_summaries_locked(root, state_directory, router)
    )
    _atomic_write(
        state_directory,
        path,
        candidate,
        validator=parse_router,
    )
    return candidate


def discover_handoffs(
    project: Path,
) -> tuple[Path, str, tuple[dict[str, str], ...], bool]:
    root = _enabled_root(project)
    with _locked_local_directory(root) as (_, directory):
        path, router, content = _ensure_router_locked(root, directory)
        if router is None:
            return path, content, (), True
        summaries = _operation_summaries_locked(root, directory, router)
        readable = render_readable_router(summaries)
        if content != readable:
            _atomic_write(
                directory,
                path,
                readable,
                validator=parse_router,
            )
            content = readable
        return (
            path,
            content,
            summaries,
            False,
        )


def assert_current_handoff(project: Path, operation: str) -> Path:
    root = _enabled_root(project)
    _operation_suffix(operation)
    with _locked_local_directory(root) as (_, directory):
        router_path, content = _read_handoff_content_locked(root, directory)
        if handoff_format(content) != "router":
            raise HandoffError(
                "inactive_parent",
                "nested execution requires a routed parent operation",
            )
        router = parse_router(content)
        if operation not in router.operations:
            raise HandoffError(
                "inactive_parent",
                f"parent operation is not registered: {operation}",
            )
        operation_path, _, current = _read_operation_at(
            root, directory, operation
        )
        if current.status not in RECOVERABLE_STATUSES:
            raise HandoffError(
                "inactive_parent",
                f"parent operation is not recoverable: {current.status}",
            )
        if not router_path.is_file():
            raise HandoffError(
                "inactive_parent", "HANDOFF router disappeared during verification"
            )
        return operation_path


def read_handoff(
    project: Path,
    operation: str | None = None,
) -> tuple[Path, str, str]:
    root = _enabled_root(project)
    with _locked_local_directory(root) as (_, directory):
        path, router, content = _ensure_router_locked(root, directory)
        if router is None:
            if operation is not None:
                raise HandoffError(
                    "legacy_recovery_required",
                    "legacy HANDOFF has no routed operation identity",
                )
            return path, content, parse_handoff(content).status
        if operation is not None:
            _, _, operation_path, operation_content, current = (
                _registered_operation_locked(root, directory, operation)
            )
            return operation_path, operation_content, current.status
        if not router.operations:
            return path, content, "idle"
        if len(router.operations) > 1:
            raise HandoffError(
                "operation_selection_required",
                "multiple operations are registered; select one from Show",
            )
        operation = router.operations[0]
        operation_path, operation_content, current = _read_operation_at(
            root, directory, operation
        )
        return operation_path, operation_content, current.status


def begin_handoff(
    project: Path,
    flow_name: str,
    origin: str,
    flow_identity: str,
    user_input: str,
    *,
    summary: str | None = None,
    expected_writes: tuple[str, ...] = (),
) -> tuple[Path, str]:
    root = _enabled_root(project)
    with _locked_local_directory(root) as (_, directory):
        router_path, router, _ = _ensure_router_locked(root, directory)
        if router is None:
            raise HandoffError(
                "legacy_recovery_required",
                "legacy HANDOFF is read-only; inspect or finish it before a new flow",
            )
        candidate = render_begin(
            flow_name,
            origin,
            flow_identity,
            user_input,
            summary=summary,
            base_revision=_workspace_base(root),
            expected_writes=expected_writes,
        )
        operation = parse_handoff(candidate).metadata["Operation"]
        if operation in router.operations:
            raise HandoffError(
                "operation_collision", "operation identity is already registered"
            )
        operation_path = _operation_path(root, operation)
        created = False
        try:
            with _opened_operation_directory(
                root, directory, create=True
            ) as (_, operation_directory):
                created = _install_operation_document(
                    operation_directory,
                    operation_path,
                    candidate,
                    allow_existing=False,
                )
            _write_readable_router_locked(
                root,
                directory,
                router_path,
                Router(tuple(sorted((*router.operations, operation)))),
            )
        except BaseException:
            if created:
                try:
                    with _opened_operation_directory(
                        root, directory
                    ) as (_, operation_directory):
                        operation_directory.unlink(operation_path.name)
                        operation_directory.sync()
                except FileNotFoundError:
                    pass
            raise
        return operation_path, operation


def outcome_handoff(
    project: Path,
    status: str,
    *,
    operation: str,
    done: str,
    position: str,
    next_action: str,
    blocker: str,
    checks: tuple[str, ...] = (),
    references: tuple[str, ...] = (),
    observed_changes: tuple[str, ...] = (),
) -> Path:
    if status not in OUTCOME_STATUSES:
        raise HandoffError("invalid_transition", f"invalid outcome status: {status}")
    root = _enabled_root(project)
    with _locked_local_directory(root) as (_, directory):
        router_path, router, path, _, current = _registered_operation_locked(
            root, directory, operation
        )
        if current.status not in RECOVERABLE_STATUSES:
            raise HandoffError(
                "invalid_transition", f"cannot update terminal status: {current.status}"
            )
        values = (done, position, next_action, blocker)
        if any(not value.strip() for value in values) or len(next_action.splitlines()) != 1:
            raise HandoffError("invalid_outcome", "outcome fields must be non-empty")
        metadata = dict(current.metadata)
        if "Summary" not in metadata:
            metadata["Summary"] = _summary(json.loads(current.sections["Input"]))
            metadata["Started"] = "unknown"
        metadata["Updated"] = _timestamp()
        metadata["Status"] = status
        sections = dict(current.sections)
        if "Workspace" in sections:
            base_revision, expected_writes, _ = _parse_workspace(
                sections["Workspace"]
            )
        else:
            base_revision, expected_writes = "unknown", ()
        sections.update(
            {
                "Done": done.strip(),
                "Current position": position.strip(),
                "Next action": next_action.strip(),
                "Blocker": blocker.strip(),
                "Checks": "\n".join(f"- {value}" for value in checks) or "- not-run",
                "References": (
                    "\n".join(f"- {value}" for value in references) or "- None."
                ),
                "Workspace": _render_workspace(
                    base_revision,
                    expected_writes,
                    observed_changes,
                ),
            }
        )
        candidate = _render_active(metadata=metadata, sections=sections)
        parse_handoff(candidate)
        result = _write_operation_at(
            root, directory, operation, candidate
        )
        _write_readable_router_locked(
            root, directory, router_path, router
        )
        return result


def save_handoff(
    project: Path,
    operation: str,
    candidate: Path,
) -> tuple[Path, str]:
    root = _enabled_root(project)
    _operation_suffix(operation)
    candidate = Path(os.path.abspath(candidate))
    candidate = Path(os.path.realpath(candidate.parent)) / candidate.name
    expected = _operation_candidate_path(root, operation)
    if candidate != expected:
        raise HandoffError(
            "invalid_candidate", f"candidate must be {expected}"
        )
    with _locked_local_directory(root) as (_, directory):
        router_path, router, target, _, current = _registered_operation_locked(
            root, directory, operation
        )
        with _opened_operation_directory(
            root, directory
        ) as (_, operation_directory):
            content = _read_regular_at(
                operation_directory,
                candidate.name,
                candidate,
                missing_code="missing_candidate",
                missing_detail=f"candidate is missing: {candidate}",
            )
        parsed = parse_handoff(content)
        if parsed.legacy:
            raise HandoffError("legacy_read_only", "legacy HANDOFF cannot be saved")
        if parsed.status == "idle":
            raise HandoffError(
                "invalid_transition", "only explicit finish may write idle"
            )
        if current.status not in RECOVERABLE_STATUSES:
            raise HandoffError(
                "invalid_transition", "terminal HANDOFF is inspect-or-finish only"
            )
        current_enriched = "Summary" in current.metadata
        parsed_enriched = "Summary" in parsed.metadata
        if not parsed_enriched:
            raise HandoffError(
                "invalid_transition",
                "save cannot downgrade or preserve the old operation shape; "
                "use an enriched candidate",
            )
        if parsed.metadata["Operation"] != current.metadata["Operation"]:
            raise HandoffError(
                "stale_operation", "save cannot change operation identity"
            )
        immutable = (
            "Invocation",
            "Flow",
            "Origin",
            "Flow identity",
            "Input digest",
        )
        if any(
            parsed.metadata[name] != current.metadata[name] for name in immutable
        ):
            raise HandoffError(
                "invalid_transition",
                "save cannot change immutable operation context",
            )
        parsed_base, parsed_expected, _ = _parse_workspace(
            parsed.sections["Workspace"]
        )
        if current_enriched:
            current_base, current_expected, _ = _parse_workspace(
                current.sections["Workspace"]
            )
            immutable_recovery_changed = (
                parsed.metadata["Started"] != current.metadata["Started"]
                or parsed_base != current_base
                or parsed_expected != current_expected
            )
        else:
            immutable_recovery_changed = (
                parsed.metadata["Started"] != "unknown"
                or parsed_base != "unknown"
                or bool(parsed_expected)
            )
        if immutable_recovery_changed:
            raise HandoffError(
                "invalid_transition",
                "save cannot change or invent immutable recovery context",
            )
        metadata = dict(parsed.metadata)
        metadata["Updated"] = _timestamp()
        content = _render_active(metadata=metadata, sections=parsed.sections)
        parse_handoff(content)
        _write_operation_at(root, directory, operation, content)
        _write_readable_router_locked(
            root, directory, router_path, router
        )
        with _opened_operation_directory(
            root, directory
        ) as (_, operation_directory):
            operation_directory.unlink(candidate.name)
            operation_directory.sync()
        return target, parsed.status


def finish_handoff(
    project: Path,
    operation: str | None = None,
) -> Path:
    root = _enabled_root(project)
    with _locked_local_directory(root) as (_, directory):
        path, router, _ = _ensure_router_locked(root, directory)
        if router is None:
            if operation is not None:
                raise HandoffError(
                    "legacy_recovery_required",
                    "legacy HANDOFF has no routed operation identity",
                )
            _atomic_write(
                directory,
                path,
                render_readable_router(),
                validator=parse_router,
            )
            return path

        if operation is None:
            if not router.operations:
                return path
            if len(router.operations) > 1:
                raise HandoffError(
                    "operation_selection_required",
                    "multiple operations are registered; select one from Show",
                )
            operation = router.operations[0]
        _registered_operation_locked(root, directory, operation)

        remaining = tuple(
            current
            for current in router.operations
            if current != operation
        )
        _write_readable_router_locked(
            root,
            directory,
            path,
            Router(remaining),
        )
        with _opened_operation_directory(
            root, directory
        ) as (_, operation_directory):
            for name in (
                operation_candidate_filename(operation),
                operation_filename(operation),
            ):
                try:
                    operation_directory.unlink(name)
                except FileNotFoundError:
                    pass
            operation_directory.sync()
        return path


def cleanup_handoffs(project: Path) -> tuple[Path, tuple[str, ...]]:
    root = _enabled_root(project)
    with _locked_local_directory(root) as (_, directory):
        path, router, _ = _ensure_router_locked(root, directory)
        if router is None:
            raise HandoffError(
                "legacy_recovery_required",
                "legacy HANDOFF must be finished explicitly",
            )
        terminal: list[str] = []
        for operation in router.operations:
            _, _, current = _read_operation_at(root, directory, operation)
            if current.status in TERMINAL_STATUSES:
                terminal.append(operation)
        if not terminal:
            _write_readable_router_locked(
                root, directory, path, router
            )
            return path, ()

        removed = tuple(terminal)
        remaining = tuple(
            operation
            for operation in router.operations
            if operation not in removed
        )
        _write_readable_router_locked(
            root,
            directory,
            path,
            Router(remaining),
        )
        with _opened_operation_directory(
            root, directory
        ) as (_, operation_directory):
            for operation in removed:
                for name in (
                    operation_candidate_filename(operation),
                    operation_filename(operation),
                ):
                    try:
                        operation_directory.unlink(name)
                    except FileNotFoundError:
                        pass
            operation_directory.sync()
        return path, removed


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage generic USW handoff")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("show", "resume"):
        command = commands.add_parser(name)
        command.add_argument("project", nargs="?", default=".", type=Path)
        command.add_argument("operation", nargs="?")
    finish = commands.add_parser("finish")
    finish.add_argument("project", nargs="?", default=".", type=Path)
    finish.add_argument("operation", nargs="?")
    cleanup = commands.add_parser("cleanup")
    cleanup.add_argument("project", nargs="?", default=".", type=Path)
    save = commands.add_parser("save")
    save.add_argument("project", type=Path)
    save.add_argument("operation")
    save.add_argument("candidate", type=Path)
    begin = commands.add_parser("begin")
    begin.add_argument("project", type=Path)
    begin.add_argument("flow")
    begin.add_argument("origin", choices=("local", "shared"))
    begin.add_argument("flow_identity")
    begin.add_argument("input")
    begin.add_argument("--summary")
    begin.add_argument("--expected-write", action="append", default=[])
    outcome = commands.add_parser("outcome")
    outcome.add_argument("project", type=Path)
    outcome.add_argument("status", choices=sorted(OUTCOME_STATUSES))
    outcome.add_argument("--operation", required=True)
    outcome.add_argument("--done", required=True)
    outcome.add_argument("--position", required=True)
    outcome.add_argument("--next-action", required=True)
    outcome.add_argument("--blocker", required=True)
    outcome.add_argument("--check", action="append", default=[])
    outcome.add_argument("--reference", action="append", default=[])
    outcome.add_argument("--observed-change", action="append", default=[])
    assert_current = commands.add_parser("assert-current")
    assert_current.add_argument("project", type=Path)
    assert_current.add_argument("operation")
    args = parser.parse_args(argv)

    try:
        if args.command in {"show", "resume"}:
            if args.operation is None:
                router_path, router_content, operations, legacy = (
                    discover_handoffs(args.project)
                )
                if not legacy and len(operations) != 1:
                    _print(
                        {
                            "path": str(router_path),
                            "status": (
                                "idle"
                                if not operations
                                else "selection_required"
                            ),
                            "legacy": False,
                            "recovery_only": bool(operations),
                            "operations": operations,
                            "content": router_content,
                        }
                    )
                    return 0
                selected = (
                    operations[0]["operation"] if operations else None
                )
            else:
                selected = args.operation
            path, content, status = read_handoff(
                args.project, selected
            )
            parsed = parse_handoff(content)
            _print(
                {
                    "path": str(path),
                    "status": status,
                    "legacy": parsed.legacy,
                    "recovery_only": parsed.legacy or status != "idle",
                    "content": content,
                }
            )
        elif args.command == "finish":
            _print(
                {
                    "path": str(
                        finish_handoff(args.project, args.operation)
                    ),
                    "status": "finished",
                    "operation": args.operation,
                }
            )
        elif args.command == "cleanup":
            path, removed = cleanup_handoffs(args.project)
            _print(
                {
                    "path": str(path),
                    "status": "cleaned",
                    "removed_operations": removed,
                }
            )
        elif args.command == "save":
            path, status = save_handoff(
                args.project, args.operation, args.candidate
            )
            _print({"path": str(path), "status": status})
        elif args.command == "begin":
            path, operation = begin_handoff(
                args.project,
                args.flow,
                args.origin,
                args.flow_identity,
                args.input,
                summary=args.summary,
                expected_writes=tuple(args.expected_write),
            )
            _print(
                {
                    "path": str(path),
                    "status": "in_progress",
                    "operation": operation,
                }
            )
        elif args.command == "assert-current":
            _print(
                {
                    "path": str(
                        assert_current_handoff(
                            args.project, args.operation
                        )
                    ),
                    "status": "current",
                    "operation": args.operation,
                }
            )
        else:
            path = outcome_handoff(
                args.project,
                args.status,
                operation=args.operation,
                done=args.done,
                position=args.position,
                next_action=args.next_action,
                blocker=args.blocker,
                checks=tuple(args.check),
                references=tuple(args.reference),
                observed_changes=tuple(args.observed_change),
            )
            _print({"path": str(path), "status": args.status})
        return 0
    except (HandoffError, OSError) as error:
        code = error.code if isinstance(error, HandoffError) else "handoff_io_error"
        detail = error.detail if isinstance(error, HandoffError) else str(error)
        print(
            json.dumps({"error": code, "detail": detail}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
