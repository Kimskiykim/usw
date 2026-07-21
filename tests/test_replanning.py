import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = ROOT / "skills/usw-initialize-project/scripts/artifact_contract.py"
SPEC = importlib.util.spec_from_file_location("replanning_artifacts", SCRIPT_PATH)
ARTIFACTS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = ARTIFACTS
SPEC.loader.exec_module(ARTIFACTS)


class ReplanningTests(unittest.TestCase):
    def git(self, project: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(project), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def project(self, directory: str) -> Path:
        project = Path(directory)
        self.git(project, "init", "--quiet")
        self.git(project, "config", "user.name", "USW Tests")
        self.git(project, "config", "user.email", "usw@example.invalid")
        (project / ".gitignore").write_text("ignored.txt\n.usw/\n", encoding="utf-8")
        (project / "product.txt").write_text("one\n", encoding="utf-8")
        (project / "usw/changes").mkdir(parents=True)
        (project / "usw/changes/state.md").write_text("workflow\n", encoding="utf-8")
        self.git(project, "add", ".gitignore", "product.txt", "usw/changes/state.md")
        self.git(project, "commit", "--quiet", "-m", "initial")
        return project

    def identity(self, project: Path) -> str:
        return ARTIFACTS.source_identity(project, ["usw"])

    def test_source_identity_is_stable_and_has_normative_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            first = self.identity(project)
            second = self.identity(project)
            manifest = ARTIFACTS.build_source_manifest(project, ["usw"])

            self.assertEqual(first, second)
            self.assertRegex(first, r"^usw-source-v1:[0-9a-f]{64}$")
            self.assertTrue(manifest.startswith(b"USW-SOURCE-V1\0"))

    def test_product_changes_affect_identity_but_workflow_and_head_do_not(self):
        mutations = {
            "unstaged": lambda project: (project / "product.txt").write_text("two\n"),
            "untracked": lambda project: (project / "new.txt").write_text("new\n"),
            "staged": lambda project: (
                (project / "staged.txt").write_text("staged\n"),
                self.git(project, "add", "staged.txt"),
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                project = self.project(directory)
                before = self.identity(project)
                mutate(project)
                self.assertNotEqual(before, self.identity(project))

        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            before = self.identity(project)
            (project / "usw/changes/state.md").write_text("changed workflow\n")
            (project / ".usw").mkdir()
            (project / ".usw/HANDOFF.md").write_text("local\n")
            self.assertEqual(before, self.identity(project))
            self.git(project, "add", "usw/changes/state.md")
            self.git(project, "commit", "--quiet", "-m", "workflow only")
            self.assertEqual(before, self.identity(project))

    def test_ignored_untracked_file_does_not_affect_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            before = self.identity(project)
            (project / "ignored.txt").write_text("ignored\n", encoding="utf-8")
            self.assertEqual(before, self.identity(project))

    @unittest.skipIf(os.name == "nt", "POSIX mode and symlink semantics required")
    def test_executable_mode_and_symlink_target_affect_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            script = project / "tool.sh"
            script.write_text("#!/bin/sh\n", encoding="utf-8")
            link = project / "current-tool"
            os.symlink("tool.sh", link)
            self.git(project, "add", "tool.sh", "current-tool")
            plain = self.identity(project)

            script.chmod(script.stat().st_mode | stat.S_IXUSR)
            executable = self.identity(project)
            self.assertNotEqual(plain, executable)

            link.unlink()
            os.symlink("other.sh", link)
            self.assertNotEqual(executable, self.identity(project))

    def test_in_scope_finding_reopens_same_task_and_appends_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks = root / "tasks.md"
            task = root / "task.md"
            tasks.write_text("- [x] 7 [Fix](tasks/7-fix/task.md)\n", encoding="utf-8")
            task.write_text(
                "# Task 7\n\n## Artifact model\n\n- `v1`\n\n"
                "## Milestone log\n\n"
                "| Attempt | Trigger | Contract | Source | Outcome | References |\n"
                "|---|---|---|---|---|---|\n"
                "| 1 | created | `c1` | `s1` | complete | none |\n",
                encoding="utf-8",
            )

            outcome = ARTIFACTS.reopen_task(
                tasks,
                task,
                task_id="7",
                finding_scope="in_scope",
                contract_identity="c1",
                source_identity_value="s2",
                receipt_reference="review-2",
            )

            self.assertEqual("reopened", outcome)
            self.assertIn("- [ ] 7 [Fix]", tasks.read_text())
            self.assertIn("| 2 | blocking finding |", task.read_text())
            self.assertIn("review-2", task.read_text())

    def test_new_scope_requires_approval_and_does_not_mutate_task(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tasks = root / "tasks.md"
            task = root / "task.md"
            original_index = "- [x] 7 [Fix](tasks/7-fix/task.md)\n"
            original_task = "## Milestone log\n"
            tasks.write_text(original_index, encoding="utf-8")
            task.write_text(original_task, encoding="utf-8")

            outcome = ARTIFACTS.reopen_task(
                tasks,
                task,
                task_id="7",
                finding_scope="new_scope",
                contract_identity="c1",
                source_identity_value="s1",
                receipt_reference="review-2",
            )

            self.assertEqual("user_approval_required_for_new_task", outcome)
            self.assertEqual(original_index, tasks.read_text())
            self.assertEqual(original_task, task.read_text())


if __name__ == "__main__":
    unittest.main()
