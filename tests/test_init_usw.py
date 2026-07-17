import importlib.util
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "skills"
    / "usw-initialize-project"
    / "scripts"
    / "init_usw.py"
)
SPEC = importlib.util.spec_from_file_location("init_usw", SCRIPT_PATH)
INIT_USW = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(INIT_USW)


class InitializeUswTests(unittest.TestCase):
    def test_creates_openspec_workspace_and_local_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)

            results = INIT_USW.initialize_usw(project)
            (
                (openspec_directory, openspec_created),
                (specs_directory, specs_created),
                (changes_directory, changes_created),
                (agents_file, agents_created),
                (local_ignore_file, local_ignore_created),
                (handoff_file, handoff_created),
            ) = results

            self.assertTrue(openspec_created)
            self.assertEqual(project.resolve() / "openspec", openspec_directory)
            self.assertTrue(specs_created)
            self.assertEqual(openspec_directory / "specs", specs_directory)
            self.assertTrue(changes_created)
            self.assertEqual(openspec_directory / "changes", changes_directory)

            self.assertTrue(agents_created)
            self.assertEqual(openspec_directory / "AGENTS.md", agents_file)
            agents_content = agents_file.read_text(encoding="utf-8")
            self.assertIn("# OpenSpec workflow\n", agents_content)
            self.assertIn("completion checkboxes only in `tasks.md`", agents_content)
            self.assertIn("tasks/<task-id>-<slug>/task.md", agents_content)

            self.assertTrue(local_ignore_created)
            self.assertEqual(project.resolve() / ".usw" / ".gitignore", local_ignore_file)
            self.assertEqual("*\n", local_ignore_file.read_text(encoding="utf-8"))
            self.assertTrue(handoff_created)
            self.assertEqual(project.resolve() / ".usw" / "HANDOFF.md", handoff_file)
            handoff_content = handoff_file.read_text(encoding="utf-8")
            self.assertIn("# Developer Handoff\n", handoff_content)
            self.assertIn("- Status: idle\n", handoff_content)
            self.assertIn("No active work.\n", handoff_content)

            self.assertFalse((project / "usw" / "SYNC.md").exists())
            self.assertFalse((project / "hello_world.py").exists())

    def test_uses_nearest_git_root(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".git").mkdir()
            nested = project / "src" / "feature"
            nested.mkdir(parents=True)

            results = INIT_USW.initialize_usw(nested)

            for path, _ in results:
                self.assertTrue(path.is_relative_to(project.resolve()))
            self.assertEqual(project.resolve() / "openspec", results[0][0])
            self.assertEqual(project.resolve() / ".usw" / "HANDOFF.md", results[-1][0])

    def test_adopts_existing_openspec_workspace_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            openspec = project / "openspec"
            specs = openspec / "specs"
            specs.mkdir(parents=True)
            agents_file = openspec / "AGENTS.md"
            agents_file.write_text("existing OpenSpec instructions\n", encoding="utf-8")

            results = INIT_USW.initialize_usw(project)

            self.assertFalse(results[0][1])
            self.assertFalse(results[1][1])
            self.assertTrue(results[2][1])
            self.assertFalse(results[3][1])
            self.assertEqual(
                "existing OpenSpec instructions\n",
                agents_file.read_text(encoding="utf-8"),
            )
            self.assertTrue((openspec / "changes").is_dir())

    def test_second_initialization_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            first_results = INIT_USW.initialize_usw(project)
            first_handoff = (project / ".usw" / "HANDOFF.md").read_text(
                encoding="utf-8"
            )

            second_results = INIT_USW.initialize_usw(project)

            self.assertTrue(all(created for _, created in first_results))
            self.assertTrue(all(not created for _, created in second_results))
            self.assertEqual(
                first_handoff,
                (project / ".usw" / "HANDOFF.md").read_text(encoding="utf-8"),
            )

    def test_does_not_overwrite_existing_local_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            local_ignore_file = project / ".usw" / ".gitignore"
            local_ignore_file.parent.mkdir()
            local_ignore_file.write_text("existing ignore\n", encoding="utf-8")
            handoff_file = project / ".usw" / "HANDOFF.md"
            handoff_file.write_text("existing handoff\n", encoding="utf-8")

            results = INIT_USW.initialize_usw(project)

            self.assertFalse(results[-2][1])
            self.assertFalse(results[-1][1])
            self.assertEqual(
                "existing ignore\n", local_ignore_file.read_text(encoding="utf-8")
            )
            self.assertEqual(
                "existing handoff\n", handoff_file.read_text(encoding="utf-8")
            )

    def test_rejects_symlinked_local_state_without_writing_outside_project(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            outside = Path(directory) / "outside"
            project.mkdir()
            outside.mkdir()
            os.symlink(outside, project / ".usw")

            with self.assertRaisesRegex(OSError, "symbolic links"):
                INIT_USW.initialize_usw(project)

            self.assertFalse((outside / ".gitignore").exists())
            self.assertFalse((outside / "HANDOFF.md").exists())
            self.assertFalse((project / "openspec").exists())

    def test_rejects_symlinked_openspec_without_writing_outside_project(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            outside = Path(directory) / "outside"
            project.mkdir()
            outside.mkdir()
            os.symlink(outside, project / "openspec")

            with self.assertRaisesRegex(OSError, "symbolic links"):
                INIT_USW.initialize_usw(project)

            self.assertFalse((outside / "specs").exists())
            self.assertFalse((outside / "changes").exists())
            self.assertFalse((project / ".usw").exists())

    def test_rejects_existing_ignore_that_exposes_local_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            subprocess.run(
                ["git", "init", "--quiet", str(project)],
                check=True,
                capture_output=True,
                text=True,
            )
            local_state = project / ".usw"
            local_state.mkdir()
            (local_state / ".gitignore").write_text("*.tmp\n", encoding="utf-8")

            with self.assertRaisesRegex(OSError, "does not ignore USW local state"):
                INIT_USW.initialize_usw(project)

            self.assertFalse((local_state / "HANDOFF.md").exists())
            self.assertFalse((project / "openspec").exists())

    def test_accepts_existing_ignore_that_keeps_local_state_private(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            subprocess.run(
                ["git", "init", "--quiet", str(project)],
                check=True,
                capture_output=True,
                text=True,
            )
            local_state = project / ".usw"
            local_state.mkdir()
            (local_state / ".gitignore").write_text("*\n", encoding="utf-8")

            INIT_USW.initialize_usw(project)

            self.assertTrue((local_state / "HANDOFF.md").is_file())

    def test_rejects_tracked_local_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            subprocess.run(
                ["git", "init", "--quiet", str(project)],
                check=True,
                capture_output=True,
                text=True,
            )
            local_state = project / ".usw"
            local_state.mkdir()
            (local_state / ".gitignore").write_text("*\n", encoding="utf-8")
            handoff = local_state / "HANDOFF.md"
            handoff.write_text("existing handoff\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "--force", ".usw/HANDOFF.md"],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )

            with self.assertRaisesRegex(OSError, "local state is tracked by Git"):
                INIT_USW.initialize_usw(project)

            self.assertFalse((project / "openspec").exists())

    def test_local_state_is_ignored_but_openspec_is_visible_to_git(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            subprocess.run(
                ["git", "init", "--quiet", str(project)],
                check=True,
                capture_output=True,
                text=True,
            )

            INIT_USW.initialize_usw(project)

            result = subprocess.run(
                ["git", "status", "--short", "--untracked-files=all"],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertNotIn(".usw/", result.stdout)
            self.assertIn("openspec/AGENTS.md", result.stdout)

    def test_renders_initial_handoff_with_supplied_timestamp(self):
        updated_at = datetime(2026, 7, 17, 9, 30, tzinfo=timezone.utc)

        content = INIT_USW.render_handoff(updated_at)

        self.assertEqual(
            "# Developer Handoff\n\n"
            "- Updated: 2026-07-17T09:30:00+00:00\n"
            "- Status: idle\n\n"
            "## Active work\n\n"
            "No active work.\n",
            content,
        )

    def test_fails_when_openspec_path_is_a_file(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "openspec").write_text("not a directory", encoding="utf-8")

            with self.assertRaises(NotADirectoryError):
                INIT_USW.initialize_usw(project)


if __name__ == "__main__":
    unittest.main()
