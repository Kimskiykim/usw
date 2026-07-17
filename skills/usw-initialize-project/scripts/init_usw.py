#!/usr/bin/env python3
"""Initialize the USW OpenSpec workspace without overwriting project files."""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


LOCAL_STATE_IGNORE_CONTENT = "*\n"
TEMPLATE_ROOT = Path(__file__).parents[1] / "templates"


def render_handoff(updated_at: datetime | None = None) -> str:
    """Return the initial developer-local handoff state."""
    timestamp = updated_at or datetime.now(timezone.utc)
    return (
        "# Developer Handoff\n\n"
        f"- Updated: {timestamp.isoformat(timespec='seconds')}\n"
        "- Status: idle\n\n"
        "## Active work\n\n"
        "No active work.\n"
    )


def find_project_root(start: Path) -> Path:
    """Return the nearest Git root, or the supplied directory if none exists."""
    start = start.expanduser().resolve()
    if not start.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {start}")

    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def _relative_to_project(project_root: Path, path: Path) -> tuple[str, ...]:
    """Return a project-local path, rejecting paths that escape the project."""
    try:
        relative = path.relative_to(project_root)
    except ValueError as error:
        raise OSError(f"USW path escapes the project root: {path}") from error
    if not relative.parts:
        raise OSError("USW path must not be the project root")
    return relative.parts


def _require_real_directory(path: Path) -> None:
    """Reject symlinks and non-directory path components."""
    try:
        path_stat = os.lstat(path)
    except FileNotFoundError:
        raise
    if stat.S_ISLNK(path_stat.st_mode):
        raise OSError(f"USW refuses symbolic links inside the project: {path}")
    if not stat.S_ISDIR(path_stat.st_mode):
        raise NotADirectoryError(f"Project path is not a directory: {path}")


def _ensure_real_parent_directories(project_root: Path, path: Path) -> None:
    """Create missing parents while refusing to traverse symbolic links."""
    current = project_root
    for component in _relative_to_project(project_root, path)[:-1]:
        current = current / component
        try:
            _require_real_directory(current)
        except FileNotFoundError:
            try:
                current.mkdir()
            except FileExistsError:
                pass
            _require_real_directory(current)


def _existing_path_kind(path: Path) -> str | None:
    """Classify an existing path without following a symbolic link."""
    try:
        path_stat = os.lstat(path)
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(path_stat.st_mode):
        raise OSError(f"USW refuses symbolic links inside the project: {path}")
    if stat.S_ISDIR(path_stat.st_mode):
        return "directory"
    if stat.S_ISREG(path_stat.st_mode):
        return "file"
    raise OSError(f"Unsupported project filesystem object: {path}")


def create_file(project_root: Path, path: Path, content: str) -> bool:
    """Safely create a project-local file without following symbolic links."""
    _ensure_real_parent_directories(project_root, path)
    existing_kind = _existing_path_kind(path)
    if existing_kind == "file":
        return False
    if existing_kind == "directory":
        raise IsADirectoryError(f"Project path is a directory, not a file: {path}")

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        existing_kind = _existing_path_kind(path)
        if existing_kind == "file":
            return False
        if existing_kind == "directory":
            raise IsADirectoryError(f"Project path is a directory, not a file: {path}")
        raise
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return True


def create_directory(project_root: Path, path: Path) -> bool:
    """Safely create a project-local directory without following symbolic links."""
    _ensure_real_parent_directories(project_root, path)
    existing_kind = _existing_path_kind(path)
    if existing_kind == "directory":
        return False
    if existing_kind == "file":
        raise NotADirectoryError(f"Project path is not a directory: {path}")
    try:
        path.mkdir()
    except FileExistsError:
        existing_kind = _existing_path_kind(path)
        if existing_kind == "directory":
            return False
        if existing_kind == "file":
            raise NotADirectoryError(f"Project path is not a directory: {path}")
        raise
    return True


def read_template(relative_path: str) -> str:
    """Read a template distributed with the initialization skill."""
    return (TEMPLATE_ROOT / relative_path).read_text(encoding="utf-8")


def _git_is_worktree(project_root: Path) -> bool:
    """Return whether project_root is a usable Git worktree."""
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def _git_path_is_ignored(project_root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "check-ignore",
            "--quiet",
            "--no-index",
            "--",
            relative_path,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _git_path_is_tracked(project_root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "ls-files",
            "--error-unmatch",
            "--",
            relative_path,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def validate_workspace_paths(project_root: Path) -> None:
    """Reject existing managed paths that are symlinks or have the wrong type."""
    expected_paths = (
        ("openspec", "directory"),
        ("openspec/specs", "directory"),
        ("openspec/changes", "directory"),
        ("openspec/AGENTS.md", "file"),
        (".usw", "directory"),
        (".usw/.gitignore", "file"),
        (".usw/HANDOFF.md", "file"),
    )
    for rendered_path, expected_kind in expected_paths:
        parts = Path(rendered_path).parts
        current = project_root
        for index, component in enumerate(parts):
            current = current / component
            current_kind = _existing_path_kind(current)
            if current_kind is None:
                break
            is_leaf = index == len(parts) - 1
            required_kind = expected_kind if is_leaf else "directory"
            if current_kind != required_kind:
                if required_kind == "directory":
                    raise NotADirectoryError(f"Project path is not a directory: {current}")
                raise IsADirectoryError(f"Project path is a directory, not a file: {current}")


def validate_local_state_git_policy(project_root: Path) -> None:
    """Ensure existing local USW state will remain local in a Git worktree."""
    local_ignore_file = project_root / ".usw" / ".gitignore"
    if not _git_is_worktree(project_root):
        return

    local_paths = (".usw/HANDOFF.md", ".usw/HANDOFF.next.md")
    tracked = [
        relative_path
        for relative_path in local_paths
        if _git_path_is_tracked(project_root, relative_path)
    ]
    if tracked:
        rendered = ", ".join(tracked)
        raise OSError(
            f"USW local state is tracked by Git: {rendered}; run "
            "'git rm --cached <path>' before initializing"
        )
    if _existing_path_kind(local_ignore_file) is None:
        return
    unignored = [
        relative_path
        for relative_path in local_paths
        if not _git_path_is_ignored(project_root, relative_path)
    ]
    if unignored:
        rendered = ", ".join(unignored)
        raise OSError(
            f"Existing {local_ignore_file} does not ignore USW local state: {rendered}"
        )


def initialize_usw(project: Path) -> list[tuple[Path, bool]]:
    """Create the OpenSpec workspace and local USW state without overwrites."""
    project_root = find_project_root(project)
    openspec_directory = project_root / "openspec"
    specs_directory = openspec_directory / "specs"
    changes_directory = openspec_directory / "changes"
    agents_file = openspec_directory / "AGENTS.md"
    local_state_ignore_file = project_root / ".usw" / ".gitignore"
    handoff_file = project_root / ".usw" / "HANDOFF.md"

    validate_workspace_paths(project_root)
    validate_local_state_git_policy(project_root)

    return [
        (openspec_directory, create_directory(project_root, openspec_directory)),
        (specs_directory, create_directory(project_root, specs_directory)),
        (changes_directory, create_directory(project_root, changes_directory)),
        (
            agents_file,
            create_file(project_root, agents_file, read_template("openspec/AGENTS.md")),
        ),
        (
            local_state_ignore_file,
            create_file(project_root, local_state_ignore_file, LOCAL_STATE_IGNORE_CONTENT),
        ),
        (handoff_file, create_file(project_root, handoff_file, render_handoff())),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create an OpenSpec-compatible workspace and developer-local "
            ".usw/HANDOFF.md without overwriting existing project files."
        )
    )
    parser.add_argument(
        "project",
        nargs="?",
        default=".",
        type=Path,
        help="Project directory (defaults to the current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        results = initialize_usw(args.project)
    except OSError as error:
        print(f"USW initialization failed: {error}", file=sys.stderr)
        return 1

    for path, created in results:
        status = "Created" if created else "Already exists"
        print(f"{status}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
