import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "skills"
    / "usw-manage-handoff"
    / "scripts"
    / "handoff_state.py"
)
INIT_SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "skills"
    / "usw-initialize-project"
    / "scripts"
    / "init_usw.py"
)
SPEC = importlib.util.spec_from_file_location("handoff_state", SCRIPT_PATH)
HANDOFF_STATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = HANDOFF_STATE
SPEC.loader.exec_module(HANDOFF_STATE)


def active_handoff(
    *,
    status: str = "paused",
    next_action: str = "Run the focused unit test.",
) -> str:
    return (
        "# Developer Handoff\n\n"
        "- Updated: 2026-07-17T12:00:00+03:00\n"
        f"- Status: {status}\n"
        "- Task: Implement local resume flow\n\n"
        "## Done\n\n"
        "- Added the handoff validator.\n\n"
        "## Changed areas\n\n"
        "- `skills/usw-manage-handoff/`\n\n"
        "## Verification\n\n"
        "- `python3 -m unittest tests.test_handoff_state` -> passed\n\n"
        "## Risks / blockers\n\n"
        "- None known.\n\n"
        "## Next action\n\n"
        f"{next_action}\n\n"
        "## References\n\n"
        "- `dev/SDD_PROVIDER_IDEA.md`\n"
    )


class HandoffStateTests(unittest.TestCase):
    def run_git(self, project: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(project), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def initialize_project(self, project: Path) -> Path:
        handoff = project / ".usw" / "HANDOFF.md"
        handoff.parent.mkdir()
        (handoff.parent / ".gitignore").write_text("*\n", encoding="utf-8")
        handoff.write_text(HANDOFF_STATE.render_idle(), encoding="utf-8")
        return handoff

    def initialize_git_project(self, project: Path) -> Path:
        self.run_git(project, "init", "--quiet")
        self.run_git(project, "config", "core.trustctime", "false")
        tracked = project / "tracked.txt"
        tracked.write_bytes(b"alpha\n")
        old_timestamp_ns = 1_600_000_000_000_000_000
        os.utime(tracked, ns=(old_timestamp_ns, old_timestamp_ns))
        self.run_git(project, "add", "tracked.txt")
        self.run_git(
            project,
            "-c",
            "user.name=USW Tests",
            "-c",
            "user.email=usw-tests@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "initial",
        )
        self.initialize_project(project)
        return tracked

    def assert_generated_snapshot(self, content: str) -> None:
        self.assertEqual(1, content.count("## Source snapshot"))
        self.assertIn("- Schema: `usw-source-v1`", content)
        self.assertRegex(content, r"- State: (complete|unavailable)")
        self.assertRegex(
            content,
            r"- Source: (`sha256:[0-9a-f]{64}`|unavailable)",
        )

    def add_intent_to_add(self, project: Path) -> None:
        (project / "intent.txt").write_text("intent\n", encoding="utf-8")
        self.run_git(project, "add", "--intent-to-add", "intent.txt")

    def make_stat_preserving_edit(self, project: Path) -> None:
        tracked = project / "tracked.txt"
        before = tracked.stat()
        tracked.write_bytes(b"bravo\n")
        os.utime(tracked, ns=(before.st_atime_ns, before.st_mtime_ns))
        after = tracked.stat()
        self.assertEqual(before.st_size, after.st_size)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self.assertEqual(
            "",
            self.run_git(
                project,
                "status",
                "--porcelain=v1",
                "--",
                "tracked.txt",
            ).stdout,
        )

    def capture_complete_snapshot(self, project: Path):
        snapshot = HANDOFF_STATE.capture_source_snapshot(project)
        self.assertEqual("complete", snapshot.state, snapshot.problem)
        return snapshot

    def report_after_change(self, project: Path, mutate):
        saved = self.capture_complete_snapshot(project)
        mutate(project)
        return HANDOFF_STATE.compare_source_snapshots(
            saved,
            self.capture_complete_snapshot(project),
        )

    def test_renders_and_validates_idle_handoff(self):
        updated_at = datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc)

        content = HANDOFF_STATE.render_idle(updated_at)

        self.assertEqual(
            "# Developer Handoff\n\n"
            "- Updated: 2026-07-17T10:00:00+00:00\n"
            "- Status: idle\n\n"
            "## Active work\n\n"
            "No active work.\n",
            content,
        )
        self.assertEqual("idle", HANDOFF_STATE.validate_handoff(content))

    def test_validates_active_handoff(self):
        self.assertEqual(
            "paused", HANDOFF_STATE.validate_handoff(active_handoff())
        )

    def test_rejects_missing_active_section(self):
        content = active_handoff().replace(
            "## Risks / blockers\n\n- None known.\n\n", ""
        )

        with self.assertRaisesRegex(
            HANDOFF_STATE.HandoffError, "Active sections must appear exactly"
        ):
            HANDOFF_STATE.validate_handoff(content)

    def test_rejects_multiple_next_actions(self):
        content = active_handoff(next_action="First action.\nSecond action.")

        with self.assertRaisesRegex(
            HANDOFF_STATE.HandoffError, "exactly one non-empty line"
        ):
            HANDOFF_STATE.validate_handoff(content)

    def test_rejects_unstructured_verification(self):
        content = active_handoff().replace(
            " -> passed", " completed successfully"
        )

        with self.assertRaisesRegex(
            HANDOFF_STATE.HandoffError, "Verification entries must end"
        ):
            HANDOFF_STATE.validate_handoff(content)

    def test_saves_valid_candidate_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            handoff = self.initialize_project(project)
            candidate = project / ".usw" / "HANDOFF.next.md"
            candidate.write_text(active_handoff(), encoding="utf-8")

            saved_path, status = HANDOFF_STATE.save_handoff(project, candidate)

            self.assertEqual(handoff.resolve(), saved_path)
            self.assertEqual("paused", status)
            saved_content = handoff.read_text(encoding="utf-8")
            self.assertIn("- Task: Implement local resume flow", saved_content)
            self.assert_generated_snapshot(saved_content)
            self.assertFalse(candidate.exists())

    def test_invalid_candidate_does_not_replace_current_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            handoff = self.initialize_project(project)
            original = handoff.read_text(encoding="utf-8")
            candidate = project / ".usw" / "HANDOFF.next.md"
            candidate.write_text("invalid\n", encoding="utf-8")

            with self.assertRaises(HANDOFF_STATE.HandoffError):
                HANDOFF_STATE.save_handoff(project, candidate)

            self.assertEqual(original, handoff.read_text(encoding="utf-8"))
            self.assertTrue(candidate.exists())

    def test_rejects_symlinked_candidate_without_deleting_its_target(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            handoff = self.initialize_project(project)
            original = handoff.read_text(encoding="utf-8")
            victim = project / "victim.md"
            victim.write_text(active_handoff(), encoding="utf-8")
            candidate = project / ".usw" / "HANDOFF.next.md"
            os.symlink(victim, candidate)

            with self.assertRaisesRegex(HANDOFF_STATE.HandoffError, "symbolic link"):
                HANDOFF_STATE.save_handoff(project, candidate)

            self.assertEqual(active_handoff(), victim.read_text(encoding="utf-8"))
            self.assertEqual(original, handoff.read_text(encoding="utf-8"))
            self.assertTrue(candidate.is_symlink())

    def test_rejects_symlinked_handoff_without_reading_its_target(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            handoff = self.initialize_project(project)
            victim = project / "victim.md"
            victim.write_text(active_handoff(), encoding="utf-8")
            handoff.unlink()
            os.symlink(victim, handoff)

            with self.assertRaisesRegex(HANDOFF_STATE.HandoffError, "symbolic link"):
                HANDOFF_STATE.read_handoff(project)

            self.assertEqual(active_handoff(), victim.read_text(encoding="utf-8"))

    def test_rejects_symlinked_local_state_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            outside = Path(directory) / "outside"
            project.mkdir()
            outside.mkdir()
            outside_handoff = outside / "HANDOFF.md"
            outside_handoff.write_text(HANDOFF_STATE.render_idle(), encoding="utf-8")
            os.symlink(outside, project / ".usw")

            with self.assertRaisesRegex(HANDOFF_STATE.HandoffError, "symbolic link"):
                HANDOFF_STATE.read_handoff(project)

            self.assertEqual(
                HANDOFF_STATE.render_idle(), outside_handoff.read_text(encoding="utf-8")
            )

    def test_valid_candidate_repairs_invalid_current_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            handoff = self.initialize_project(project)
            handoff.write_text("old or damaged state\n", encoding="utf-8")
            candidate = project / ".usw" / "HANDOFF.next.md"
            candidate.write_text(active_handoff(), encoding="utf-8")

            saved_path, status = HANDOFF_STATE.save_handoff(project, candidate)

            self.assertEqual(handoff.resolve(), saved_path)
            self.assertEqual("paused", status)
            saved_content = handoff.read_text(encoding="utf-8")
            self.assertIn("- Task: Implement local resume flow", saved_content)
            self.assert_generated_snapshot(saved_content)

    def test_physical_drift_does_not_report_false_fresh(self):
        cases = (
            (
                "intent-to-add",
                self.add_intent_to_add,
                {"stale", "unknown"},
            ),
            (
                "stat-preserving tracked edit",
                self.make_stat_preserving_edit,
                {"stale"},
            ),
        )

        for name, mutate, expected_freshness in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                self.initialize_git_project(project)
                saved = HANDOFF_STATE.capture_source_snapshot(project)

                mutate(project)

                current = HANDOFF_STATE.capture_source_snapshot(project)
                report = HANDOFF_STATE.compare_source_snapshots(saved, current)
                self.assertIn(report.freshness, expected_freshness)
                self.assertNotEqual("fresh", report.freshness)

    def test_save_replaces_forged_candidate_snapshot(self):
        forged_digest = f"sha256:{'0' * 64}"
        forged_snapshot = (
            "\n## Source snapshot\n\n"
            "- Schema: `usw-source-v1`\n"
            "- State: complete\n"
            "- Branch: `refs/heads/forged`\n"
            f"- HEAD: `{'0' * 40}`\n"
            f"- Index: `{forged_digest}`\n"
            f"- Tracked filesystem: `{forged_digest}`\n"
            f"- Untracked filesystem: `{forged_digest}`\n"
            f"- Submodules: `{forged_digest}`\n"
            f"- Source: `{forged_digest}`\n"
        )

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize_git_project(project)
            candidate = project / ".usw" / "HANDOFF.next.md"
            candidate.write_text(
                active_handoff() + forged_snapshot,
                encoding="utf-8",
            )

            handoff, status = HANDOFF_STATE.save_handoff(project, candidate)

            saved_content = handoff.read_text(encoding="utf-8")
            self.assertEqual("paused", status)
            self.assert_generated_snapshot(saved_content)
            self.assertNotIn(forged_digest, saved_content)
            self.assertNotIn("refs/heads/forged", saved_content)
            self.assertFalse(candidate.exists())

    def test_reconciles_source_change_matrix(self):
        def no_setup(project: Path) -> None:
            return None

        def stage_add(project: Path) -> None:
            (project / "staged.txt").write_text("staged\n", encoding="utf-8")
            self.run_git(project, "add", "staged.txt")

        def stage_delete(project: Path) -> None:
            self.run_git(project, "rm", "--quiet", "tracked.txt")

        def stage_modify(project: Path) -> None:
            (project / "tracked.txt").write_text("staged change\n", encoding="utf-8")
            self.run_git(project, "add", "tracked.txt")

        def tracked_edit(project: Path) -> None:
            (project / "tracked.txt").write_text("changed\n", encoding="utf-8")

        def add_untracked(project: Path) -> None:
            (project / "untracked.txt").write_text("one\n", encoding="utf-8")

        def set_up_untracked(project: Path) -> None:
            (project / "untracked.txt").write_text("one\n", encoding="utf-8")

        def modify_untracked(project: Path) -> None:
            (project / "untracked.txt").write_text("two\n", encoding="utf-8")

        def delete_untracked(project: Path) -> None:
            (project / "untracked.txt").unlink()

        cases = (
            ("staged addition", no_setup, stage_add, "Index"),
            ("staged modification", no_setup, stage_modify, "Index"),
            ("staged deletion", no_setup, stage_delete, "Index"),
            ("tracked edit", no_setup, tracked_edit, "Tracked filesystem"),
            ("new untracked", no_setup, add_untracked, "Untracked filesystem"),
            (
                "modified untracked",
                set_up_untracked,
                modify_untracked,
                "Untracked filesystem",
            ),
            (
                "deleted untracked",
                set_up_untracked,
                delete_untracked,
                "Untracked filesystem",
            ),
        )
        for name, set_up, mutate, component in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                self.initialize_git_project(project)
                set_up(project)

                report = self.report_after_change(project, mutate)

                self.assertEqual("stale", report.freshness)
                self.assertIn(component, report.changed_components)

    def test_branch_only_change_is_fresh_with_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize_git_project(project)
            saved = self.capture_complete_snapshot(project)
            self.run_git(project, "branch", "checkpoint-other")
            self.run_git(project, "checkout", "--quiet", "checkpoint-other")

            report = HANDOFF_STATE.compare_source_snapshots(
                saved,
                self.capture_complete_snapshot(project),
            )

            self.assertEqual("fresh", report.freshness)
            self.assertTrue(report.branch_changed)

    def test_different_head_is_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize_git_project(project)
            saved = self.capture_complete_snapshot(project)
            (project / "committed.txt").write_text("next\n", encoding="utf-8")
            self.run_git(project, "add", "committed.txt")
            self.run_git(
                project,
                "-c",
                "user.name=USW Tests",
                "-c",
                "user.email=usw-tests@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "next",
            )

            report = HANDOFF_STATE.compare_source_snapshots(
                saved,
                self.capture_complete_snapshot(project),
            )

            self.assertEqual("stale", report.freshness)
            self.assertIn("HEAD", report.changed_components)

    def test_ignored_and_reserved_state_do_not_cause_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize_git_project(project)
            (project / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
            self.run_git(project, "add", ".gitignore")
            self.run_git(
                project,
                "-c",
                "user.name=USW Tests",
                "-c",
                "user.email=usw-tests@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "ignore local output",
            )
            saved = self.capture_complete_snapshot(project)
            (project / "ignored.txt").write_text("ignored\n", encoding="utf-8")
            (project / ".usw" / "HANDOFF.md").write_text(
                "runtime state\n",
                encoding="utf-8",
            )

            report = HANDOFF_STATE.compare_source_snapshots(
                saved,
                self.capture_complete_snapshot(project),
            )

            self.assertEqual("fresh", report.freshness)

    def test_tracked_handoff_is_still_reserved(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize_git_project(project)
            self.run_git(project, "add", "--force", ".usw/HANDOFF.md")
            self.run_git(
                project,
                "-c",
                "user.name=USW Tests",
                "-c",
                "user.email=usw-tests@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "track runtime handoff",
            )
            saved = self.capture_complete_snapshot(project)
            (project / ".usw" / "HANDOFF.md").write_text(
                "changed runtime state\n",
                encoding="utf-8",
            )

            report = HANDOFF_STATE.compare_source_snapshots(
                saved,
                self.capture_complete_snapshot(project),
            )

            self.assertEqual("fresh", report.freshness)

    def test_full_restoration_is_fresh(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize_git_project(project)
            saved = self.capture_complete_snapshot(project)
            tracked = project / "tracked.txt"
            tracked.write_bytes(b"bravo\n")
            self.assertEqual(
                "stale",
                HANDOFF_STATE.compare_source_snapshots(
                    saved,
                    self.capture_complete_snapshot(project),
                ).freshness,
            )
            tracked.write_bytes(b"alpha\n")

            report = HANDOFF_STATE.compare_source_snapshots(
                saved,
                self.capture_complete_snapshot(project),
            )

            self.assertEqual("fresh", report.freshness)

    def test_physical_mode_and_symlink_changes_are_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize_git_project(project)
            tracked = project / "tracked.txt"
            os.chmod(tracked, 0o755)
            self.run_git(project, "add", "tracked.txt")
            self.run_git(
                project,
                "-c",
                "user.name=USW Tests",
                "-c",
                "user.email=usw-tests@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "make executable",
            )
            executable_snapshot = self.capture_complete_snapshot(project)
            os.chmod(tracked, 0o644)
            mode_report = HANDOFF_STATE.compare_source_snapshots(
                executable_snapshot,
                self.capture_complete_snapshot(project),
            )
            self.assertEqual("stale", mode_report.freshness)

            link = project / "tracked-link"
            os.symlink("tracked.txt", link)
            self.run_git(project, "add", "tracked-link")
            self.run_git(
                project,
                "-c",
                "user.name=USW Tests",
                "-c",
                "user.email=usw-tests@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "add symlink",
            )
            symlink_snapshot = self.capture_complete_snapshot(project)
            link.unlink()
            os.symlink("different-target", link)
            link_report = HANDOFF_STATE.compare_source_snapshots(
                symlink_snapshot,
                self.capture_complete_snapshot(project),
            )
            self.assertEqual("stale", link_report.freshness)

    def test_legacy_unknown_future_and_malformed_snapshots(self):
        future_snapshot = (
            "\n## Source snapshot\n\n"
            "- Schema: `usw-source-v999`\n"
            "- State: complete\n"
        )
        malformed_v1 = (
            "\n## Source snapshot\n\n"
            "- Schema: `usw-source-v1`\n"
            "- State: complete\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            handoff = self.initialize_project(project)
            handoff.write_text(active_handoff(), encoding="utf-8")
            content, legacy_report = HANDOFF_STATE.reconcile_handoff(project)
            self.assertEqual(active_handoff(), content)
            self.assertEqual("unknown", legacy_report.freshness)
            self.assertEqual("saved snapshot missing", legacy_report.reason)

            handoff.write_text(active_handoff() + future_snapshot, encoding="utf-8")
            _, future_report = HANDOFF_STATE.reconcile_handoff(project)
            self.assertEqual("unknown", future_report.freshness)
            self.assertEqual("unsupported schema", future_report.reason)

            handoff.write_text(active_handoff() + malformed_v1, encoding="utf-8")
            with self.assertRaisesRegex(HANDOFF_STATE.HandoffError, "Malformed"):
                HANDOFF_STATE.read_handoff(project)

    def test_reconcile_idle_handoff_does_not_capture_source(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            handoff = self.initialize_project(project)

            with mock.patch.object(HANDOFF_STATE, "capture_source_snapshot") as capture:
                content, report = HANDOFF_STATE.reconcile_handoff(project)

            self.assertEqual(handoff.read_text(encoding="utf-8"), content)
            self.assertEqual("unknown", report.freshness)
            self.assertEqual("saved snapshot missing", report.reason)
            capture.assert_not_called()

    def test_duplicate_candidate_snapshot_does_not_replace_current_state(self):
        supplied_snapshot = (
            "\n## Source snapshot\n\n"
            "- Schema: `anything`\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            handoff = self.initialize_project(project)
            original = handoff.read_text(encoding="utf-8")
            candidate = project / ".usw" / "HANDOFF.next.md"
            candidate.write_text(
                active_handoff() + supplied_snapshot + supplied_snapshot,
                encoding="utf-8",
            )

            with self.assertRaisesRegex(HANDOFF_STATE.HandoffError, "Duplicate section"):
                HANDOFF_STATE.save_handoff(project, candidate)

            self.assertEqual(original, handoff.read_text(encoding="utf-8"))
            self.assertTrue(candidate.exists())

    def test_capture_ignores_redirecting_git_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize_git_project(project)
            with mock.patch.dict(
                os.environ,
                {
                    "GIT_DIR": "/definitely/not/the/project/.git",
                    "GIT_WORK_TREE": "/definitely/not/the/project",
                    "GIT_INDEX_FILE": "/definitely/not/the/project/index",
                },
            ):
                snapshot = HANDOFF_STATE.capture_source_snapshot(project)

            self.assertEqual("complete", snapshot.state, snapshot.problem)

    def test_show_is_read_only_and_reports_freshness(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize_git_project(project)
            candidate = project / ".usw" / "HANDOFF.next.md"
            candidate.write_text(active_handoff(), encoding="utf-8")
            HANDOFF_STATE.save_handoff(project, candidate)
            index = project / ".git" / "index"
            before_index = (index.read_bytes(), index.stat().st_mtime_ns)
            before_tracked = (project / "tracked.txt").read_bytes()

            shown = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "show", str(project)],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("freshness: fresh", shown.stderr)
            self.assertEqual(before_index, (index.read_bytes(), index.stat().st_mtime_ns))
            self.assertEqual(before_tracked, (project / "tracked.txt").read_bytes())

    def test_unborn_and_detached_head_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            unborn_project = Path(directory) / "unborn"
            unborn_project.mkdir()
            self.run_git(unborn_project, "init", "--quiet")
            self.initialize_project(unborn_project)
            unborn = self.capture_complete_snapshot(unborn_project)
            self.assertEqual("unborn", unborn.head)

            detached_project = Path(directory) / "detached"
            detached_project.mkdir()
            self.initialize_git_project(detached_project)
            self.run_git(detached_project, "checkout", "--quiet", "--detach", "HEAD")
            detached = self.capture_complete_snapshot(detached_project)
            self.assertIsNone(detached.branch)

    def test_recursive_submodule_change_is_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            source = parent / "source-submodule"
            source.mkdir()
            self.run_git(source, "init", "--quiet")
            (source / "child.txt").write_text("child\n", encoding="utf-8")
            self.run_git(source, "add", "child.txt")
            self.run_git(
                source,
                "-c",
                "user.name=USW Tests",
                "-c",
                "user.email=usw-tests@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "child initial",
            )

            project = parent / "project"
            project.mkdir()
            self.initialize_git_project(project)
            self.run_git(
                project,
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "--quiet",
                "../source-submodule",
                "vendor/child",
            )
            self.run_git(
                project,
                "-c",
                "user.name=USW Tests",
                "-c",
                "user.email=usw-tests@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "add child",
            )
            saved = self.capture_complete_snapshot(project)
            (project / "vendor" / "child" / "child.txt").write_text(
                "changed child\n",
                encoding="utf-8",
            )

            report = HANDOFF_STATE.compare_source_snapshots(
                saved,
                self.capture_complete_snapshot(project),
            )

            self.assertEqual("stale", report.freshness)
            self.assertIn("Submodules", report.changed_components)

    def test_finishes_active_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            handoff = self.initialize_project(project)
            handoff.write_text(active_handoff(), encoding="utf-8")

            finished_path = HANDOFF_STATE.finish_handoff(project)

            self.assertEqual(handoff.resolve(), finished_path)
            self.assertEqual(
                "idle",
                HANDOFF_STATE.validate_handoff(handoff.read_text(encoding="utf-8")),
            )

    def test_requires_usw_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                HANDOFF_STATE.HandoffError, "run /usw-init first"
            ):
                HANDOFF_STATE.read_handoff(Path(directory))

    def test_cli_init_save_show_finish_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            initialized = subprocess.run(
                [sys.executable, str(INIT_SCRIPT_PATH), str(project)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Created:", initialized.stdout)

            initial_state = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "show", str(project)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("- Status: idle", initial_state.stdout)
            self.assertIn("status: idle", initial_state.stderr)

            candidate = project / ".usw" / "HANDOFF.next.md"
            candidate.write_text(active_handoff(), encoding="utf-8")
            saved = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "save",
                    str(project),
                    str(candidate),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("status: paused", saved.stdout)

            shown = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "show", str(project)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("- Task: Implement local resume flow", shown.stdout)
            self.assert_generated_snapshot(shown.stdout)
            self.assertIn("freshness: unknown", shown.stderr)
            self.assertIn("status: paused", shown.stderr)

            finished = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "finish", str(project)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("status: idle", finished.stdout)
            self.assertEqual(
                "idle",
                HANDOFF_STATE.validate_handoff(
                    (project / ".usw" / "HANDOFF.md").read_text(encoding="utf-8")
                ),
            )


if __name__ == "__main__":
    unittest.main()
