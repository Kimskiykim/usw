#!/usr/bin/env python3
"""Initialize the USW project harness without overwriting files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SYNC_CONTENT = "# SYNC\n"
HELLO_WORLD_CONTENT = 'print("Hello, World!")\n'


def find_project_root(start: Path) -> Path:
    """Return the nearest Git root, or the supplied directory if none exists."""
    start = start.expanduser().resolve()
    if not start.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {start}")

    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def create_file(path: Path, content: str) -> bool:
    """Create a file with content, returning false when it already exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except FileExistsError:
        return False
    return True


def initialize_usw(project: Path) -> list[tuple[Path, bool]]:
    """Create USW project files without overwriting existing files."""
    project_root = find_project_root(project)
    sync_file = project_root / "usw" / "SYNC.md"
    hello_world_file = project_root / "hello_world.py"

    return [
        (sync_file, create_file(sync_file, SYNC_CONTENT)),
        (
            hello_world_file,
            create_file(hello_world_file, HELLO_WORLD_CONTENT),
        ),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create usw/SYNC.md and hello_world.py in the current project "
            "without overwriting them."
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
