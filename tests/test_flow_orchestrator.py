import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import nullcontext, redirect_stderr
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

    def test_packaged_flow_returns_exact_entrypoint_and_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            package.mkdir()
            content = b"# Packaged flow\r\n\r\nUse scripts/check.py.\r\n"
            (package / "FLOW.md").write_bytes(content)

            try:
                invocation = RUNNER.prepare_markdown_run(
                    project, shared, "review", "inspect this"
                )
            except RUNNER.FlowError as error:
                self.fail(f"packaged flow should resolve: {error}")

            self.assertEqual(content.decode("utf-8"), invocation.flow.markdown)
            expected_package = Path(os.path.realpath(package))
            self.assertEqual(expected_package, invocation.flow.flow_directory)
            self.assertEqual(expected_package / "FLOW.md", invocation.flow.path)
            self.assertEqual(
                "usw-markdown:shared:" + hashlib.sha256(content).hexdigest(),
                invocation.flow.identity,
            )

    def test_cli_resolve_packaged_entrypoint_without_reading_sibling(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            scripts = package / "scripts"
            scripts.mkdir(parents=True)
            content = b"Read scripts/check.py.\r\n"
            (package / "FLOW.md").write_bytes(content)
            sibling = scripts / "check.py"
            sibling.write_bytes(b"\xff not UTF-8")
            arguments = ["resolve", str(project), str(shared), "review", "input"]

            for pathname_backend in (False, True):
                with self.subTest(pathname_backend=pathname_backend):
                    reports = []
                    backend = (
                        mock.patch.object(
                            RUNNER.SAFE_ACCESS,
                            "supports_descriptor_relative_access",
                            return_value=False,
                        )
                        if pathname_backend
                        else nullcontext()
                    )
                    with backend, mock.patch.object(
                        RUNNER, "_print_json", side_effect=lambda value: reports.append(value)
                    ):
                        self.assertEqual(0, RUNNER.main(arguments))
                    self.assertEqual(1, len(reports))
                    report = reports[0]
                    self.assertEqual(content.decode("utf-8"), report["markdown"])
                    self.assertEqual(os.path.realpath(package), report["flow_directory"])
                    self.assertEqual(
                        "usw-markdown:shared:" + hashlib.sha256(content).hexdigest(),
                        report["identity"],
                    )
                    self.assertEqual("input", report["input"])
                    self.assertNotIn("content_base64", report)

            sibling.write_text("new content\n", encoding="utf-8", newline="\n")
            self.assertEqual("new content\n", sibling.read_text(encoding="utf-8"))
            self.assertEqual(
                report["identity"],
                RUNNER.resolve_markdown_flow(project, shared, "review").identity,
            )

    def test_user_input_keeps_its_original_path_text(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            package.mkdir()
            (package / "FLOW.md").write_text("Review the input.\n", encoding="utf-8")
            invocation = RUNNER.prepare_markdown_run(
                project, shared, "review", "Use scripts/check.py"
            )
            self.assertEqual("Use scripts/check.py", invocation.user_input)
            self.assertNotIn("scripts/check.py", invocation.flow.markdown)

    def test_root_execution_uses_begin_or_ephemeral_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("review\n", encoding="utf-8", newline="\n")
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
            (shared / "root.md").write_text("root\n", encoding="utf-8", newline="\n")
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

    def test_nested_run_receives_packaged_flow_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "root.md").write_text("root\n", encoding="utf-8", newline="\n")
            package = shared / "child"
            package.mkdir()
            (package / "FLOW.md").write_text("child\n", encoding="utf-8", newline="\n")
            root = RUNNER.bind_root_execution(
                RUNNER.prepare_markdown_run(project, shared, "root", "input"),
                handoff_enabled=False,
            )

            child = RUNNER.prepare_nested_run(
                project,
                shared,
                "child",
                "child input",
                parent=root.context,
                branch_label="packaged child",
            )

            self.assertEqual(
                Path(os.path.realpath(package)),
                child.invocation.flow.flow_directory,
            )
            self.assertEqual(
                Path(os.path.realpath(package / "FLOW.md")),
                child.invocation.flow.path,
            )

    def test_nested_run_stops_on_stale_parent_and_skips_disabled_check(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "flow.md").write_text("flow\n", encoding="utf-8", newline="\n")
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
            (local / "review.md").write_text("local\n", encoding="utf-8", newline="\n")
            (shared / "review.md").write_text("shared\n", encoding="utf-8", newline="\n")

            default = RUNNER.resolve_markdown_flow(project, shared, "review")
            selected = RUNNER.resolve_markdown_flow(
                project, shared, "review", origin="shared"
            )

            self.assertEqual(("local", "local\n"), (default.origin, default.markdown))
            self.assertEqual(("shared", "shared\n"), (selected.origin, selected.markdown))
            self.assertNotEqual(default.identity, selected.identity)

    def test_dual_layout_is_ambiguous_before_origin_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            local = project / ".usw/flows"
            package = local / "review"
            package.mkdir(parents=True)
            (local / "review.md").write_text("flat\n", encoding="utf-8", newline="\n")
            (package / "FLOW.md").write_text("package\n", encoding="utf-8", newline="\n")
            (shared / "review.md").write_text("shared\n", encoding="utf-8", newline="\n")

            with self.assertRaisesRegex(
                RUNNER.FlowError, "ambiguous_flow_layout"
            ):
                RUNNER.resolve_markdown_flow(project, shared, "review")

    def test_local_package_precedes_shared_flat(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            local_package = project / ".usw/flows/review"
            local_package.mkdir(parents=True)
            (local_package / "FLOW.md").write_text("local\n", encoding="utf-8", newline="\n")
            (shared / "review.md").write_text("shared\n", encoding="utf-8", newline="\n")

            flow = RUNNER.resolve_markdown_flow(project, shared, "review")

            self.assertEqual(("local", "local\n"), (flow.origin, flow.markdown))
            self.assertEqual(Path(os.path.realpath(local_package)), flow.flow_directory)

    def test_incomplete_local_package_falls_back_to_shared(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (project / ".usw/flows/review").mkdir(parents=True)
            (shared / "review.md").write_text("shared\n", encoding="utf-8", newline="\n")

            flow = RUNNER.resolve_markdown_flow(project, shared, "review")

            self.assertEqual(("shared", "shared\n"), (flow.origin, flow.markdown))

    def test_rejects_package_directory_and_entrypoint_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            actual = project / "actual-package"
            actual.mkdir()
            (actual / "FLOW.md").write_text("linked package\n", encoding="utf-8", newline="\n")
            os.symlink(actual, shared / "review", target_is_directory=True)

            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_root"):
                RUNNER.load_markdown_flow(
                    project, shared, "review", origin="shared"
                )

        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            package.mkdir()
            target = project / "target.md"
            target.write_text("linked entrypoint\n", encoding="utf-8", newline="\n")
            os.symlink(target, package / "FLOW.md")

            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_file"):
                RUNNER.load_markdown_flow(
                    project, shared, "review", origin="shared"
                )

    def test_missing_local_falls_back_but_explicit_local_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("shared\n", encoding="utf-8", newline="\n")

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
            (shared / "review.md").write_text("safe\n", encoding="utf-8", newline="\n")
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
            (actual / "review.md").write_text("outside\n", encoding="utf-8", newline="\n")
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
            target.write_text("target\n", encoding="utf-8", newline="\n")
            os.symlink(target, shared / "linked.md")
            (shared / "directory.md").mkdir()
            (shared / "binary.md").write_bytes(b"\xff")
            (shared / "valid.md").write_text("valid\n", encoding="utf-8", newline="\n")

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

    def as_pathname_platform(self):
        """Force the backend platforms without dir_fd use, such as Windows."""

        return mock.patch.object(
            RUNNER.SAFE_ACCESS,
            "supports_descriptor_relative_access",
            mock.Mock(return_value=False),
        )

    def test_pathname_backend_resolves_a_flat_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(os.path.realpath(directory))
            (shared / "review.md").write_text("flat\n", encoding="utf-8", newline="\n")

            expected = RUNNER.prepare_markdown_run(project, shared, "review", "input")
            with self.as_pathname_platform():
                invocation = RUNNER.prepare_markdown_run(
                    project, shared, "review", "input"
                )

            self.assertEqual("flat\n", invocation.flow.markdown)
            self.assertEqual(expected.flow.identity, invocation.flow.identity)
            self.assertEqual(expected.flow.path, invocation.flow.path)
            self.assertEqual(expected.flow.flow_directory, invocation.flow.flow_directory)

    def test_pathname_backend_resolves_a_packaged_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(os.path.realpath(directory))
            package = shared / "review"
            package.mkdir()
            (package / "FLOW.md").write_text("packaged\n", encoding="utf-8", newline="\n")

            expected = RUNNER.prepare_markdown_run(project, shared, "review", "input")
            with self.as_pathname_platform():
                invocation = RUNNER.prepare_markdown_run(
                    project, shared, "review", "input"
                )

            self.assertEqual("packaged\n", invocation.flow.markdown)
            self.assertEqual(expected.flow.identity, invocation.flow.identity)
            self.assertEqual(expected.flow.path, invocation.flow.path)
            self.assertEqual(
                Path(os.path.realpath(package)), invocation.flow.flow_directory
            )

    def test_pathname_backend_still_rejects_a_symlinked_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(os.path.realpath(directory))
            outside = project / "outside.md"
            outside.write_text("outside\n", encoding="utf-8", newline="\n")
            os.symlink(outside, shared / "review.md")

            with self.as_pathname_platform():
                with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_file"):
                    RUNNER.prepare_markdown_run(project, shared, "review", "input")

    def test_pathname_backend_still_rejects_ambiguous_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(os.path.realpath(directory))
            (shared / "review.md").write_text("flat\n", encoding="utf-8", newline="\n")
            package = shared / "review"
            package.mkdir()
            (package / "FLOW.md").write_text("packaged\n", encoding="utf-8", newline="\n")

            with self.as_pathname_platform():
                with self.assertRaisesRegex(RUNNER.FlowError, "ambiguous_flow_layout"):
                    RUNNER.prepare_markdown_run(project, shared, "review", "input")

    def test_final_file_open_is_nonblocking_before_regular_file_check(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            path = shared / "review.md"
            path.write_text("safe\n", encoding="utf-8", newline="\n")
            original_open = os.open

            def require_nonblocking(name, flags, *, dir_fd=None):
                if name == "review.md":
                    self.assertTrue(flags & os.O_NONBLOCK)
                return original_open(name, flags, dir_fd=dir_fd)

            with mock.patch.object(RUNNER.os, "open", side_effect=require_nonblocking):
                flow = RUNNER.load_markdown_flow(
                    project, shared, "review", origin="shared"
                )

            self.assertEqual("safe\n", flow.markdown)

    def test_legacy_flow_json_is_only_warned_and_never_read(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            local = project / ".usw"
            local.mkdir()
            legacy = local / "FLOW.json"
            legacy.write_bytes(b"\xff legacy bytes")
            before = legacy.read_bytes()
            (shared / "review.md").write_text("review\n", encoding="utf-8", newline="\n")

            invocation = RUNNER.prepare_markdown_run(
                project, shared, "review", "input"
            )

            self.assertEqual(1, len(invocation.warnings))
            self.assertIn("left untouched", invocation.warnings[0])
            self.assertEqual(before, legacy.read_bytes())

    @unittest.skipUnless(
        RUNNER.SAFE_ACCESS.supports_descriptor_relative_access(),
        "asserts the descriptor-relative guarantee itself: that a component "
        "swapped after it was trusted cannot change what is read. The pathname "
        "backend deliberately does not provide it, which is disclosed rather "
        "than hidden, so the assertion does not apply there.",
    )
    def test_final_read_uses_held_directory_descriptor(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("trusted\n", encoding="utf-8", newline="\n")
            outside = project / "outside"
            outside.mkdir()
            (outside / "review.md").write_text("replaced\n", encoding="utf-8", newline="\n")
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
            (shared / "review.md").write_text("review\n", encoding="utf-8", newline="\n")
            outside = project / "outside"
            outside.mkdir()
            (outside / "FLOW.json").write_text("legacy\n", encoding="utf-8", newline="\n")
            os.symlink(outside, project / ".usw", target_is_directory=True)

            invocation = RUNNER.prepare_markdown_run(
                project, shared, "review", "input", origin="shared"
            )

            self.assertEqual((), invocation.warnings)

    def test_cli_returns_markdown_and_migration_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("review body\n", encoding="utf-8", newline="\n")
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
            self.assertIn("flow_directory", report)
            self.assertEqual(os.path.realpath(shared), report["flow_directory"])

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
            (shared / "review.md").write_text("shared\n", encoding="utf-8", newline="\n")
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
            self.assertIn("flow_directory", report)
            self.assertEqual(os.path.realpath(local), report["flow_directory"])
            self.assertEqual(content.decode("utf-8"), report["markdown"])
            self.assertEqual(
                "usw-markdown:local:" + hashlib.sha256(content).hexdigest(),
                report["identity"],
            )
            self.assertEqual([], report["warnings"])
            self.assertNotIn("input", report)

    def test_cli_inspect_reports_package_directory_without_reading_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            resources = package / "scripts"
            resources.mkdir(parents=True)
            content = b"Read scripts/check.py.\n"
            (package / "FLOW.md").write_bytes(content)
            (resources / "check.py").write_bytes(b"\xff unreadable as UTF-8")

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
            self.assertEqual(content.decode("utf-8"), report["markdown"])
            self.assertEqual(os.path.realpath(package), report["flow_directory"])
            self.assertNotIn("resources", report)

    def test_cli_inspect_supports_explicit_shared_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            local = project / ".usw/flows"
            local.mkdir(parents=True)
            (local / "review.md").write_text("local\n", encoding="utf-8", newline="\n")
            (shared / "review.md").write_text("shared\n", encoding="utf-8", newline="\n")

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
            (local / "review.md").write_text("local\n", encoding="utf-8", newline="\n")
            (shared / "review.md").write_text("shared\n", encoding="utf-8", newline="\n")

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

    def test_cli_rejects_repeated_or_conflicting_origins(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            (shared / "review.md").write_text("review\n", encoding="utf-8", newline="\n")

            for selectors in (
                ("--origin", "shared", "--origin", "shared"),
                ("--origin", "local", "--origin", "shared"),
            ):
                with self.subTest(selectors=selectors):
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(SCRIPT),
                            "inspect",
                            str(project),
                            str(shared),
                            "review",
                            *selectors,
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    self.assertEqual(2, completed.returncode)
                    self.assertEqual(
                        "invalid_flow_origin",
                        json.loads(completed.stderr)["error"],
                    )

    def test_prepare_write_uses_default_and_custom_shared_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)

            prepared = RUNNER.prepare_flow_write(project, "review")

            self.assertEqual("shared", prepared.origin)
            self.assertEqual("package", prepared.layout)
            self.assertFalse(prepared.exists)
            self.assertEqual(
                Path(os.path.realpath(shared / "review/FLOW.md")), prepared.path
            )
            self.assertEqual("", prepared.markdown)

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            custom = project / "automation/flows"
            custom.mkdir(parents=True)
            (project / "usw.yaml").write_text(
                "schema_version: 1\nflows:\n  root: automation/flows\n",
                encoding="utf-8",
                newline="\n",
            )

            prepared = RUNNER.prepare_flow_write(project, "review")

            self.assertEqual(
                Path(os.path.realpath(custom / "review/FLOW.md")), prepared.path
            )

    def test_prepare_write_supports_local_and_preserves_existing_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            local = project / ".usw/flows"
            local.mkdir(parents=True)
            flat = local / "review.md"
            flat.write_text("flat\n", encoding="utf-8", newline="\n")

            prepared = RUNNER.prepare_flow_write(
                project, "review", origin="local"
            )

            self.assertEqual("local", prepared.origin)
            self.assertEqual("flat", prepared.layout)
            self.assertTrue(prepared.exists)
            self.assertEqual(Path(os.path.realpath(flat)), prepared.path)
            self.assertEqual("flat\n", prepared.markdown)

            flat.unlink()
            package = local / "review"
            package.mkdir()
            (package / "FLOW.md").write_text(
                "package\n", encoding="utf-8", newline="\n"
            )

            prepared = RUNNER.prepare_flow_write(
                project, "review", origin="local"
            )

            self.assertEqual("package", prepared.layout)
            self.assertEqual(
                Path(os.path.realpath(package / "FLOW.md")), prepared.path
            )
            self.assertEqual("package\n", prepared.markdown)
            self.assertFalse((shared / "review/FLOW.md").exists())

    def test_prepare_write_rejects_ambiguous_and_unexpected_types(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            package.mkdir()
            (shared / "review.md").write_text(
                "flat\n", encoding="utf-8", newline="\n"
            )
            (package / "FLOW.md").write_text(
                "package\n", encoding="utf-8", newline="\n"
            )

            with self.assertRaisesRegex(
                RUNNER.FlowError, "ambiguous_flow_layout"
            ):
                RUNNER.prepare_flow_write(project, "review")

        for relative, error_code in (
            ("usw/flows/review.md", "unsafe_flow_file"),
            ("usw/flows/review", "unsafe_flow_root"),
        ):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                project, _ = self.project(directory)
                path = project / relative
                if path.suffix:
                    path.mkdir()
                else:
                    path.write_text("not a directory\n", encoding="utf-8")
                with self.assertRaisesRegex(RUNNER.FlowError, error_code):
                    RUNNER.prepare_flow_write(project, "review")

    def test_prepare_write_rejects_symlink_at_each_authoring_position(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            actual = project / "actual-flows"
            actual.mkdir()
            os.symlink(actual, project / "usw", target_is_directory=True)
            with self.assertRaisesRegex(
                RUNNER.FlowError, "symlinked_root|unsafe_flow_root"
            ):
                RUNNER.prepare_flow_write(project, "review")

        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            actual = project / "actual-package"
            actual.mkdir()
            os.symlink(actual, shared / "review", target_is_directory=True)
            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_root"):
                RUNNER.prepare_flow_write(project, "review")

        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            package.mkdir()
            target = project / "target.md"
            target.write_text("linked\n", encoding="utf-8", newline="\n")
            os.symlink(target, package / "FLOW.md")
            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_file"):
                RUNNER.prepare_flow_write(project, "review")

    def test_write_creates_package_and_updates_existing_layouts(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            prepared = RUNNER.prepare_flow_write(project, "review")

            written = RUNNER.write_prepared_flow(
                project, "review", prepared.write_token, "new\n"
            )

            self.assertEqual("new\n", written.markdown)
            self.assertEqual("new\n", (shared / "review/FLOW.md").read_text())
            self.assertFalse((shared / "review.md").exists())

        for layout in ("flat", "package"):
            with self.subTest(layout=layout), tempfile.TemporaryDirectory() as directory:
                project, shared = self.project(directory)
                if layout == "flat":
                    target = shared / "review.md"
                else:
                    package = shared / "review"
                    package.mkdir()
                    target = package / "FLOW.md"
                    sibling = package / "notes.bin"
                    sibling.write_bytes(b"\xff sibling")
                target.write_text("old\n", encoding="utf-8", newline="\n")
                prepared = RUNNER.prepare_flow_write(project, "review")

                written = RUNNER.write_prepared_flow(
                    project, "review", prepared.write_token, "updated\n"
                )

                self.assertEqual(Path(os.path.realpath(target)), written.path)
                self.assertEqual("updated\n", target.read_text())
                if layout == "package":
                    self.assertEqual(b"\xff sibling", sibling.read_bytes())

    def test_write_rejects_stale_content_layout_and_config(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            target = shared / "review.md"
            target.write_text("old\n", encoding="utf-8", newline="\n")
            prepared = RUNNER.prepare_flow_write(project, "review")
            target.write_text("changed\n", encoding="utf-8", newline="\n")

            with self.assertRaisesRegex(RUNNER.FlowError, "stale_flow_target"):
                RUNNER.write_prepared_flow(
                    project, "review", prepared.write_token, "replacement\n"
                )
            self.assertEqual("changed\n", target.read_text())

        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            prepared = RUNNER.prepare_flow_write(project, "review")
            alternate = shared / "review.md"
            alternate.write_text("appeared\n", encoding="utf-8", newline="\n")

            with self.assertRaisesRegex(
                RUNNER.FlowError, "stale_flow_target|ambiguous_flow_layout"
            ):
                RUNNER.write_prepared_flow(
                    project, "review", prepared.write_token, "replacement\n"
                )
            self.assertEqual("appeared\n", alternate.read_text())

        with tempfile.TemporaryDirectory() as directory:
            project, _ = self.project(directory)
            custom = project / "custom/flows"
            custom.mkdir(parents=True)
            prepared = RUNNER.prepare_flow_write(project, "review")
            (project / "usw.yaml").write_text(
                "schema_version: 1\nflows:\n  root: custom/flows\n",
                encoding="utf-8",
                newline="\n",
            )

            with self.assertRaisesRegex(RUNNER.FlowError, "stale_flow_target"):
                RUNNER.write_prepared_flow(
                    project, "review", prepared.write_token, "replacement\n"
                )
            self.assertFalse((custom / "review/FLOW.md").exists())

    def test_cli_prepare_write_and_write_use_json_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            prepared = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "prepare-write",
                    str(project),
                    "review",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, prepared.returncode, prepared.stderr)
            plan = json.loads(prepared.stdout)
            self.assertEqual("shared", plan["origin"])
            self.assertEqual(
                os.path.realpath(shared / "review/FLOW.md"), plan["path"]
            )

            written = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "write",
                    str(project),
                    "review",
                    plan["write_token"],
                ],
                input="written through stdin\n",
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, written.returncode, written.stderr)
            self.assertEqual(
                "written through stdin\n", json.loads(written.stdout)["markdown"]
            )

            stale = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "write",
                    str(project),
                    "review",
                    plan["write_token"],
                ],
                input="must not replace\n",
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(2, stale.returncode)
            self.assertEqual("stale_flow_target", json.loads(stale.stderr)["error"])
            self.assertEqual(
                "written through stdin\n",
                (shared / "review/FLOW.md").read_text(),
            )

    def test_write_rechecks_after_staging_and_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            target = shared / "review.md"
            target.write_text("old\n", encoding="utf-8", newline="\n")
            prepared = RUNNER.prepare_flow_write(project, "review")
            probe = RUNNER.SAFE_ACCESS.open_safe_directory(shared)
            backend = type(probe)
            probe.close()
            original = backend.write_exclusive

            def race(directory_handle, name, content, mode):
                original(directory_handle, name, content, mode)
                if name.startswith(".review.md."):
                    target.write_text("raced\n", encoding="utf-8", newline="\n")

            with mock.patch.object(backend, "write_exclusive", race):
                with self.assertRaisesRegex(
                    RUNNER.FlowError, "stale_flow_target"
                ):
                    RUNNER.write_prepared_flow(
                        project,
                        "review",
                        prepared.write_token,
                        "replacement\n",
                    )

            self.assertEqual("raced\n", target.read_text())
            self.assertEqual([], list(shared.glob(".review.md.*.tmp")))

    def test_write_works_through_pathname_backend(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            with mock.patch.object(
                RUNNER.SAFE_ACCESS,
                "supports_descriptor_relative_access",
                return_value=False,
            ):
                prepared = RUNNER.prepare_flow_write(project, "review")
                written = RUNNER.write_prepared_flow(
                    project, "review", prepared.write_token, "portable\n"
                )

            self.assertEqual("portable\n", written.markdown)
            self.assertEqual(
                "portable\n", (shared / "review/FLOW.md").read_text()
            )

    def test_cli_write_rejects_non_utf8_stdin(self):
        with tempfile.TemporaryDirectory() as directory:
            project, _ = self.project(directory)
            prepared = RUNNER.prepare_flow_write(project, "review")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "write",
                    str(project),
                    "review",
                    prepared.write_token,
                ],
                input=b"\xff",
                capture_output=True,
                check=False,
            )

            self.assertEqual(2, completed.returncode)
            self.assertEqual(
                "invalid_flow_encoding",
                json.loads(completed.stderr.decode("utf-8"))["error"],
            )


class FlowWriteReviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve()
        self.root = self.project / "usw/flows"

    def cli(self, command, *arguments, content=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), command, str(self.project), "review", *arguments],
            input=content, capture_output=True, text=True, check=False,
        )

    def backend(self, pathname):
        native = RUNNER.SAFE_ACCESS.supports_descriptor_relative_access()
        return mock.patch.object(
            RUNNER.SAFE_ACCESS, "supports_descriptor_relative_access",
            return_value=native and not pathname,
        )

    def test_missing_roots_are_prepared_without_writes_then_created(self):
        for origin, relative in (("shared", "usw/flows"),
                                 ("shared", "automation/flows"),
                                 ("local", ".usw/flows")):
            for pathname in (False, True):
                with self.subTest(origin=origin, root=relative, pathname=pathname), tempfile.TemporaryDirectory() as raw:
                    project = Path(raw).resolve()
                    if origin == "local":
                        (project / ".usw").mkdir()
                    if relative == "automation/flows":
                        (project / "usw.yaml").write_text(
                            "schema_version: 1\nflows:\n  root: automation/flows\n",
                            encoding="utf-8",
                        )
                    before = set(project.rglob("*"))
                    native = RUNNER.SAFE_ACCESS.supports_descriptor_relative_access()
                    with mock.patch.object(
                        RUNNER.SAFE_ACCESS, "supports_descriptor_relative_access",
                        return_value=native and not pathname,
                    ):
                        plan = RUNNER.prepare_flow_write(project, "review", origin=origin)
                        self.assertFalse(plan.root_exists)
                        self.assertEqual(before, set(project.rglob("*")))
                        result = RUNNER.write_prepared_flow(
                            project, "review", plan.write_token, "Review notes.\n", origin=origin
                        )
                        self.assertEqual(project / relative / "review/FLOW.md", result.path)
                        flow = RUNNER.resolve_markdown_flow(
                            project, project / relative, "review", origin=origin
                        )
                        self.assertEqual("Review notes.\n", flow.markdown)

    def test_local_requires_existing_workspace_on_prepare_and_write(self):
        with self.assertRaisesRegex(RUNNER.FlowError, "workspace_not_initialized"):
            RUNNER.prepare_flow_write(self.project, "review", origin="local")
        self.assertFalse((self.project / ".usw").exists())
        (self.project / ".usw").mkdir()
        plan = RUNNER.prepare_flow_write(self.project, "review", origin="local")
        (self.project / ".usw").rmdir()
        with self.assertRaisesRegex(RUNNER.FlowError, "workspace_not_initialized"):
            RUNNER.write_prepared_flow(
                self.project, "review", plan.write_token, "Review.\n", origin="local"
            )
        self.assertFalse((self.project / ".usw").exists())

    def test_root_appearance_invalidates_prepared_token(self):
        plan = RUNNER.prepare_flow_write(self.project, "review")
        self.root.mkdir(parents=True)
        current = RUNNER.prepare_flow_write(self.project, "review")
        self.assertNotEqual(plan.write_token, current.write_token)
        with self.assertRaisesRegex(RUNNER.FlowError, "stale_flow_target"):
            RUNNER.write_prepared_flow(self.project, "review", plan.write_token, "Review.\n")
        self.assertEqual([], list(self.root.iterdir()))

    def test_empty_stdin_preserves_existing_flow_and_creates_no_directories(self):
        plan = RUNNER.prepare_flow_write(self.project, "review")
        for content in ("", " \t\n", "\u2003\n"):
            with self.subTest(content=repr(content)):
                result = self.cli("write", plan.write_token, content=content)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertEqual("empty_flow_content", json.loads(result.stderr)["error"])
                self.assertEqual([], list(self.project.iterdir()))
        self.root.mkdir(parents=True)
        target = self.root / "review.md"
        target.write_text("Keep me.\n", encoding="utf-8")
        plan = RUNNER.prepare_flow_write(self.project, "review")
        for content in ("", " \t\n"):
            result = self.cli("write", plan.write_token, content=content)
            self.assertEqual("empty_flow_content", json.loads(result.stderr)["error"])
            self.assertEqual("Keep me.\n", target.read_text(encoding="utf-8"))

    def test_malformed_tokens_return_json_without_writes(self):
        for token in ("", "bad-token", "токен", "usw-write:" + "0" * 64):
            with self.subTest(token=token):
                result = self.cli("write", token, content="Review.\n")
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertEqual("stale_flow_target", json.loads(result.stderr)["error"])
                self.assertEqual([], list(self.project.iterdir()))

    def test_authoring_uses_the_normalized_config_root(self):
        for value, relative in (("x # comment", "x"), (r"usw\flows", "usw/flows")):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as raw:
                project = Path(raw).resolve()
                (project / "usw.yaml").write_text(
                    f"schema_version: 1\nflows:\n  root: {value}\n", encoding="utf-8"
                )
                plan = RUNNER.prepare_flow_write(project, "review")
                self.assertEqual(project / relative / "review/FLOW.md", plan.path)
                RUNNER.write_prepared_flow(project, "review", plan.write_token, "Review.\n")
                resolved = RUNNER.resolve_markdown_flow(
                    project, project / relative, "review", origin="shared"
                )
                self.assertEqual("Review.\n", resolved.markdown)

    def test_staging_failure_cleans_only_new_directories_and_allows_retry(self):
        for pathname in (False, True):
            for root_exists in (False, True):
                with self.subTest(pathname=pathname, root_exists=root_exists), tempfile.TemporaryDirectory() as raw, self.backend(pathname):
                    project = Path(raw).resolve()
                    root = project / "usw/flows"
                    if root_exists:
                        root.mkdir(parents=True)
                    before = set(project.rglob("*"))
                    plan = RUNNER.prepare_flow_write(project, "review")
                    probe = RUNNER.SAFE_ACCESS.open_safe_directory(project)
                    backend = type(probe)
                    probe.close()
                    original = backend.write_exclusive

                    def fail_after_staging(handle, name, content, mode):
                        original(handle, name, content, mode)
                        raise OSError("staging failed")

                    with mock.patch.object(backend, "write_exclusive", fail_after_staging):
                        with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_file"):
                            RUNNER.write_prepared_flow(project, "review", plan.write_token, "New.\n")
                    self.assertEqual(before, set(project.rglob("*")))
                    retry = RUNNER.prepare_flow_write(project, "review")
                    self.assertEqual(plan.write_token, retry.write_token)
                    RUNNER.write_prepared_flow(project, "review", plan.write_token, "Retry.\n")
                    self.assertEqual("Retry.\n", plan.path.read_text(encoding="utf-8"))

    def test_recheck_failure_cleans_package_and_missing_root(self):
        plan = RUNNER.prepare_flow_write(self.project, "review")
        original = RUNNER._assert_write_target
        calls = 0

        def fail_recheck(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise RUNNER.FlowError("stale_flow_target", "changed during staging")
            return original(*args, **kwargs)

        with mock.patch.object(RUNNER, "_assert_write_target", fail_recheck):
            with self.assertRaisesRegex(RUNNER.FlowError, "stale_flow_target"):
                RUNNER.write_prepared_flow(self.project, "review", plan.write_token, "New.\n")
        self.assertEqual([], list(self.project.iterdir()))

    def test_new_directory_open_or_sync_failure_leaves_no_residue(self):
        for stage in ("open", "sync"):
            with self.subTest(stage=stage):
                plan = RUNNER.prepare_flow_write(self.project, "review")
                probe = RUNNER.SAFE_ACCESS.open_safe_directory(self.project)
                backend = type(probe)
                probe.close()
                original = backend.child_directory

                def fail_open(handle, name):
                    if name == "review":
                        raise OSError("cannot open new package")
                    return original(handle, name)

                method = "child_directory" if stage == "open" else "sync"
                replacement = fail_open if stage == "open" else mock.Mock(side_effect=OSError("sync failed"))
                with mock.patch.object(backend, method, replacement):
                    with self.assertRaises(RUNNER.FlowError):
                        RUNNER.write_prepared_flow(self.project, "review", plan.write_token, "New.\n")
                self.assertEqual([], list(self.project.iterdir()))

    def test_cleanup_keeps_new_directories_with_foreign_entries(self):
        plan = RUNNER.prepare_flow_write(self.project, "review")
        probe = RUNNER.SAFE_ACCESS.open_safe_directory(self.project)
        backend = type(probe)
        probe.close()
        original = backend.write_exclusive

        def foreign_entry(handle, name, content, mode):
            original(handle, "foreign.txt", "Keep me.\n", 0o600)
            raise OSError("staging failed")

        with mock.patch.object(backend, "write_exclusive", foreign_entry):
            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_file"):
                RUNNER.write_prepared_flow(self.project, "review", plan.write_token, "New.\n")
        self.assertEqual("Keep me.\n", (plan.path.parent / "foreign.txt").read_text(encoding="utf-8"))
        self.assertFalse(plan.path.exists())

    def test_cleanup_failure_preserves_primary_error_in_cli_json(self):
        for pathname in (False, True):
            for root_exists in (False, True):
                with self.subTest(pathname=pathname, root_exists=root_exists), tempfile.TemporaryDirectory() as raw, self.backend(pathname):
                    project = Path(raw).resolve()
                    if root_exists:
                        (project / "usw/flows").mkdir(parents=True)
                    plan = RUNNER.prepare_flow_write(project, "review")
                    probe = RUNNER.SAFE_ACCESS.open_safe_directory(project)
                    backend = type(probe)
                    probe.close()
                    original = RUNNER._assert_write_target
                    calls = 0

                    def fail_recheck(*args, **kwargs):
                        nonlocal calls
                        calls += 1
                        if calls == 3:
                            raise RUNNER.FlowError("stale_flow_target", "changed during staging")
                        return original(*args, **kwargs)

                    errors = io.StringIO()
                    with mock.patch.object(RUNNER, "_assert_write_target", fail_recheck), mock.patch.object(backend, "remove_directory", side_effect=PermissionError(13, "cleanup denied")), mock.patch.object(sys, "stdin", io.StringIO("New.\n")), redirect_stderr(errors):
                        code = RUNNER.main(["write", str(project), "review", plan.write_token])
                    self.assertEqual(2, code)
                    report = json.loads(errors.getvalue())
                    self.assertEqual("stale_flow_target", report["error"])
                    self.assertIn("changed during staging", report["detail"])
                    self.assertIn("cleanup denied", report["detail"])
                    self.assertNotIn("written", report)
                    self.assertEqual([], list(plan.path.parent.iterdir()))

    def test_errors_after_replace_report_written_true_in_cli_json(self):
        for stage, pathname in ((s, p) for s in ("sync", "readback", "interrupt", "mismatch", "close") for p in (False, True)):
            with self.subTest(stage=stage, pathname=pathname), tempfile.TemporaryDirectory() as raw, self.backend(pathname):
                project = Path(raw).resolve()
                root = project / "usw/flows"
                root.mkdir(parents=True)
                target = root / "review.md"
                target.write_text("Old.\n", encoding="utf-8")
                plan = RUNNER.prepare_flow_write(project, "review")
                probe = RUNNER.SAFE_ACCESS.open_safe_directory(project)
                backend = type(probe)
                probe.close()
                replace, sync, read = backend.replace, backend.sync, backend.read_bytes
                close = backend.close
                replaced = False
                close_failed = False

                def replace_and_mark(handle, source, destination):
                    nonlocal replaced
                    replace(handle, source, destination)
                    replaced = True
                    if stage == "mismatch":
                        target.write_text("Concurrent edit.\n", encoding="utf-8")

                def fail_sync(handle):
                    if replaced and stage == "sync":
                        raise OSError("durability unconfirmed")
                    sync(handle)

                def fail_readback(handle, name):
                    if replaced and stage == "interrupt":
                        raise KeyboardInterrupt("read-back interrupted")
                    if replaced and stage == "readback":
                        raise OSError("read-back failed")
                    return read(handle, name)

                def fail_close(handle):
                    nonlocal close_failed
                    close(handle)
                    if replaced and stage == "close" and not close_failed:
                        close_failed = True
                        raise OSError("directory close failed")

                errors = io.StringIO()
                with mock.patch.object(backend, "replace", replace_and_mark), mock.patch.object(backend, "sync", fail_sync), mock.patch.object(backend, "read_bytes", fail_readback), mock.patch.object(backend, "close", fail_close), mock.patch.object(sys, "stdin", io.StringIO("New.\n")), redirect_stderr(errors):
                    code = RUNNER.main(["write", str(project), "review", plan.write_token])
                self.assertTrue(replaced)
                self.assertEqual(2, code)
                report = json.loads(errors.getvalue())
                self.assertEqual("write_unverified", report["error"])
                self.assertIs(True, report["written"])
                self.assertTrue(target.is_file())

    def test_staging_collision_does_not_delete_existing_file(self):
        self.root.mkdir(parents=True)
        target = self.root / "review.md"
        target.write_text("Old.\n", encoding="utf-8")
        collision = self.root / (".review.md." + "a" * 24 + ".tmp")
        collision.write_text("Not ours.\n", encoding="utf-8")
        plan = RUNNER.prepare_flow_write(self.project, "review")
        with mock.patch.object(RUNNER.secrets, "token_hex", return_value="a" * 24):
            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_file"):
                RUNNER.write_prepared_flow(self.project, "review", plan.write_token, "New.\n")
        self.assertEqual("Not ours.\n", collision.read_text(encoding="utf-8"))
        self.assertEqual("Old.\n", target.read_text(encoding="utf-8"))

    def test_root_and_package_swaps_during_staging_do_not_touch_foreign_files(self):
        for pathname in (False, True):
            for position in ("root", "package"):
                with self.subTest(pathname=pathname, position=position), tempfile.TemporaryDirectory() as raw, self.backend(pathname):
                    project = Path(raw).resolve()
                    root = project / "usw/flows"
                    package = root / "review"
                    package.mkdir(parents=True)
                    (package / "FLOW.md").write_text("Old.\n", encoding="utf-8")
                    outside = project / "outside"
                    foreign_parent = outside / "review" if position == "root" else outside
                    foreign_parent.mkdir(parents=True)
                    foreign = foreign_parent / "FLOW.md"
                    foreign.write_text("Old.\n", encoding="utf-8")
                    temporary = foreign_parent / (".FLOW.md." + "a" * 24 + ".tmp")
                    temporary.write_text("Foreign temporary.\n", encoding="utf-8")
                    swapped = root if position == "root" else package
                    moved = project / "moved"
                    plan = RUNNER.prepare_flow_write(project, "review")
                    probe = RUNNER.SAFE_ACCESS.open_safe_directory(project)
                    backend = type(probe)
                    probe.close()
                    original = backend.write_exclusive

                    def swap(handle, name, content, mode):
                        original(handle, name, content, mode)
                        swapped.rename(moved)
                        os.symlink(outside, swapped, target_is_directory=True)

                    with mock.patch.object(backend, "write_exclusive", swap), mock.patch.object(RUNNER.secrets, "token_hex", return_value="a" * 24):
                        with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_root"):
                            RUNNER.write_prepared_flow(project, "review", plan.write_token, "New.\n")
                    self.assertEqual("Old.\n", foreign.read_text(encoding="utf-8"))
                    self.assertEqual("Foreign temporary.\n", temporary.read_text(encoding="utf-8"))

    @unittest.skipIf(os.name == "nt", "POSIX permissions; Windows branch is covered separately")
    def test_new_modes_respect_umask_and_existing_modes_are_preserved(self):
        for pathname in (False, True):
            for mask in (0o022, 0o077):
                with self.subTest(pathname=pathname, mask=mask), tempfile.TemporaryDirectory() as raw, self.backend(pathname):
                    project = Path(raw).resolve()
                    plan = RUNNER.prepare_flow_write(project, "review")
                    previous_umask = os.umask(mask)
                    try:
                        RUNNER.write_prepared_flow(project, "review", plan.write_token, "New.\n")
                        self.assertEqual(0o644 & ~mask, stat.S_IMODE(plan.path.stat().st_mode))
                        for directory in (project / "usw", project / "usw/flows", plan.path.parent):
                            self.assertEqual(0o755 & ~mask, stat.S_IMODE(directory.stat().st_mode))
                        plan.path.chmod(0o664)
                        updated = RUNNER.prepare_flow_write(project, "review")
                        RUNNER.write_prepared_flow(project, "review", updated.write_token, "Updated.\n")
                        self.assertEqual(0o664, stat.S_IMODE(plan.path.stat().st_mode))
                        flat = project / "usw/flows/flat.md"
                        flat.write_text("Old.\n", encoding="utf-8")
                        flat.chmod(0o640)
                        updated = RUNNER.prepare_flow_write(project, "flat")
                        RUNNER.write_prepared_flow(project, "flat", updated.write_token, "Updated.\n")
                        self.assertEqual(0o640, stat.S_IMODE(flat.stat().st_mode))
                    finally:
                        os.umask(previous_umask)


if __name__ == "__main__":
    unittest.main()
