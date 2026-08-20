#!/usr/bin/env python3
"""One safe filesystem boundary, with a backend per platform.

Every USW component reads and writes workspace state through this module rather
than calling the filesystem directly, so platform behavior lives in one place.

Two backends with the same surface:

`DescriptorDirectory` traverses and reads descriptor-relative. Once a component
is trusted it is never reached by pathname again, so it cannot be swapped by a
concurrent process afterwards.

`PathnameDirectory` serves platforms without `dir_fd`, which is every Windows
build. It rejects links and reparse points per entry and refuses names that
cross a directory boundary, but it must address entries by pathname, so it
narrows rather than closes the window between check and use. That difference is
deliberate and disclosed; it is not an oversight. See
openspec/changes/support-windows-execution/design.md.

Methods raise the ordinary `OSError` family — `FileNotFoundError`,
`FileExistsError`, `NotADirectoryError` — so each caller keeps translating
failures into its own error type and messages, identically on both platforms.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path, PurePath

try:  # POSIX only.
    import fcntl
except ImportError:  # pragma: no cover - selected by platform
    fcntl = None


def supports_descriptor_relative_access() -> bool:
    """Whether this platform can traverse descriptor-relative.

    Probes the capability that actually decides the implementation rather than
    branching on `os.name`, so a POSIX platform without `dir_fd` also falls back.
    """

    return bool(os.supports_dir_fd) and fcntl is not None


def require_simple_name(name: str) -> str:
    """Names that would cross a directory boundary never reach the filesystem."""

    if not name or name in {".", ".."} or os.sep in name or "/" in name:
        raise OSError(f"unsafe entry name: {name}")
    if os.altsep and os.altsep in name:
        raise OSError(f"unsafe entry name: {name}")
    return name


def reject_link(path: Path) -> os.stat_result:
    """Reject a link before it is used.

    Covers Windows junctions as well as symbolic links: a junction is not a
    symlink but redirects just as effectively, so checking `S_ISLNK` alone would
    miss it.
    """

    info = os.lstat(path)  # FileNotFoundError propagates to the caller
    if stat.S_ISLNK(info.st_mode):
        raise OSError(f"unsafe link component: {path}")
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if reparse and getattr(info, "st_file_attributes", 0) & reparse:
        raise OSError(f"unsafe reparse point: {path}")
    return info


class SafeDirectory:
    """Safe access to the contents of one directory."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def close(self) -> None:
        return None

    def read_text(self, name: str) -> str:
        return self.read_bytes(name).decode("utf-8")


class DescriptorDirectory(SafeDirectory):
    DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(
        os, "O_NOFOLLOW", 0
    )
    EXCLUSIVE_FLAGS = (
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    )
    READ_FLAGS = (
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    )

    def __init__(self, path: Path, descriptor: int) -> None:
        super().__init__(path)
        self.descriptor = descriptor

    def child_directory(self, name: str) -> "DescriptorDirectory":
        descriptor = os.open(
            require_simple_name(name), self.DIRECTORY_FLAGS, dir_fd=self.descriptor
        )
        child = DescriptorDirectory(self.path / name, descriptor)
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            child.close()
            raise NotADirectoryError(f"not a directory: {child.path}")
        return child

    def entry_mode(self, name: str) -> int | None:
        try:
            return os.stat(
                require_simple_name(name),
                dir_fd=self.descriptor,
                follow_symlinks=False,
            ).st_mode
        except FileNotFoundError:
            return None

    def read_bytes(self, name: str) -> bytes:
        descriptor = os.open(
            require_simple_name(name), self.READ_FLAGS, dir_fd=self.descriptor
        )
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError(f"not a regular file: {self.path / name}")
            with os.fdopen(descriptor, "rb", closefd=False) as source:
                return source.read()
        finally:
            os.close(descriptor)

    def make_directory(self, name: str, mode: int) -> None:
        os.mkdir(require_simple_name(name), mode, dir_fd=self.descriptor)

    def write_exclusive(self, name: str, content: str, mode: int) -> None:
        descriptor = os.open(
            require_simple_name(name), self.EXCLUSIVE_FLAGS, mode, dir_fd=self.descriptor
        )
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

    def replace(self, source: str, target: str) -> None:
        os.replace(
            require_simple_name(source),
            require_simple_name(target),
            src_dir_fd=self.descriptor,
            dst_dir_fd=self.descriptor,
        )

    def sync(self) -> None:
        os.fsync(self.descriptor)

    def unlink(self, name: str) -> None:
        os.unlink(require_simple_name(name), dir_fd=self.descriptor)

    def close(self) -> None:
        os.close(self.descriptor)


class PathnameDirectory(SafeDirectory):
    def child_directory(self, name: str) -> "PathnameDirectory":
        path = self.path / require_simple_name(name)
        info = reject_link(path)
        if not stat.S_ISDIR(info.st_mode):
            raise NotADirectoryError(f"not a directory: {path}")
        return PathnameDirectory(path)

    def entry_mode(self, name: str) -> int | None:
        try:
            return os.lstat(self.path / require_simple_name(name)).st_mode
        except FileNotFoundError:
            return None

    def read_bytes(self, name: str) -> bytes:
        path = self.path / require_simple_name(name)
        info = reject_link(path)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(f"not a regular file: {path}")
        with open(path, "rb") as source:
            return source.read()

    def make_directory(self, name: str, mode: int) -> None:
        os.mkdir(self.path / require_simple_name(name), mode)

    def write_exclusive(self, name: str, content: str, mode: int) -> None:
        path = self.path / require_simple_name(name)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

    def replace(self, source: str, target: str) -> None:
        os.replace(
            self.path / require_simple_name(source),
            self.path / require_simple_name(target),
        )

    def sync(self) -> None:
        # A directory cannot be opened for fsync without dir_fd. File contents
        # are still flushed and fsynced individually in write_exclusive.
        return None

    def unlink(self, name: str) -> None:
        os.unlink(self.path / require_simple_name(name))


def open_safe_directory(path: Path) -> SafeDirectory:
    """Open one directory through the backend this platform supports."""

    if not supports_descriptor_relative_access():
        info = reject_link(path)
        if not stat.S_ISDIR(info.st_mode):
            raise NotADirectoryError(f"not a directory: {path}")
        return PathnameDirectory(path)

    descriptor = os.open(path, DescriptorDirectory.DIRECTORY_FLAGS)
    return DescriptorDirectory(path, descriptor)


def traverse(root: SafeDirectory, relative: PurePath) -> SafeDirectory:
    """Walk one contained relative path, one checked component at a time.

    The caller owns closing the returned directory. Intermediate directories are
    closed as the walk proceeds, so a failure part-way leaks nothing.
    """

    current = root
    opened: SafeDirectory | None = None
    try:
        for part in relative.parts:
            child = current.child_directory(part)
            if opened is not None:
                opened.close()
            opened = child
            current = child
        return opened if opened is not None else root
    except BaseException:
        if opened is not None:
            opened.close()
        raise
