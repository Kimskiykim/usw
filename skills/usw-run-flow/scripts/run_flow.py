#!/usr/bin/env python3
"""Safely load one opaque Markdown flow for model execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import stat
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, NamedTuple


FLOW_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ORIGINS = frozenset({"local", "shared"})
OPERATION_ID = re.compile(r"^usw-operation:[0-9a-f]{64}$")
NATURAL_STOP_STATUSES = frozenset(
    {"completed", "failed", "paused", "blocked", "decision_required"}
)
RETIRED_COMMANDS = frozenset(
    {"validate", "run-script", "checkpoint-save", "checkpoint-resume"}
)
MIGRATION_DETAIL = (
    "structured runtime was removed; remove --experimental-structured and run "
    "the same Markdown with $usw-run-flow <name> <input>"
)


class FlowError(ValueError):
    """A stable loader or migration error."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class MarkdownFlow(NamedTuple):
    name: str
    markdown: str
    path: Path
    origin: str
    identity: str


class MarkdownInvocation(NamedTuple):
    flow: MarkdownFlow
    user_input: str
    warnings: tuple[str, ...] = ()


class ExecutionContext(NamedTuple):
    root_identity: str
    handoff_enabled: bool
    branch_label: str | None
    owns_durable_state: bool


class ExecutableInvocation(NamedTuple):
    invocation: MarkdownInvocation
    context: ExecutionContext


class NestedResult(NamedTuple):
    root_identity: str
    branch_label: str
    flow_name: str
    flow_origin: str
    flow_identity: str
    status: str
    factual_result: str
    checks: tuple[str, ...]
    references: tuple[str, ...]
    blocker: str
    next_action: str


class NestedAggregate(NamedTuple):
    root_identity: str
    results: tuple[NestedResult, ...]
    unresolved_statuses: tuple[str, ...]
    automatic_retry: bool = False


def _absolute(path: Path, *, relative_to: Path | None = None) -> Path:
    if not path.is_absolute() and relative_to is not None:
        path = relative_to / path
    return Path(os.path.abspath(path))


def _uses_windows_path_fallback() -> bool:
    return os.name == "nt"


def _symlink_component(path: Path) -> Path | None:
    """Return the first symlink component, if any."""
    for component in (path, *path.parents):
        if component == Path(component.anchor):
            break
        try:
            if component.is_symlink():
                return component
        except OSError:
            return component
    return None


@contextmanager
def _open_directory(
    project_root: Path, candidate: Path, label: str
):
    original_root = _absolute(project_root)
    candidate = _absolute(candidate, relative_to=original_root)
    try:
        relative = candidate.relative_to(original_root)
    except ValueError as error:
        raise FlowError(
            "unsafe_flow_root", f"{label} escapes project root: {candidate}"
        ) from error

    if _uses_windows_path_fallback():
        if _symlink_component(original_root) is not None:
            raise FlowError(
                "unsafe_project_root", f"project root contains a symlink: {original_root}"
            )
        if not original_root.is_dir():
            raise FlowError(
                "unsafe_project_root", f"project root is not a real directory: {original_root}"
            )
        current = original_root
        for part in relative.parts:
            current /= part
            if _symlink_component(current) is not None:
                raise FlowError(
                    "unsafe_flow_root",
                    f"{label} traverses a symlink: {current}",
                )
            if not current.is_dir():
                raise FlowError("missing_flow_root", f"{label} is missing: {current}")
        # Windows has no dir_fd/openat equivalent; retain the same checks by
        # validating every path component before the final file read.
        yield current, current
        return

    project_root = Path(os.path.realpath(original_root))
    current = project_root
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(
        os, "O_NOFOLLOW", 0
    )
    try:
        descriptor = os.open(project_root, flags)
    except OSError as error:
        raise FlowError(
            "unsafe_project_root", f"project root is not a real directory: {current}"
        ) from error
    try:
        for part in relative.parts:
            current /= part
            try:
                next_descriptor = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError as error:
                raise FlowError(
                    "missing_flow_root", f"{label} is missing: {current}"
                ) from error
            except OSError as error:
                raise FlowError(
                    "unsafe_flow_root",
                    f"{label} traverses a non-directory or symlink: {current}",
                ) from error
            os.close(descriptor)
            descriptor = next_descriptor
        yield project_root / relative, descriptor
    finally:
        os.close(descriptor)


def _read_regular_file(directory_descriptor: int | Path, name: str, path: Path) -> bytes:
    if isinstance(directory_descriptor, Path):
        if path.is_symlink():
            raise FlowError("unsafe_flow_file", f"cannot open Markdown flow: {path}")
        if not path.exists():
            raise FlowError("missing_flow", f"Markdown flow is missing: {path}")
        try:
            mode = path.stat().st_mode
        except OSError as error:
            raise FlowError("unsafe_flow_file", f"cannot open Markdown flow: {path}") from error
        if not stat.S_ISREG(mode):
            raise FlowError(
                "unsafe_flow_file", f"Markdown flow is not a regular file: {path}"
            )
        try:
            return path.read_bytes()
        except FileNotFoundError as error:
            raise FlowError("missing_flow", f"Markdown flow is missing: {path}") from error
        except OSError as error:
            raise FlowError("unsafe_flow_file", f"cannot open Markdown flow: {path}") from error

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=directory_descriptor)
    except FileNotFoundError as error:
        raise FlowError("missing_flow", f"Markdown flow is missing: {path}") from error
    except OSError as error:
        raise FlowError("unsafe_flow_file", f"cannot open Markdown flow: {path}") from error
    try:
        mode = os.fstat(descriptor).st_mode
        if not stat.S_ISREG(mode):
            raise FlowError(
                "unsafe_flow_file", f"Markdown flow is not a regular file: {path}"
            )
        with os.fdopen(descriptor, "rb", closefd=False) as source:
            return source.read()
    finally:
        os.close(descriptor)


def load_markdown_flow(
    project_root: Path,
    flow_root: Path,
    name: str,
    *,
    origin: str,
) -> MarkdownFlow:
    """Read a safe named flow once and bind identity to those exact bytes."""
    if not FLOW_NAME.fullmatch(name):
        raise FlowError("invalid_flow_name", f"unsafe flow name: {name!r}")
    if origin not in ORIGINS:
        raise FlowError("invalid_flow_origin", f"unsupported flow origin: {origin!r}")

    with _open_directory(
        project_root, flow_root, f"{origin} flow root"
    ) as (root, descriptor):
        path = root / f"{name}.md"
        content = _read_regular_file(descriptor, path.name, path)
    try:
        markdown = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise FlowError("invalid_flow_encoding", f"flow is not UTF-8: {path}") from error
    digest = hashlib.sha256(content).hexdigest()
    return MarkdownFlow(
        name=name,
        markdown=markdown,
        path=path,
        origin=origin,
        identity=f"usw-markdown:{origin}:{digest}",
    )


def resolve_markdown_flow(
    project_root: Path,
    shared_root: Path,
    name: str,
    *,
    origin: str | None = None,
) -> MarkdownFlow:
    """Resolve local first unless one exact origin was requested."""
    if origin not in {None, *ORIGINS}:
        raise FlowError("invalid_flow_origin", f"unsupported flow origin: {origin!r}")
    project_root = _absolute(project_root)
    if origin in {None, "local"}:
        try:
            return load_markdown_flow(
                project_root,
                project_root / ".usw" / "flows",
                name,
                origin="local",
            )
        except FlowError as error:
            if origin == "local" or error.code not in {
                "missing_flow_root",
                "missing_flow",
            }:
                raise
    return load_markdown_flow(
        project_root,
        shared_root,
        name,
        origin="shared",
    )


def _legacy_flow_warning(project_root: Path) -> tuple[str, ...]:
    if _uses_windows_path_fallback():
        try:
            with _open_directory(project_root, project_root, "project root") as (
                project_path,
                _,
            ):
                local_path = project_path / ".usw"
                legacy_path = local_path / "FLOW.json"
                if (
                    local_path.is_symlink()
                    or not local_path.is_dir()
                    or legacy_path.is_symlink()
                    or not legacy_path.exists()
                ):
                    return ()
        except (FileNotFoundError, FlowError, OSError):
            return ()
        return (
            "legacy .usw/FLOW.json belongs to the removed structured runtime "
            "and was left untouched",
        )

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(
        os, "O_NOFOLLOW", 0
    )
    try:
        with _open_directory(project_root, project_root, "project root") as (
            _,
            project_descriptor,
        ):
            local_descriptor = os.open(".usw", flags, dir_fd=project_descriptor)
            try:
                os.stat(
                    "FLOW.json",
                    dir_fd=local_descriptor,
                    follow_symlinks=False,
                )
            finally:
                os.close(local_descriptor)
    except (FileNotFoundError, FlowError, OSError):
        return ()
    return (
        "legacy .usw/FLOW.json belongs to the removed structured runtime "
        "and was left untouched",
    )


def prepare_markdown_run(
    project_root: Path,
    shared_root: Path,
    name: str,
    user_input: str,
    *,
    origin: str | None = None,
) -> MarkdownInvocation:
    if not isinstance(user_input, str) or not user_input.strip():
        raise FlowError("missing_input", "Markdown flow input must be non-empty")
    return MarkdownInvocation(
        flow=resolve_markdown_flow(
            project_root, shared_root, name, origin=origin
        ),
        user_input=user_input,
        warnings=_legacy_flow_warning(project_root),
    )


def bind_root_execution(
    invocation: MarkdownInvocation,
    *,
    handoff_enabled: bool,
    operation: str | None = None,
) -> ExecutableInvocation:
    if handoff_enabled:
        if operation is None or OPERATION_ID.fullmatch(operation) is None:
            raise FlowError(
                "invalid_execution_context",
                "enabled handoff requires the exact Begin operation identity",
            )
        identity = operation
    else:
        if operation is not None:
            raise FlowError(
                "invalid_execution_context",
                "disabled handoff root cannot bind a persisted operation",
            )
        identity = f"usw-ephemeral:{secrets.token_hex(16)}"
    return ExecutableInvocation(
        invocation=invocation,
        context=ExecutionContext(
            root_identity=identity,
            handoff_enabled=handoff_enabled,
            branch_label=None,
            owns_durable_state=True,
        ),
    )


def prepare_nested_run(
    project_root: Path,
    shared_root: Path,
    name: str,
    user_input: str,
    *,
    parent: ExecutionContext,
    branch_label: str,
    origin: str | None = None,
    assert_current: Callable[[Path, str], object] | None = None,
) -> ExecutableInvocation:
    if (
        not parent.owns_durable_state
        or parent.branch_label is not None
        or not isinstance(branch_label, str)
        or not branch_label.strip()
        or len(branch_label.splitlines()) != 1
    ):
        raise FlowError(
            "invalid_execution_context",
            "nested execution requires a root-owned context and one branch label",
        )
    invocation = prepare_markdown_run(
        project_root,
        shared_root,
        name,
        user_input,
        origin=origin,
    )
    if parent.handoff_enabled:
        if (
            OPERATION_ID.fullmatch(parent.root_identity) is None
            or assert_current is None
        ):
            raise FlowError(
                "invalid_execution_context",
                "nested execution requires exact routed parent verification",
            )
        assert_current(Path(project_root), parent.root_identity)
    elif assert_current is not None:
        raise FlowError(
            "invalid_execution_context",
            "disabled handoff must not inspect local handoff state",
        )
    return ExecutableInvocation(
        invocation=invocation,
        context=ExecutionContext(
            root_identity=parent.root_identity,
            handoff_enabled=parent.handoff_enabled,
            branch_label=branch_label.strip(),
            owns_durable_state=False,
        ),
    )


def record_nested_result(
    child: ExecutableInvocation,
    *,
    status: str,
    factual_result: str,
    checks: tuple[str, ...] = (),
    references: tuple[str, ...] = (),
    blocker: str = "None.",
    next_action: str = "Return to the root executor.",
) -> NestedResult:
    context = child.context
    if context.owns_durable_state or context.branch_label is None:
        raise FlowError(
            "invalid_nested_result",
            "only a nested invocation can return a child result",
        )
    if status not in NATURAL_STOP_STATUSES:
        raise FlowError(
            "invalid_nested_result", f"unsupported child status: {status}"
        )
    values = (factual_result, blocker, next_action)
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise FlowError(
            "invalid_nested_result",
            "child result, blocker and next action must be factual text",
        )
    return NestedResult(
        root_identity=context.root_identity,
        branch_label=context.branch_label,
        flow_name=child.invocation.flow.name,
        flow_origin=child.invocation.flow.origin,
        flow_identity=child.invocation.flow.identity,
        status=status,
        factual_result=factual_result.strip(),
        checks=tuple(checks),
        references=tuple(references),
        blocker=blocker.strip(),
        next_action=next_action.strip(),
    )


def collect_nested_results(
    root: ExecutionContext,
    results: tuple[NestedResult, ...] | list[NestedResult],
) -> NestedAggregate:
    if not root.owns_durable_state or root.branch_label is not None:
        raise FlowError(
            "invalid_nested_result",
            "nested results require their root-owned execution context",
        )
    collected = tuple(results)
    labels = [result.branch_label for result in collected]
    if len(labels) != len(set(labels)):
        raise FlowError(
            "invalid_nested_result", "nested branch labels must be unique"
        )
    for result in collected:
        if result.root_identity != root.root_identity:
            raise FlowError(
                "cross_root_result",
                "nested result belongs to another root operation",
            )
    return NestedAggregate(
        root_identity=root.root_identity,
        results=collected,
        unresolved_statuses=tuple(
            result.status
            for result in collected
            if result.status != "completed"
        ),
        automatic_retry=False,
    )


def _print_json(value: object, *, stream: object = sys.stdout) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True), file=stream)


def _migration_error() -> int:
    _print_json(
        {"error": "structured_runtime_removed", "detail": MIGRATION_DETAIL},
        stream=sys.stderr,
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if (
        "--experimental-structured" in arguments
        or (arguments and arguments[0] in RETIRED_COMMANDS)
    ):
        return _migration_error()

    parser = argparse.ArgumentParser(description="Load a text-first USW flow")
    parser.add_argument("--origin", choices=sorted(ORIGINS))
    commands = parser.add_subparsers(dest="command", required=True)

    resolve = commands.add_parser("resolve")
    resolve.add_argument("project_root", type=Path)
    resolve.add_argument("shared_root", type=Path)
    resolve.add_argument("name")
    resolve.add_argument("input")
    resolve.add_argument(
        "--origin", choices=sorted(ORIGINS), default=argparse.SUPPRESS
    )

    inspect = commands.add_parser("inspect")
    inspect.add_argument("project_root", type=Path)
    inspect.add_argument("shared_root", type=Path)
    inspect.add_argument("name")
    inspect.add_argument(
        "--origin", choices=sorted(ORIGINS), default=argparse.SUPPRESS
    )
    args = parser.parse_args(arguments)

    try:
        if args.command == "inspect":
            flow = resolve_markdown_flow(
                args.project_root,
                args.shared_root,
                args.name,
                origin=args.origin,
            )
        else:
            invocation = prepare_markdown_run(
                args.project_root,
                args.shared_root,
                args.name,
                args.input,
                origin=args.origin,
            )
    except FlowError as error:
        _print_json(
            {"error": error.code, "detail": error.detail},
            stream=sys.stderr,
        )
        return 2

    if args.command == "inspect":
        _print_json(
            {
                "name": flow.name,
                "origin": flow.origin,
                "identity": flow.identity,
                "path": str(flow.path),
                "markdown": flow.markdown,
                "warnings": [],
            }
        )
    else:
        _print_json(
            {
                "name": invocation.flow.name,
                "origin": invocation.flow.origin,
                "identity": invocation.flow.identity,
                "path": str(invocation.flow.path),
                "input": invocation.user_input,
                "markdown": invocation.flow.markdown,
                "warnings": list(invocation.warnings),
            }
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
