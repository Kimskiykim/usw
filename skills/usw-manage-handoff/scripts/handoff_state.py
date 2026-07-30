#!/usr/bin/env python3
"""Validate and atomically persist optional generic USW handoff state."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import runpy
import secrets
import stat
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
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
SECTIONS = (
    "Input",
    "Done",
    "Current position",
    "Next action",
    "Blocker",
    "Checks",
    "References",
)
FLOW_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
FLOW_IDENTITY = re.compile(r"^usw-markdown:(local|shared):[0-9a-f]{64}$")
INVOCATION = re.compile(r"^[0-9a-f]{32}$")
LEGACY_HEADER = "| Subject | Role | Attempt | Current operation | Status | Updated |"
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


@contextmanager
def _locked_local_directory(root: Path):
    path = root / ".usw"
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(
        os, "O_NOFOLLOW", 0
    )
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError as error:
        raise HandoffError(
            "missing_handoff", "run /usw-init before using handoff"
        ) from error
    except OSError as error:
        raise HandoffError(
            "unsafe_handoff", f"unsafe local state directory: {path}"
        ) from error
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield path, descriptor
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _handoff_path(root: Path) -> Path:
    return root / ".usw" / "HANDOFF.md"


def _read_regular_at(
    directory_descriptor: int,
    name: str,
    path: Path,
    *,
    missing_code: str,
    missing_detail: str,
) -> str:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=directory_descriptor)
    except FileNotFoundError as error:
        raise HandoffError(missing_code, missing_detail) from error
    except OSError as error:
        raise HandoffError("unsafe_handoff", f"unsafe file: {path}") from error
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise HandoffError("unsafe_handoff", f"unsafe file: {path}")
        with os.fdopen(descriptor, "r", encoding="utf-8", closefd=False) as handle:
            return handle.read()
    finally:
        os.close(descriptor)


def _timestamp(value: datetime | None = None) -> str:
    return (value or datetime.now(timezone.utc)).isoformat(timespec="seconds")


def _validate_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise HandoffError("invalid_handoff", "Updated must be ISO 8601") from error
    if parsed.tzinfo is None:
        raise HandoffError("invalid_handoff", "Updated must include a timezone")


def render_idle(updated_at: datetime | None = None) -> str:
    return (
        "# Developer Handoff\n\n"
        f"- Updated: {_timestamp(updated_at)}\n"
        "- Status: idle\n\n"
        "## Active work\n\n"
        "No active work.\n"
    )


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
    _validate_timestamp(metadata["Updated"])
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
    expected_metadata = {
        "Updated",
        "Status",
        "Operation",
        "Invocation",
        "Flow",
        "Origin",
        "Flow identity",
        "Input digest",
    }
    if set(metadata) != expected_metadata:
        raise HandoffError("invalid_handoff", "invalid active metadata fields")
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
    if order != list(SECTIONS) or any(not sections[name] for name in SECTIONS):
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
    updated_at: datetime | None = None,
) -> str:
    if not user_input.strip():
        raise HandoffError("invalid_input", "input must be non-empty")
    input_digest = f"sha256:{hashlib.sha256(user_input.encode('utf-8')).hexdigest()}"
    invocation = secrets.token_hex(16)
    metadata = {
        "Updated": _timestamp(updated_at),
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
    }
    content = _render_active(metadata=metadata, sections=sections)
    parse_handoff(content)
    return content


def _atomic_write(
    directory_descriptor: int, path: Path, content: str
) -> None:
    temporary = f".HANDOFF.md.{secrets.token_hex(8)}.tmp"
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(temporary, flags, 0o600, dir_fd=directory_descriptor)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temporary,
            path.name,
            src_dir_fd=directory_descriptor,
            dst_dir_fd=directory_descriptor,
        )
        os.fsync(directory_descriptor)
        saved = _read_regular_at(
            directory_descriptor,
            path.name,
            path,
            missing_code="missing_handoff",
            missing_detail="HANDOFF disappeared after write",
        )
        parse_handoff(saved)
        if saved != content:
            raise HandoffError(
                "write_verification",
                "HANDOFF changed before exact readback verification",
            )
    finally:
        try:
            os.unlink(temporary, dir_fd=directory_descriptor)
        except FileNotFoundError:
            pass


def _read_handoff_locked(
    root: Path, directory_descriptor: int
) -> tuple[Path, str, str]:
    path = _handoff_path(root)
    content = _read_regular_at(
        directory_descriptor,
        path.name,
        path,
        missing_code="missing_handoff",
        missing_detail="run /usw-init before using handoff",
    )
    return path, content, parse_handoff(content).status


def read_handoff(project: Path) -> tuple[Path, str, str]:
    root = _enabled_root(project)
    with _locked_local_directory(root) as (_, descriptor):
        return _read_handoff_locked(root, descriptor)


def begin_handoff(
    project: Path,
    flow_name: str,
    origin: str,
    flow_identity: str,
    user_input: str,
) -> tuple[Path, str]:
    root = _enabled_root(project)
    with _locked_local_directory(root) as (_, descriptor):
        path, content, status = _read_handoff_locked(root, descriptor)
        current = parse_handoff(content)
        if current.legacy:
            raise HandoffError(
                "legacy_recovery_required",
                "legacy HANDOFF is read-only; inspect or finish it before a new flow",
            )
        if status in RECOVERABLE_STATUSES:
            raise HandoffError(
                "active_handoff",
                "a recoverable non-idle HANDOFF blocks every new flow until explicit finish",
            )
        candidate = render_begin(flow_name, origin, flow_identity, user_input)
        _atomic_write(descriptor, path, candidate)
        return path, parse_handoff(candidate).metadata["Operation"]


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
) -> Path:
    if status not in OUTCOME_STATUSES:
        raise HandoffError("invalid_transition", f"invalid outcome status: {status}")
    root = _enabled_root(project)
    with _locked_local_directory(root) as (_, descriptor):
        path, content, _ = _read_handoff_locked(root, descriptor)
        current = parse_handoff(content)
        if current.legacy:
            raise HandoffError(
                "legacy_recovery_required",
                "legacy HANDOFF cannot receive generic Outcome",
            )
        if current.metadata.get("Operation") != operation:
            raise HandoffError(
                "stale_operation", "Outcome does not match the current operation"
            )
        if current.status not in RECOVERABLE_STATUSES:
            raise HandoffError(
                "invalid_transition", f"cannot update terminal status: {current.status}"
            )
        values = (done, position, next_action, blocker)
        if any(not value.strip() for value in values) or len(next_action.splitlines()) != 1:
            raise HandoffError("invalid_outcome", "outcome fields must be non-empty")
        metadata = dict(current.metadata)
        metadata["Updated"] = _timestamp()
        metadata["Status"] = status
        sections = dict(current.sections)
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
            }
        )
        candidate = _render_active(metadata=metadata, sections=sections)
        parse_handoff(candidate)
        _atomic_write(descriptor, path, candidate)
        return path


def save_handoff(project: Path, candidate: Path) -> tuple[Path, str]:
    root = _enabled_root(project)
    target = _handoff_path(root)
    candidate = Path(os.path.abspath(candidate))
    candidate = Path(os.path.realpath(candidate.parent)) / candidate.name
    expected = target.with_name("HANDOFF.next.md")
    if candidate != expected:
        raise HandoffError(
            "invalid_candidate", f"candidate must be {expected}"
        )
    with _locked_local_directory(root) as (_, descriptor):
        _, current_content, _ = _read_handoff_locked(root, descriptor)
        current = parse_handoff(current_content)
        content = _read_regular_at(
            descriptor,
            candidate.name,
            candidate,
            missing_code="missing_candidate",
            missing_detail=f"candidate is missing: {candidate}",
        )
        parsed = parse_handoff(content)
        if parsed.legacy:
            raise HandoffError("legacy_read_only", "legacy HANDOFF cannot be saved")
        if current.legacy:
            raise HandoffError(
                "legacy_recovery_required",
                "legacy HANDOFF is read-only until explicit finish",
            )
        if parsed.status == "idle":
            raise HandoffError(
                "invalid_transition", "only explicit finish may write idle"
            )
        if current.status == "idle":
            raise HandoffError(
                "invalid_transition", "only Begin may create an operation from idle"
            )
        if current.status not in RECOVERABLE_STATUSES:
            raise HandoffError(
                "invalid_transition", "terminal HANDOFF is inspect-or-finish only"
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
        _atomic_write(descriptor, target, content)
        os.unlink(candidate.name, dir_fd=descriptor)
        return target, parsed.status


def finish_handoff(project: Path) -> Path:
    root = _enabled_root(project)
    with _locked_local_directory(root) as (_, descriptor):
        path, content, _ = _read_handoff_locked(root, descriptor)
        parse_handoff(content)
        _atomic_write(descriptor, path, render_idle())
        return path


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage generic USW handoff")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("show", "resume", "finish"):
        command = commands.add_parser(name)
        command.add_argument("project", nargs="?", default=".", type=Path)
    save = commands.add_parser("save")
    save.add_argument("project", type=Path)
    save.add_argument("candidate", type=Path)
    begin = commands.add_parser("begin")
    begin.add_argument("project", type=Path)
    begin.add_argument("flow")
    begin.add_argument("origin", choices=("local", "shared"))
    begin.add_argument("flow_identity")
    begin.add_argument("input")
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
    args = parser.parse_args(argv)

    try:
        if args.command in {"show", "resume"}:
            path, content, status = read_handoff(args.project)
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
            _print({"path": str(finish_handoff(args.project)), "status": "idle"})
        elif args.command == "save":
            path, status = save_handoff(args.project, args.candidate)
            _print({"path": str(path), "status": status})
        elif args.command == "begin":
            path, operation = begin_handoff(
                args.project,
                args.flow,
                args.origin,
                args.flow_identity,
                args.input,
            )
            _print(
                {
                    "path": str(path),
                    "status": "in_progress",
                    "operation": operation,
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
