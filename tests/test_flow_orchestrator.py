import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "skills/usw-run-flow/scripts/run_flow.py"
SPEC = importlib.util.spec_from_file_location("text_flow_runner", SCRIPT)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


class TextFlowRunnerTests(unittest.TestCase):
    def project(self, directory: str) -> tuple[Path, Path]:
        project = Path(directory)
        shared = project / "usw/flows"
        shared.mkdir(parents=True)
        return project, shared

    def test_exact_bytes_create_identity_and_model_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            content = b"# Flow\r\n\r\nCALL whatever the model can read.\r\n"
            (shared / "review.md").write_bytes(content)

            invocation = RUNNER.prepare_markdown_run(
                project, shared, "review", "inspect this"
            )

            self.assertEqual(content.decode("utf-8"), invocation.flow.markdown)
            self.assertEqual("inspect this", invocation.user_input)
            self.assertEqual(
                "usw-markdown:shared:" + hashlib.sha256(content).hexdigest(),
                invocation.flow.identity,
            )

    def test_root_execution_uses_begin_or_ephemeral_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("review\n", encoding="utf-8")
            invocation = RUNNER.prepare_markdown_run(
                project, shared, "review", "input"
            )
            operation = "usw-operation:" + "1" * 64

            enabled = RUNNER.bind_root_execution(
                invocation,
                handoff_enabled=True,
                operation=operation,
            )
            disabled = RUNNER.bind_root_execution(
                invocation,
                handoff_enabled=False,
            )
            repeated = RUNNER.bind_root_execution(
                invocation,
                handoff_enabled=False,
            )

            self.assertEqual(operation, enabled.context.root_identity)
            self.assertTrue(enabled.context.owns_durable_state)
            self.assertIsNone(enabled.context.branch_label)
            self.assertRegex(
                disabled.context.root_identity,
                r"^usw-ephemeral:[0-9a-f]{32}$",
            )
            self.assertNotEqual(
                disabled.context.root_identity,
                repeated.context.root_identity,
            )
            with self.assertRaisesRegex(
                RUNNER.FlowError, "exact Begin operation"
            ):
                RUNNER.bind_root_execution(
                    invocation,
                    handoff_enabled=True,
                    operation=None,
                )

    def test_nested_run_resolves_safely_and_borrows_verified_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "root.md").write_text("root\n", encoding="utf-8")
            child_bytes = b"child\r\n"
            (shared / "child.md").write_bytes(child_bytes)
            operation = "usw-operation:" + "1" * 64
            root = RUNNER.bind_root_execution(
                RUNNER.prepare_markdown_run(
                    project, shared, "root", "root input"
                ),
                handoff_enabled=True,
                operation=operation,
            )
            verified = []

            child = RUNNER.prepare_nested_run(
                project,
                shared,
                "child",
                "ordinary input with usw-operation:" + "2" * 64,
                parent=root.context,
                branch_label="review branch",
                assert_current=lambda path, identity: verified.append(
                    (path, identity)
                ),
            )

            self.assertEqual(
                child_bytes.decode("utf-8"),
                child.invocation.flow.markdown,
            )
            self.assertEqual(operation, child.context.root_identity)
            self.assertEqual("review branch", child.context.branch_label)
            self.assertFalse(child.context.owns_durable_state)
            self.assertEqual([(project, operation)], verified)
            self.assertIn(
                "usw-operation:" + "2" * 64,
                child.invocation.user_input,
            )
            with self.assertRaisesRegex(
                RUNNER.FlowError, "root-owned context"
            ):
                RUNNER.prepare_nested_run(
                    project,
                    shared,
                    "child",
                    "input",
                    parent=child.context,
                    branch_label="nested again",
                    assert_current=lambda *_: None,
                )

    def test_nested_run_stops_on_stale_parent_and_skips_disabled_check(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "flow.md").write_text("flow\n", encoding="utf-8")
            invocation = RUNNER.prepare_markdown_run(
                project, shared, "flow", "input"
            )
            routed = RUNNER.bind_root_execution(
                invocation,
                handoff_enabled=True,
                operation="usw-operation:" + "1" * 64,
            )

            def stale_parent(*_):
                raise RUNNER.FlowError(
                    "inactive_parent", "parent route is stale"
                )

            with self.assertRaisesRegex(RUNNER.FlowError, "parent route is stale"):
                RUNNER.prepare_nested_run(
                    project,
                    shared,
                    "flow",
                    "child",
                    parent=routed.context,
                    branch_label="child",
                    assert_current=stale_parent,
                )

            ephemeral = RUNNER.bind_root_execution(
                invocation, handoff_enabled=False
            )
            child = RUNNER.prepare_nested_run(
                project,
                shared,
                "flow",
                "child",
                parent=ephemeral.context,
                branch_label="offline child",
            )
            self.assertFalse(child.context.handoff_enabled)
            with self.assertRaisesRegex(
                RUNNER.FlowError, "must not inspect"
            ):
                RUNNER.prepare_nested_run(
                    project,
                    shared,
                    "flow",
                    "child",
                    parent=ephemeral.context,
                    branch_label="wrong child",
                    assert_current=lambda *_: None,
                )

    def test_local_precedes_shared_and_explicit_shared_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            local = project / ".usw/flows"
            local.mkdir(parents=True)
            (local / "review.md").write_text("local\n", encoding="utf-8")
            (shared / "review.md").write_text("shared\n", encoding="utf-8")

            default = RUNNER.resolve_markdown_flow(project, shared, "review")
            selected = RUNNER.resolve_markdown_flow(
                project, shared, "review", origin="shared"
            )

            self.assertEqual(("local", "local\n"), (default.origin, default.markdown))
            self.assertEqual(("shared", "shared\n"), (selected.origin, selected.markdown))
            self.assertNotEqual(default.identity, selected.identity)

    def test_missing_local_falls_back_but_explicit_local_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("shared\n", encoding="utf-8")

            self.assertEqual(
                "shared",
                RUNNER.resolve_markdown_flow(project, shared, "review").origin,
            )
            with self.assertRaisesRegex(RUNNER.FlowError, "missing_flow_root"):
                RUNNER.resolve_markdown_flow(
                    project, shared, "review", origin="local"
                )

    def test_rejects_unsafe_names_root_escape_and_intermediate_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("safe\n", encoding="utf-8")
            outside = project.parent / f"{project.name}-outside"
            outside.mkdir()
            self.addCleanup(outside.rmdir)

            for name in ("../review", "/review", "Review", "review.md"):
                with self.subTest(name=name), self.assertRaisesRegex(
                    RUNNER.FlowError, "invalid_flow_name"
                ):
                    RUNNER.load_markdown_flow(
                        project, shared, name, origin="shared"
                    )
            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_root"):
                RUNNER.load_markdown_flow(
                    project, outside, "review", origin="shared"
                )

            actual = project / "actual"
            actual.mkdir()
            (actual / "review.md").write_text("outside\n", encoding="utf-8")
            linked = project / "linked"
            os.symlink(actual, linked)
            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_root"):
                RUNNER.load_markdown_flow(
                    project, linked, "review", origin="shared"
                )

    def test_rejects_final_symlink_non_file_invalid_utf8_and_empty_input(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            target = project / "target.md"
            target.write_text("target\n", encoding="utf-8")
            os.symlink(target, shared / "linked.md")
            (shared / "directory.md").mkdir()
            (shared / "binary.md").write_bytes(b"\xff")
            (shared / "valid.md").write_text("valid\n", encoding="utf-8")

            for name in ("linked", "directory"):
                with self.subTest(name=name), self.assertRaisesRegex(
                    RUNNER.FlowError, "unsafe_flow_file"
                ):
                    RUNNER.load_markdown_flow(
                        project, shared, name, origin="shared"
                    )
            with self.assertRaisesRegex(RUNNER.FlowError, "invalid_flow_encoding"):
                RUNNER.load_markdown_flow(
                    project, shared, "binary", origin="shared"
                )
            with self.assertRaisesRegex(RUNNER.FlowError, "missing_input"):
                RUNNER.prepare_markdown_run(project, shared, "valid", "  ")

    def test_windows_path_fallback_resolves_markdown_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(os.path.realpath(directory))
            (shared / "review.md").write_text("windows-safe\n", encoding="utf-8")

            with mock.patch.object(RUNNER, "_uses_windows_path_fallback", return_value=True):
                invocation = RUNNER.prepare_markdown_run(
                    project, shared, "review", "input"
                )

            self.assertEqual("windows-safe\n", invocation.flow.markdown)

    def test_legacy_flow_json_is_only_warned_and_never_read(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            local = project / ".usw"
            local.mkdir()
            legacy = local / "FLOW.json"
            legacy.write_bytes(b"\xff legacy bytes")
            before = legacy.read_bytes()
            (shared / "review.md").write_text("review\n", encoding="utf-8")

            invocation = RUNNER.prepare_markdown_run(
                project, shared, "review", "input"
            )

            self.assertEqual(1, len(invocation.warnings))
            self.assertIn("left untouched", invocation.warnings[0])
            self.assertEqual(before, legacy.read_bytes())

    def test_final_read_uses_held_directory_descriptor(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("trusted\n", encoding="utf-8")
            outside = project / "outside"
            outside.mkdir()
            (outside / "review.md").write_text("replaced\n", encoding="utf-8")
            held = shared.with_name("flows-held")
            original_read = RUNNER._read_regular_file

            def replace_path(descriptor, name, path):
                shared.rename(held)
                os.symlink(outside, shared, target_is_directory=True)
                try:
                    return original_read(descriptor, name, path)
                finally:
                    shared.unlink()
                    held.rename(shared)

            with mock.patch.object(
                RUNNER, "_read_regular_file", side_effect=replace_path
            ):
                flow = RUNNER.load_markdown_flow(
                    project, shared, "review", origin="shared"
                )

            self.assertEqual("trusted\n", flow.markdown)

    def test_legacy_warning_does_not_follow_symlinked_local_root(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("review\n", encoding="utf-8")
            outside = project / "outside"
            outside.mkdir()
            (outside / "FLOW.json").write_text("legacy\n", encoding="utf-8")
            os.symlink(outside, project / ".usw", target_is_directory=True)

            invocation = RUNNER.prepare_markdown_run(
                project, shared, "review", "input", origin="shared"
            )

            self.assertEqual((), invocation.warnings)

    def test_cli_returns_markdown_and_migration_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("review body\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "resolve",
                    str(project),
                    str(shared),
                    "review",
                    "user input",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(completed.stdout)
            self.assertEqual("review body\n", report["markdown"])
            self.assertEqual("user input", report["input"])

            for arguments in (
                ["validate", "ignored"],
                ["resolve", "--experimental-structured"],
                ["checkpoint-resume"],
            ):
                with self.subTest(arguments=arguments):
                    retired = subprocess.run(
                        [sys.executable, str(SCRIPT), *arguments],
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(2, retired.returncode)
                    error = json.loads(retired.stderr)
                    self.assertEqual("structured_runtime_removed", error["error"])
                    self.assertIn("$usw-run-flow", error["detail"])

    def test_cli_inspect_returns_exact_markdown_without_execution_input(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            local = project / ".usw/flows"
            local.mkdir(parents=True)
            content = b"# Local flow\r\n\r\nFinish.\r\n"
            (local / "review.md").write_bytes(content)
            (shared / "review.md").write_text("shared\n", encoding="utf-8")
            (project / ".usw/FLOW.json").write_text(
                "legacy\n", encoding="utf-8"
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "inspect",
                    str(project),
                    str(shared),
                    "review",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual("review", report["name"])
            self.assertEqual("local", report["origin"])
            self.assertEqual(
                os.path.realpath(local / "review.md"), report["path"]
            )
            self.assertEqual(content.decode("utf-8"), report["markdown"])
            self.assertEqual(
                "usw-markdown:local:" + hashlib.sha256(content).hexdigest(),
                report["identity"],
            )
            self.assertEqual([], report["warnings"])
            self.assertNotIn("input", report)

    def test_cli_inspect_supports_explicit_shared_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            local = project / ".usw/flows"
            local.mkdir(parents=True)
            (local / "review.md").write_text("local\n", encoding="utf-8")
            (shared / "review.md").write_text("shared\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "inspect",
                    str(project),
                    str(shared),
                    "review",
                    "--origin",
                    "shared",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual("shared", report["origin"])
            self.assertEqual("shared\n", report["markdown"])

    def test_cli_resolve_accepts_origin_before_command(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            local = project / ".usw/flows"
            local.mkdir(parents=True)
            (local / "review.md").write_text("local\n", encoding="utf-8")
            (shared / "review.md").write_text("shared\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--origin",
                    "shared",
                    "resolve",
                    str(project),
                    str(shared),
                    "review",
                    "input",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual("shared", report["origin"])
            self.assertEqual("shared\n", report["markdown"])


if __name__ == "__main__":
    unittest.main()
