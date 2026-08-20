#!/usr/bin/env python3
"""Safely load one opaque Markdown flow for model execution."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
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
    flow_directory: Path
    project_root: Path
    origin: str
    identity: str


class MarkdownInvocation(NamedTuple):
    flow: MarkdownFlow
    user_input: str
    warnings: tuple[str, ...] = ()


class FlowResource(NamedTuple):
    path: Path
    identity: str
    content: bytes


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


SKILLS_ROOT = Path(__file__).parents[2]


def _load_safe_access(skills_root: Path):
    """Load the one shared safe-access module, shared across skills."""

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


SAFE_ACCESS = _load_safe_access(SKILLS_ROOT)


def _symlink_component(path: Path) -> Path | None:
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

    project_root = Path(os.path.realpath(original_root))
    try:
        root = SAFE_ACCESS.open_safe_directory(project_root)
    except OSError as error:
        raise FlowError(
            "unsafe_project_root",
            f"project root is not a real directory: {project_root}",
        ) from error

    current = project_root
    directory = root
    try:
        for part in relative.parts:
            current /= part
            try:
                child = directory.child_directory(part)
            except FileNotFoundError as error:
                raise FlowError(
                    "missing_flow_root", f"{label} is missing: {current}"
                ) from error
            except OSError as error:
                raise FlowError(
                    "unsafe_flow_root",
                    f"{label} traverses a non-directory or symlink: {current}",
                ) from error
            if directory is not root:
                directory.close()
            directory = child
        yield project_root / relative, directory
    finally:
        if directory is not root:
            directory.close()
        root.close()


def _read_regular_file(directory, name: str, path: Path) -> bytes:
    try:
        return directory.read_bytes(name)
    except FileNotFoundError as error:
        raise FlowError("missing_flow", f"Markdown flow is missing: {path}") from error
    except OSError as error:
        raise FlowError(
            "unsafe_flow_file", f"cannot open Markdown flow: {path}"
        ) from error


def _entry_mode(
    directory,
    name: str,
    path: Path,
    *,
    error_code: str,
) -> int | None:
    try:
        return directory.entry_mode(name)
    except OSError as error:
        raise FlowError(error_code, f"cannot inspect flow path: {path}") from error


@contextmanager
def _open_child_directory(
    directory,
    name: str,
    path: Path,
    label: str,
):
    try:
        child = directory.child_directory(name)
    except OSError as error:
        raise FlowError("unsafe_flow_root", f"{label} is unsafe: {path}") from error
    try:
        yield path, child
    finally:
        child.close()


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
    ) as (root, directory):
        flat_path = root / f"{name}.md"
        flat_mode = _entry_mode(
            directory,
            flat_path.name,
            flat_path,
            error_code="unsafe_flow_file",
        )
        if flat_mode is not None and not stat.S_ISREG(flat_mode):
            raise FlowError(
                "unsafe_flow_file",
                f"Markdown flow is not a regular file: {flat_path}",
            )

        package_path = root / name
        package_mode = _entry_mode(
            directory,
            name,
            package_path,
            error_code="unsafe_flow_root",
        )
        if package_mode is not None and not stat.S_ISDIR(package_mode):
            raise FlowError(
                "unsafe_flow_root",
                f"flow package is not a real directory: {package_path}",
            )

        packaged = False
        if package_mode is not None:
            with _open_child_directory(
                directory,
                name,
                package_path,
                f"{origin} flow package",
            ) as (package_root, package_directory):
                packaged_path = package_root / "FLOW.md"
                packaged_mode = _entry_mode(
                    package_directory,
                    packaged_path.name,
                    packaged_path,
                    error_code="unsafe_flow_file",
                )
                if packaged_mode is not None and not stat.S_ISREG(packaged_mode):
                    raise FlowError(
                        "unsafe_flow_file",
                        f"Markdown flow is not a regular file: {packaged_path}",
                    )
                packaged = packaged_mode is not None
                if flat_mode is not None and packaged:
                    raise FlowError(
                        "ambiguous_flow_layout",
                        f"both flow layouts exist: {flat_path}, {packaged_path}",
                    )
                if packaged:
                    path = packaged_path
                    flow_directory = package_root
                    content = _read_regular_file(
                        package_directory, path.name, path
                    )

        if not packaged:
            if flat_mode is None:
                raise FlowError(
                    "missing_flow",
                    f"Markdown flow is missing: {flat_path}",
                )
            path = flat_path
            flow_directory = root
            content = _read_regular_file(directory, path.name, path)
    try:
        markdown = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise FlowError("invalid_flow_encoding", f"flow is not UTF-8: {path}") from error
    digest = hashlib.sha256(content).hexdigest()
    return MarkdownFlow(
        name=name,
        markdown=markdown,
        path=path,
        flow_directory=flow_directory,
        project_root=Path(os.path.realpath(_absolute(project_root))),
        origin=origin,
        identity=f"usw-markdown:{origin}:{digest}",
    )


def resolve_flow_resource(flow: MarkdownFlow, relative_path: str) -> FlowResource:
    """Read one explicitly named packaged resource through the safe boundary."""
    if flow.path.name != "FLOW.md" or flow.path.parent != flow.flow_directory:
        raise FlowError(
            "flat_flow_resource",
            "flat flow references keep project/workspace-relative semantics",
        )
    if not isinstance(relative_path, str) or not relative_path:
        raise FlowError("invalid_flow_resource", "resource path must be relative")
    normalized = relative_path.replace("\\", "/")
    parts = normalized.split("/")
    if (
        normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized)
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise FlowError(
            "invalid_flow_resource",
            f"unsafe packaged resource path: {relative_path!r}",
        )
    resource_token = re.compile(
        r"(?<![\w./\\-])"
        + re.escape(normalized)
        + r"(?![\w/\\-]|\.(?=\w))"
    )
    if resource_token.search(flow.markdown) is None:
        raise FlowError(
            "undeclared_flow_resource",
            f"packaged flow Markdown does not name resource: {relative_path!r}",
        )

    with _open_directory(
        flow.project_root,
        flow.flow_directory,
        "flow package resource base",
    ) as (base, base_directory):
        path = base.joinpath(*parts)
        directory = base_directory
        opened = None
        try:
            current = base
            for part in parts[:-1]:
                current /= part
                try:
                    child = directory.child_directory(part)
                except FileNotFoundError as error:
                    raise FlowError(
                        "missing_flow_resource", f"resource is missing: {current}"
                    ) from error
                except OSError as error:
                    raise FlowError(
                        "unsafe_flow_resource",
                        f"resource component is unsafe: {current}",
                    ) from error
                if opened is not None:
                    opened.close()
                opened = child
                directory = child

            try:
                content = directory.read_bytes(parts[-1])
            except FileNotFoundError as error:
                raise FlowError(
                    "missing_flow_resource", f"resource is missing: {path}"
                ) from error
            except OSError as error:
                raise FlowError(
                    "unsafe_flow_resource", f"resource is unsafe: {path}"
                ) from error
            return FlowResource(
                path=path,
                identity="usw-resource:" + hashlib.sha256(content).hexdigest(),
                content=content,
            )
        finally:
            if opened is not None:
                opened.close()


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
    try:
        with _open_directory(project_root, project_root, "project root") as (
            _,
            project_directory,
        ):
            local = project_directory.child_directory(".usw")
            try:
                if local.entry_mode("FLOW.json") is None:
                    return ()
            finally:
                local.close()
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
    if sum(
        argument == "--origin" or argument.startswith("--origin=")
        for argument in arguments
    ) > 1:
        _print_json(
            {
                "error": "invalid_flow_origin",
                "detail": "origin selector must not be repeated or conflicting",
            },
            stream=sys.stderr,
        )
        return 2

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

    resource = commands.add_parser("resource")
    resource.add_argument("project_root", type=Path)
    resource.add_argument("shared_root", type=Path)
    resource.add_argument("name")
    resource.add_argument("expected_identity")
    resource.add_argument("expected_path", type=Path)
    resource.add_argument("relative_path")
    resource.add_argument(
        "--origin", choices=sorted(ORIGINS), default=argparse.SUPPRESS
    )
    args = parser.parse_args(arguments)

    try:
        if args.command == "resource" and args.origin is None:
            raise FlowError(
                "missing_flow_origin",
                "resource lookup requires the exact resolved flow origin",
            )
        if args.command in {"inspect", "resource"}:
            flow = resolve_markdown_flow(
                args.project_root,
                args.shared_root,
                args.name,
                origin=args.origin,
            )
            if args.command == "resource":
                expected_path = args.expected_path
                if (
                    not expected_path.is_absolute()
                    or flow.identity != args.expected_identity
                    or flow.path != expected_path
                ):
                    raise FlowError(
                        "stale_flow_resource",
                        "resource lookup does not match the resolved flow identity and path",
                    )
                flow_resource = resolve_flow_resource(flow, args.relative_path)
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
                "flow_directory": str(flow.flow_directory),
                "markdown": flow.markdown,
                "warnings": [],
            }
        )
    elif args.command == "resource":
        _print_json(
            {
                "name": flow.name,
                "origin": flow.origin,
                "identity": flow.identity,
                "path": str(flow.path),
                "flow_directory": str(flow.flow_directory),
                "resource_path": str(flow_resource.path),
                "resource_identity": flow_resource.identity,
                "content_base64": base64.b64encode(flow_resource.content).decode(
                    "ascii"
                ),
            }
        )
    else:
        _print_json(
            {
                "name": invocation.flow.name,
                "origin": invocation.flow.origin,
                "identity": invocation.flow.identity,
                "path": str(invocation.flow.path),
                "flow_directory": str(invocation.flow.flow_directory),
                "input": invocation.user_input,
                "markdown": invocation.flow.markdown,
                "warnings": list(invocation.warnings),
            }
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
