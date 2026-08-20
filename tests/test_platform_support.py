"""Platform support that cannot be verified on the developer's own machine.

These tests simulate the absence of POSIX-only modules so a Windows-breaking
import cannot land unnoticed. They are a guard, not a substitute for the
`windows-latest` job, which is the only real verification of the platform.
"""

import contextlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).parents[1]
HANDOFF_SCRIPT = ROOT / "skills/usw-manage-handoff/scripts/handoff_state.py"
HANDOFF_SPEC = importlib.util.spec_from_file_location(
    "platform_handoff", HANDOFF_SCRIPT
)
HANDOFF = importlib.util.module_from_spec(HANDOFF_SPEC)
assert HANDOFF_SPEC.loader is not None
sys.modules[HANDOFF_SPEC.name] = HANDOFF
HANDOFF_SPEC.loader.exec_module(HANDOFF)

IMPORT_WITHOUT_MODULE = """
import importlib.util
import sys


class Blocker:
    def __init__(self, blocked):
        self.blocked = blocked

    def find_spec(self, name, path=None, target=None):
        if name == self.blocked:
            # Must be ModuleNotFoundError, not ImportError: that is what a truly
            # absent module raises, and stdlib guards catch only the subclass.
            raise ModuleNotFoundError(f"no {name} on this platform", name=name)
        return None


blocked, target = sys.argv[1], sys.argv[2]
sys.modules.pop(blocked, None)
sys.meta_path.insert(0, Blocker(blocked))

spec = importlib.util.spec_from_file_location("probe", target)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module  # dataclasses resolves __module__ through this
spec.loader.exec_module(module)
print("imported")
"""


def skill_scripts() -> list[Path]:
    return sorted((ROOT / "skills").glob("*/scripts/*.py"))


class ImportsWithoutPosixModulesTests(unittest.TestCase):
    def test_every_skill_script_imports_without_fcntl(self):
        """`import fcntl` at module level breaks every run on Windows."""

        scripts = skill_scripts()
        self.assertTrue(scripts, "no skill scripts were discovered")

        for script in scripts:
            with self.subTest(script=script.relative_to(ROOT).as_posix()):
                completed = subprocess.run(
                    [sys.executable, "-c", IMPORT_WITHOUT_MODULE, "fcntl", str(script)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    0,
                    completed.returncode,
                    f"import failed without fcntl:\n{completed.stderr}",
                )

    @unittest.skipIf(
        os.name == "nt",
        "on Windows the stdlib itself imports msvcrt, so blocking it breaks "
        "subprocess rather than testing the module under probe",
    )
    def test_every_skill_script_imports_without_msvcrt(self):
        """The Windows-only module must be equally optional on POSIX."""

        for script in skill_scripts():
            with self.subTest(script=script.relative_to(ROOT).as_posix()):
                completed = subprocess.run(
                    [sys.executable, "-c", IMPORT_WITHOUT_MODULE, "msvcrt", str(script)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, completed.returncode, completed.stderr)


class FakeMsvcrt:
    """Stands in for the Windows locking primitive, which POSIX cannot provide."""

    LK_NBLCK = 1
    LK_UNLCK = 0

    def __init__(self, *, contended: bool = False) -> None:
        self.contended = contended
        self.calls: list[tuple[int, int]] = []

    def locking(self, descriptor: int, mode: int, length: int) -> None:
        self.calls.append((mode, length))
        if mode == self.LK_NBLCK and self.contended:
            raise OSError("another process holds the lock")


class WindowsLockingTests(unittest.TestCase):
    """Branch coverage for the path this machine cannot execute for real."""

    def workspace(self, directory: str) -> Path:
        root = Path(directory)
        (root / ".usw").mkdir()
        return root

    def as_windows(self, fake: FakeMsvcrt):
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(
                HANDOFF.SAFE_ACCESS,
                "supports_descriptor_relative_access",
                mock.Mock(return_value=False),
            )
        )
        stack.enter_context(
            mock.patch.multiple(HANDOFF, msvcrt=fake, LOCK_RETRY_DELAY=0)
        )
        return stack

    def test_lock_file_is_used_when_descriptors_are_unavailable(self):
        fake = FakeMsvcrt()
        with tempfile.TemporaryDirectory() as directory:
            root = self.workspace(directory)
            with self.as_windows(fake):
                with HANDOFF._locked_local_directory(root) as (path, directory):
                    self.assertEqual(root / ".usw", path)
                    self.assertIsInstance(directory, HANDOFF._PathnameDirectory)
                    self.assertTrue((root / ".usw" / ".lock").is_file())

        self.assertEqual(
            [(FakeMsvcrt.LK_NBLCK, 1), (FakeMsvcrt.LK_UNLCK, 1)], fake.calls
        )

    def test_missing_workspace_still_reports_missing_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.as_windows(FakeMsvcrt()):
                with self.assertRaises(HANDOFF.HandoffError) as raised:
                    with HANDOFF._locked_local_directory(Path(directory)):
                        pass

        self.assertEqual("missing_handoff", raised.exception.code)

    def test_contended_lock_fails_instead_of_hanging(self):
        fake = FakeMsvcrt(contended=True)
        with tempfile.TemporaryDirectory() as directory:
            root = self.workspace(directory)
            with self.as_windows(fake):
                with self.assertRaises(HANDOFF.HandoffError) as raised:
                    with HANDOFF._locked_local_directory(root):
                        pass

        self.assertEqual("handoff_locked", raised.exception.code)
        self.assertEqual(HANDOFF.LOCK_RETRY_LIMIT, len(fake.calls))

    def test_posix_keeps_descriptor_relative_locking(self):
        """The stronger backend must stay selected wherever it is available."""

        if not HANDOFF.SAFE_ACCESS.supports_descriptor_relative_access():
            self.skipTest("platform has no descriptor-relative access")

        with tempfile.TemporaryDirectory() as directory:
            root = self.workspace(directory)
            with HANDOFF._locked_local_directory(root) as (path, handle):
                self.assertEqual(root / ".usw", path)
                self.assertIsInstance(handle, HANDOFF._DescriptorDirectory)
                self.assertIsInstance(handle.descriptor, int)
            self.assertFalse((root / ".usw" / ".lock").exists())


class PathnameBackendTests(unittest.TestCase):
    """The backend Windows will use, exercised on this machine.

    Only the Windows-specific reparse-point attribute cannot be reproduced here;
    everything else is ordinary path handling and runs identically.
    """

    def directory(self, path: Path) -> "HANDOFF._PathnameDirectory":
        return HANDOFF._PathnameDirectory(path)

    def test_reads_and_writes_a_regular_file(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            directory = self.directory(root)
            directory.write_exclusive("state.md", "content\n", 0o600)

            self.assertEqual("content\n", directory.read_text("state.md"))
            directory.replace("state.md", "moved.md")
            self.assertEqual("content\n", directory.read_text("moved.md"))
            directory.unlink("moved.md")
            self.assertFalse((root / "moved.md").exists())

    def test_existing_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = self.directory(Path(raw))
            directory.write_exclusive("state.md", "first\n", 0o600)
            with self.assertRaises(FileExistsError):
                directory.write_exclusive("state.md", "second\n", 0o600)

    def test_symbolic_link_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            outside = root / "outside.md"
            outside.write_text("secret\n", encoding="utf-8", newline="\n")
            (root / "workspace").mkdir()
            os.symlink(outside, root / "workspace" / "link.md")

            directory = self.directory(root / "workspace")
            with self.assertRaises(OSError):
                directory.read_text("link.md")

    def test_linked_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "target").mkdir()
            (root / "workspace").mkdir()
            os.symlink(root / "target", root / "workspace" / "handoffs")

            with self.assertRaises(OSError):
                self.directory(root / "workspace").child_directory("handoffs")

    def test_wrong_filesystem_type_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "state.md").mkdir()
            with self.assertRaises(OSError):
                self.directory(root).read_text("state.md")

    def test_names_crossing_a_directory_boundary_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = self.directory(Path(raw))
            for name in ("..", ".", "", "sub/state.md", f"sub{os.sep}state.md"):
                with self.subTest(name=name):
                    with self.assertRaises(OSError):
                        directory.read_text(name)

    def test_missing_entry_reports_not_found(self):
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(FileNotFoundError):
                self.directory(Path(raw)).read_text("absent.md")


class HandoffThroughPathnameBackendTests(unittest.TestCase):
    """The whole routed-handoff cycle without dir_fd — what Windows will run."""

    IDENTITY = "usw-markdown:shared:" + "a" * 64

    def as_pathname_platform(self):
        return mock.patch.object(
            HANDOFF.SAFE_ACCESS,
            "supports_descriptor_relative_access",
            mock.Mock(return_value=False),
        )

    def initialize(self, raw: str) -> Path:
        project = Path(raw)
        (project / "usw.yaml").write_text(
            "schema_version: 1\nhandoff: true\n", encoding="utf-8"
        )
        local = project / ".usw"
        local.mkdir()
        (local / "HANDOFF.md").write_text(HANDOFF.render_idle(), encoding="utf-8")
        return project

    def test_begin_outcome_and_finish_complete_without_descriptors(self):
        fake = FakeMsvcrt()
        with tempfile.TemporaryDirectory() as raw:
            project = self.initialize(raw)
            with self.as_pathname_platform(), mock.patch.multiple(
                HANDOFF, msvcrt=fake, LOCK_RETRY_DELAY=0
            ):
                _, operation = HANDOFF.begin_handoff(
                    project,
                    "chat-review",
                    "shared",
                    self.IDENTITY,
                    "Review the payment change",
                    summary="Review payment change",
                )
                document = project / ".usw" / HANDOFF.operation_relative_path(operation)
                self.assertTrue(document.is_file())
                self.assertIn("in_progress", document.read_text(encoding="utf-8"))

                HANDOFF.outcome_handoff(
                    project,
                    "completed",
                    operation=operation,
                    done="Review completed.",
                    position="At the terminal boundary.",
                    next_action="None.",
                    blocker="None.",
                )
                self.assertIn("completed", document.read_text(encoding="utf-8"))

                HANDOFF.finish_handoff(project, operation)
                self.assertFalse(document.exists())

            router = (project / ".usw" / "HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn(HANDOFF.ROUTER_TABLE_EMPTY, router)


class BackendSelectionTests(unittest.TestCase):
    def test_selection_probes_capability_rather_than_platform_name(self):
        access = HANDOFF.SAFE_ACCESS
        with mock.patch.object(access.os, "supports_dir_fd", set()):
            self.assertFalse(access.supports_descriptor_relative_access())

        with mock.patch.object(access, "fcntl", None):
            self.assertFalse(access.supports_descriptor_relative_access())

    def test_posix_selects_the_stronger_backend(self):
        if sys.platform.startswith("win"):
            self.skipTest("POSIX-only expectation")
        self.assertTrue(HANDOFF.SAFE_ACCESS.supports_descriptor_relative_access())


class SelectedBackendIsVisibleTests(unittest.TestCase):
    """A weaker backend than this platform can support must not pass silently.

    The concurrency guarantee differs between backends, so a silent downgrade
    would quietly weaken safety on a platform that could hold the stronger one.
    Reported to stdout as well, so every suite run states what it exercised.
    """

    def selected_backend(self) -> tuple[str, type]:
        with tempfile.TemporaryDirectory() as raw:
            directory = HANDOFF.SAFE_ACCESS.open_safe_directory(Path(raw))
            try:
                return type(directory).__name__, type(directory)
            finally:
                directory.close()

    def test_selected_backend_matches_platform_capability(self):
        access = HANDOFF.SAFE_ACCESS
        name, backend = self.selected_backend()
        print(f"\nsafe-access backend: {name}", flush=True)

        if access.supports_descriptor_relative_access():
            self.assertIs(
                access.DescriptorDirectory,
                backend,
                "platform supports dir_fd but the weaker backend was selected",
            )
        else:
            self.assertIs(access.PathnameDirectory, backend)

    def test_capability_probe_agrees_with_the_interpreter(self):
        """A downgrade must come from a real missing capability, not a bug."""

        access = HANDOFF.SAFE_ACCESS
        expected = bool(os.supports_dir_fd) and access.fcntl is not None
        self.assertEqual(expected, access.supports_descriptor_relative_access())


if __name__ == "__main__":
    unittest.main()
