#!/usr/bin/env python3
"""Safely load one opaque Markdown flow for model execution."""

from __future__ import annotations

import argparse
import errno
import hashlib
import importlib.util
import json
import os
import re
import secrets
import stat
import sys
from contextlib import ExitStack, contextmanager
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

    def __init__(self, code: str, detail: str, *, written: bool = False) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.written = written


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


class FlowWritePlan(NamedTuple):
    name: str
    origin: str
    layout: str
    path: Path
    flow_directory: Path
    project_root: Path
    flow_root: Path
    root_exists: bool
    exists: bool
    package_exists: bool
    markdown: str
    identity: str | None
    write_token: str


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


def _load_initialize_project(skills_root: Path):
    """Load the canonical workspace config parser without duplicating YAML."""

    name = "usw_initialize_project"
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    path = skills_root / "usw-initialize-project" / "scripts" / "init_usw.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SAFE_ACCESS = _load_safe_access(SKILLS_ROOT)
INITIALIZE_PROJECT = _load_initialize_project(SKILLS_ROOT)


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


def _authoring_root(
    project_root: Path, origin: str | None
) -> tuple[Path, Path, str]:
    selected_origin = "shared" if origin is None else origin
    if selected_origin not in ORIGINS:
        raise FlowError(
            "invalid_flow_origin", f"unsupported flow origin: {selected_origin!r}"
        )
    try:
        project = INITIALIZE_PROJECT.find_project_root(_absolute(project_root))
    except OSError as error:
        raise FlowError("unsafe_project_root", str(error)) from error
    if selected_origin == "local":
        try:
            with _open_directory(project, project / ".usw", "local workspace"):
                pass
        except FlowError as error:
            if error.code == "missing_flow_root":
                raise FlowError(
                    "workspace_not_initialized", "local workspace is missing; run usw-init"
                ) from error
            raise
        return project, project / ".usw" / "flows", selected_origin
    try:
        flow_root = project / INITIALIZE_PROJECT.load_config(project).flow_root
    except INITIALIZE_PROJECT.ConfigError as error:
        raise FlowError(error.code, str(error).partition(": ")[2] or str(error)) from error
    except UnicodeError as error:
        raise FlowError("invalid_config", "usw.yaml is not valid UTF-8") from error
    except OSError as error:
        raise FlowError("unsafe_project_config", str(error)) from error
    return project, flow_root, selected_origin


def _write_token(
    *,
    origin: str,
    flow_root: Path,
    name: str,
    layout: str,
    path: Path,
    exists: bool,
    package_exists: bool,
    identity: str | None,
    root_exists: bool = True,
) -> str:
    state = json.dumps(
        {
            "version": 1,
            "origin": origin,
            "flow_root": str(flow_root),
            "root_exists": root_exists,
            "name": name,
            "layout": layout,
            "path": str(path),
            "exists": exists,
            "package_exists": package_exists,
            "identity": identity,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "usw-write:" + hashlib.sha256(state).hexdigest()


def _inspect_flow_write(
    project_root: Path,
    flow_root: Path,
    name: str,
    origin: str,
) -> FlowWritePlan:
    if not FLOW_NAME.fullmatch(name):
        raise FlowError("invalid_flow_name", f"unsafe flow name: {name!r}")

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

        packaged_mode = None
        content = b""
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
                    "FLOW.md",
                    packaged_path,
                    error_code="unsafe_flow_file",
                )
                if packaged_mode is not None and not stat.S_ISREG(packaged_mode):
                    raise FlowError(
                        "unsafe_flow_file",
                        f"Markdown flow is not a regular file: {packaged_path}",
                    )
                if packaged_mode is not None:
                    content = _read_regular_file(
                        package_directory, "FLOW.md", packaged_path
                    )
        else:
            packaged_path = package_path / "FLOW.md"

        if flat_mode is not None and packaged_mode is not None:
            raise FlowError(
                "ambiguous_flow_layout",
                f"both flow layouts exist: {flat_path}, {packaged_path}",
            )
        if flat_mode is not None:
            layout = "flat"
            path = flat_path
            flow_directory = root
            content = _read_regular_file(directory, flat_path.name, flat_path)
            exists = True
        else:
            layout = "package"
            path = packaged_path
            flow_directory = package_path
            exists = packaged_mode is not None

    try:
        markdown = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise FlowError("invalid_flow_encoding", f"flow is not UTF-8: {path}") from error
    identity = None
    if exists:
        identity = f"usw-markdown:{origin}:{hashlib.sha256(content).hexdigest()}"
    token = _write_token(
        origin=origin,
        flow_root=root,
        name=name,
        layout=layout,
        path=path,
        exists=exists,
        package_exists=package_mode is not None,
        identity=identity,
    )
    return FlowWritePlan(
        name=name,
        origin=origin,
        layout=layout,
        path=path,
        flow_directory=flow_directory,
        project_root=Path(os.path.realpath(_absolute(project_root))),
        flow_root=root,
        root_exists=True,
        exists=exists,
        package_exists=package_mode is not None,
        markdown=markdown,
        identity=identity,
        write_token=token,
    )


def prepare_flow_write(
    project_root: Path,
    name: str,
    *,
    origin: str | None = None,
) -> FlowWritePlan:
    """Resolve one safe authoring target from project config without writing."""

    if not FLOW_NAME.fullmatch(name):
        raise FlowError("invalid_flow_name", f"unsafe flow name: {name!r}")
    project, flow_root, selected_origin = _authoring_root(project_root, origin)
    try:
        return _inspect_flow_write(project, flow_root, name, selected_origin)
    except FlowError as error:
        if error.code != "missing_flow_root":
            raise
    path = flow_root / name / "FLOW.md"
    return FlowWritePlan(
        name=name, origin=selected_origin, layout="package", path=path,
        flow_directory=path.parent, project_root=project, flow_root=flow_root,
        root_exists=False, exists=False, package_exists=False, markdown="", identity=None,
        write_token=_write_token(
            origin=selected_origin, flow_root=flow_root, name=name, layout="package",
            path=path, exists=False, package_exists=False, identity=None, root_exists=False,
        ),
    )


@contextmanager
def _open_authoring_directory(
    parent, name: str, path: Path, *, create: bool, project_root: Path
):
    created = False
    try:
        if create:
            parent.make_directory(name, 0o755)
            created = True
            parent.sync()
        with _open_child_directory(parent, name, path, "authoring directory") as opened:
            yield opened
    except BaseException as error:
        if created and not getattr(error, "written", False):
            try:
                with _open_directory(project_root, path.parent, "cleanup parent"):
                    parent.remove_directory(name)
            except FlowError:
                # The original parent is no longer safely reachable; never clean a redirect.
                pass
            except OSError as cleanup_error:
                if (
                    cleanup_error.errno not in {errno.ENOTEMPTY, errno.EEXIST, errno.ENOENT}
                    and isinstance(error, FlowError)
                ):
                    raise FlowError(
                        error.code,
                        f"{error.detail}; cannot remove created directory: {path}: {cleanup_error}",
                    ) from error
        if isinstance(error, FileExistsError) and not created:
            raise FlowError("stale_flow_target", f"directory appeared: {path}") from error
        if isinstance(error, OSError):
            raise FlowError("unsafe_flow_root", f"cannot access authoring directory: {path}: {error}") from error
        raise


@contextmanager
def _open_write_root(plan: FlowWritePlan):
    with ExitStack() as stack:
        current, directory = stack.enter_context(
            _open_directory(plan.project_root, plan.project_root, "project root")
        )
        created = False
        for part in plan.flow_root.relative_to(plan.project_root).parts:
            current /= part
            missing = _entry_mode(
                directory, part, current, error_code="unsafe_flow_root"
            ) is None
            if missing:
                if plan.origin == "local" and current == plan.project_root / ".usw":
                    raise FlowError(
                        "workspace_not_initialized", "local workspace is missing; run usw-init"
                    )
                if plan.root_exists:
                    raise FlowError("stale_flow_target", "flow root disappeared")
                created = True
            elif current == plan.flow_root and not plan.root_exists and not created:
                raise FlowError("stale_flow_target", "flow root appeared")
            _, directory = stack.enter_context(
                _open_authoring_directory(
                    directory, part, current, create=missing, project_root=plan.project_root
                )
            )
        yield plan.flow_root, directory


def _target_identity(directory, name: str, path: Path, origin: str) -> str:
    content = _read_regular_file(directory, name, path)
    return f"usw-markdown:{origin}:{hashlib.sha256(content).hexdigest()}"


def _assert_write_target(
    plan: FlowWritePlan,
    root_directory,
    *,
    package_directory=None,
    package_created: bool = False,
) -> None:
    parent = plan.flow_directory if package_directory is not None else plan.flow_root
    with _open_directory(plan.project_root, parent, "authoring target parent"):
        pass
    flat_path = plan.flow_root / f"{plan.name}.md"
    flat_mode = _entry_mode(
        root_directory,
        flat_path.name,
        flat_path,
        error_code="unsafe_flow_file",
    )
    if flat_mode is not None and not stat.S_ISREG(flat_mode):
        raise FlowError(
            "unsafe_flow_file", f"Markdown flow is not a regular file: {flat_path}"
        )
    package_path = plan.flow_root / plan.name
    package_mode = _entry_mode(
        root_directory,
        plan.name,
        package_path,
        error_code="unsafe_flow_root",
    )
    if package_mode is not None and not stat.S_ISDIR(package_mode):
        raise FlowError(
            "unsafe_flow_root", f"flow package is not a real directory: {package_path}"
        )

    expected_package = plan.package_exists or package_created
    if (package_mode is not None) != expected_package:
        raise FlowError("stale_flow_target", "flow package changed after preparation")

    if plan.layout == "flat":
        if flat_mode is None or plan.identity is None:
            raise FlowError("stale_flow_target", "flat flow changed after preparation")
        if _target_identity(
            root_directory, flat_path.name, flat_path, plan.origin
        ) != plan.identity:
            raise FlowError("stale_flow_target", "flat flow changed after preparation")
        if package_mode is not None:
            with _open_child_directory(
                root_directory,
                plan.name,
                package_path,
                f"{plan.origin} flow package",
            ) as (_, current_package):
                packaged_mode = _entry_mode(
                    current_package,
                    "FLOW.md",
                    package_path / "FLOW.md",
                    error_code="unsafe_flow_file",
                )
                if packaged_mode is not None:
                    if not stat.S_ISREG(packaged_mode):
                        raise FlowError(
                            "unsafe_flow_file",
                            f"Markdown flow is not a regular file: {package_path / 'FLOW.md'}",
                        )
                    raise FlowError(
                        "stale_flow_target", "alternate flow layout appeared"
                    )
        return

    if flat_mode is not None:
        raise FlowError("stale_flow_target", "alternate flow layout appeared")
    if package_directory is None:
        if package_mode is not None:
            raise FlowError("stale_flow_target", "flow package changed after preparation")
        return
    packaged_path = package_path / "FLOW.md"
    packaged_mode = _entry_mode(
        package_directory,
        "FLOW.md",
        packaged_path,
        error_code="unsafe_flow_file",
    )
    if packaged_mode is not None and not stat.S_ISREG(packaged_mode):
        raise FlowError(
            "unsafe_flow_file",
            f"Markdown flow is not a regular file: {packaged_path}",
        )
    if plan.exists:
        if packaged_mode is None or plan.identity is None:
            raise FlowError("stale_flow_target", "packaged flow changed after preparation")
        if _target_identity(
            package_directory, "FLOW.md", packaged_path, plan.origin
        ) != plan.identity:
            raise FlowError("stale_flow_target", "packaged flow changed after preparation")
    elif packaged_mode is not None:
        raise FlowError("stale_flow_target", "packaged flow appeared after preparation")


def _atomic_replace(
    directory,
    target: str,
    content: str,
    plan: FlowWritePlan,
    recheck: Callable[[], None],
) -> None:
    temporary = f".{target}.{secrets.token_hex(12)}.tmp"
    replaced = False
    staged = False
    try:
        mode = directory.entry_mode(target) if plan.exists else None
        directory.write_exclusive(
            temporary, content, stat.S_IMODE(mode) if mode is not None else None
        )
        staged = True
        recheck()
        directory.replace(temporary, target)
        replaced = True
        directory.sync()
    except BaseException as error:
        if replaced:
            raise FlowError(
                "write_unverified", f"entrypoint was replaced: {plan.path}; {error}", written=True
            ) from error
        if staged or not isinstance(error, FileExistsError):
            try:
                with _open_directory(plan.project_root, plan.flow_directory, "cleanup parent"):
                    directory.unlink(temporary)
            except (FlowError, OSError):
                pass
        if isinstance(error, FlowError):
            raise
        if not isinstance(error, OSError):
            raise
        raise FlowError(
            "unsafe_flow_file", f"cannot atomically write Markdown flow: {plan.path}"
        ) from error


def write_prepared_flow(
    project_root: Path,
    name: str,
    expected_token: str,
    markdown: str,
    *,
    origin: str | None = None,
) -> FlowWritePlan:
    """Revalidate and atomically write only the prepared entrypoint."""

    if not isinstance(markdown, str):
        raise FlowError("invalid_flow_encoding", "flow content must be UTF-8 text")
    if not markdown.strip():
        raise FlowError("empty_flow_content", "flow content must not be empty or whitespace-only")
    plan = prepare_flow_write(project_root, name, origin=origin)
    if plan.write_token != expected_token:
        raise FlowError("stale_flow_target", "flow target changed after preparation")

    replaced = False
    try:
        with _open_write_root(plan) as (_, root_directory):
            if plan.layout == "flat":
                _assert_write_target(plan, root_directory)
                _atomic_replace(
                    root_directory,
                    plan.path.name,
                    markdown,
                    plan,
                    lambda: _assert_write_target(plan, root_directory),
                )
                replaced = True
            else:
                package_created = not plan.package_exists
                if package_created:
                    _assert_write_target(plan, root_directory)
                with _open_authoring_directory(
                    root_directory,
                    plan.name,
                    plan.flow_directory,
                    create=package_created,
                    project_root=plan.project_root,
                ) as (_, package_directory):
                    _assert_write_target(
                        plan,
                        root_directory,
                        package_directory=package_directory,
                        package_created=package_created,
                    )
                    _atomic_replace(
                        package_directory,
                        "FLOW.md",
                        markdown,
                        plan,
                        lambda: _assert_write_target(
                            plan,
                            root_directory,
                            package_directory=package_directory,
                            package_created=package_created,
                        ),
                    )
                    replaced = True
        written = prepare_flow_write(project_root, name, origin=origin)
        if (written.path, written.origin, written.layout, written.markdown) != (
            plan.path, plan.origin, plan.layout, markdown
        ):
            raise FlowError("write_unverified", "saved flow changed before read-back")
    except BaseException as error:
        if not replaced or getattr(error, "written", False):
            raise
        raise FlowError(
            "write_unverified", f"entrypoint was replaced: {plan.path}; {error}", written=True
        ) from error
    return written


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


def _flow_write_report(plan: FlowWritePlan) -> dict[str, object]:
    return {
        "name": plan.name,
        "origin": plan.origin,
        "layout": plan.layout,
        "path": str(plan.path),
        "flow_directory": str(plan.flow_directory),
        "exists": plan.exists,
        "markdown": plan.markdown,
        "identity": plan.identity,
        "write_token": plan.write_token,
    }


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

    prepare_write = commands.add_parser("prepare-write")
    prepare_write.add_argument("project_root", type=Path)
    prepare_write.add_argument("name")
    prepare_write.add_argument(
        "--origin", choices=sorted(ORIGINS), default=argparse.SUPPRESS
    )

    write = commands.add_parser("write")
    write.add_argument("project_root", type=Path)
    write.add_argument("name")
    write.add_argument("expected_token")
    write.add_argument(
        "--origin", choices=sorted(ORIGINS), default=argparse.SUPPRESS
    )
    args = parser.parse_args(arguments)

    try:
        if args.command == "prepare-write":
            write_plan = prepare_flow_write(
                args.project_root,
                args.name,
                origin=args.origin,
            )
        elif args.command == "write":
            source = getattr(sys.stdin, "buffer", sys.stdin)
            supplied = source.read()
            try:
                markdown = (
                    supplied.decode("utf-8")
                    if isinstance(supplied, bytes)
                    else supplied
                )
            except UnicodeDecodeError as error:
                raise FlowError(
                    "invalid_flow_encoding", "flow content on stdin is not UTF-8"
                ) from error
            write_plan = write_prepared_flow(
                args.project_root,
                args.name,
                args.expected_token,
                markdown,
                origin=args.origin,
            )
        elif args.command == "inspect":
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
            {"error": error.code, "detail": error.detail, **({"written": True} if error.written else {})},
            stream=sys.stderr,
        )
        return 2

    if args.command in {"prepare-write", "write"}:
        _print_json(_flow_write_report(write_plan))
    elif args.command == "inspect":
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
