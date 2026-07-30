#!/usr/bin/env python3
"""Safely load one opaque Markdown flow for model execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple


FLOW_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ORIGINS = frozenset({"local", "shared"})
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


def _absolute(path: Path, *, relative_to: Path | None = None) -> Path:
    if not path.is_absolute() and relative_to is not None:
        path = relative_to / path
    return Path(os.path.abspath(path))


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


def _read_regular_file(directory_descriptor: int, name: str, path: Path) -> bytes:
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
    parser.add_argument("command", choices=("resolve",))
    parser.add_argument("project_root", type=Path)
    parser.add_argument("shared_root", type=Path)
    parser.add_argument("name")
    parser.add_argument("input")
    parser.add_argument("--origin", choices=sorted(ORIGINS))
    args = parser.parse_args(arguments)

    try:
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
