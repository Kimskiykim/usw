import base64
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

    def test_packaged_resource_resolves_from_flow_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            script = package / "scripts/check.py"
            script.parent.mkdir(parents=True)
            (package / "FLOW.md").write_text(
                "Use scripts/check.py.\n", encoding="utf-8"
            )
            script.write_text("print('ok')\n", encoding="utf-8", newline="\n")
            flow = RUNNER.resolve_markdown_flow(project, shared, "review")

            self.assertTrue(
                hasattr(RUNNER, "resolve_flow_resource"),
                "packaged resources need an executor boundary",
            )
            resource = RUNNER.resolve_flow_resource(flow, "scripts/check.py")

            self.assertEqual(Path(os.path.realpath(script)), resource.path)
            self.assertEqual(b"print('ok')\n", resource.content)
            self.assertEqual(
                "usw-resource:" + hashlib.sha256(resource.content).hexdigest(),
                resource.identity,
            )

    def test_packaged_resource_declaration_accepts_markdown_punctuation(self):
        for markdown in (
            "Use <scripts/check.py>.\n",
            "Use scripts/check.py—then continue.\n",
        ):
            with self.subTest(markdown=markdown), tempfile.TemporaryDirectory() as directory:
                project, shared = self.project(directory)
                package = shared / "review"
                script = package / "scripts/check.py"
                script.parent.mkdir(parents=True)
                (package / "FLOW.md").write_text(markdown, encoding="utf-8", newline="\n")
                script.write_text("print('ok')\n", encoding="utf-8", newline="\n")
                flow = RUNNER.resolve_markdown_flow(project, shared, "review")

                resource = RUNNER.resolve_flow_resource(flow, "scripts/check.py")

                self.assertEqual(Path(os.path.realpath(script)), resource.path)

    def test_packaged_resource_content_survives_post_read_path_swap(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            script = package / "scripts/check.py"
            script.parent.mkdir(parents=True)
            (package / "FLOW.md").write_text(
                "Use scripts/check.py.\n", encoding="utf-8"
            )
            script.write_text("print('trusted')\n", encoding="utf-8", newline="\n")
            outside = project / "outside.py"
            outside.write_text("print('outside')\n", encoding="utf-8", newline="\n")
            flow = RUNNER.resolve_markdown_flow(project, shared, "review")
            expected_path = Path(os.path.realpath(script))

            resource = RUNNER.resolve_flow_resource(flow, "scripts/check.py")
            script.unlink()
            os.symlink(outside, script)

            self.assertEqual(b"print('trusted')\n", resource.content)
            self.assertEqual(expected_path, resource.path)

    def test_packaged_resource_declaration_rejects_longer_path_substring(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            script = package / "scripts/check.py"
            script.parent.mkdir(parents=True)
            (package / "FLOW.md").write_text(
                "Use archive/scripts/check.py.bak.\n", encoding="utf-8"
            )
            script.write_text("print('not declared')\n", encoding="utf-8", newline="\n")
            flow = RUNNER.resolve_markdown_flow(project, shared, "review")

            with self.assertRaisesRegex(
                RUNNER.FlowError, "undeclared_flow_resource"
            ):
                RUNNER.resolve_flow_resource(flow, "scripts/check.py")

    def test_packaged_resource_rejects_absolute_and_escape_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            package.mkdir()
            (package / "FLOW.md").write_text(
                "Use scripts/check.py.\n", encoding="utf-8"
            )
            flow = RUNNER.resolve_markdown_flow(project, shared, "review")

            self.assertTrue(hasattr(RUNNER, "resolve_flow_resource"))
            for path in ("/tmp/check.py", "../check.py", "scripts/../check.py"):
                with self.subTest(path=path), self.assertRaisesRegex(
                    RUNNER.FlowError, "invalid_flow_resource"
                ):
                    RUNNER.resolve_flow_resource(flow, path)

    def test_packaged_resource_rejects_symlink_components(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            package.mkdir()
            (package / "FLOW.md").write_text(
                "Use scripts/check.py.\n", encoding="utf-8"
            )
            actual = project / "actual-scripts"
            actual.mkdir()
            (actual / "check.py").write_text("print('unsafe')\n", encoding="utf-8", newline="\n")
            os.symlink(actual, package / "scripts", target_is_directory=True)
            flow = RUNNER.resolve_markdown_flow(project, shared, "review")

            self.assertTrue(hasattr(RUNNER, "resolve_flow_resource"))
            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_resource"):
                RUNNER.resolve_flow_resource(flow, "scripts/check.py")

    def test_packaged_resource_rejects_final_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            scripts = package / "scripts"
            scripts.mkdir(parents=True)
            (package / "FLOW.md").write_text(
                "Use scripts/check.py.\n", encoding="utf-8"
            )
            target = package / "actual.py"
            target.write_text("print('unsafe')\n", encoding="utf-8", newline="\n")
            os.symlink(target, scripts / "check.py")
            flow = RUNNER.resolve_markdown_flow(project, shared, "review")

            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_resource"):
                RUNNER.resolve_flow_resource(flow, "scripts/check.py")

    def test_packaged_resource_rejects_post_resolution_ancestor_symlink_swap(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            script = package / "scripts/check.py"
            script.parent.mkdir(parents=True)
            (package / "FLOW.md").write_text(
                "Use scripts/check.py.\n", encoding="utf-8"
            )
            script.write_text("print('trusted')\n", encoding="utf-8", newline="\n")
            flow = RUNNER.resolve_markdown_flow(project, shared, "review")

            outside = project / "outside-flows"
            outside_script = outside / "review/scripts/check.py"
            outside_script.parent.mkdir(parents=True)
            outside_script.write_text("print('outside')\n", encoding="utf-8", newline="\n")
            held = shared.with_name("flows-held")
            shared.rename(held)
            os.symlink(outside, shared, target_is_directory=True)
            try:
                with self.assertRaisesRegex(
                    RUNNER.FlowError, "unsafe_flow_resource|unsafe_flow_root"
                ):
                    RUNNER.resolve_flow_resource(flow, "scripts/check.py")
            finally:
                shared.unlink()
                held.rename(shared)

    def test_packaged_resource_rejects_missing_and_non_regular_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            package.mkdir()
            (package / "FLOW.md").write_text(
                "Use scripts/missing.py or scripts/directory.py.\n",
                encoding="utf-8",
            )
            (package / "scripts").mkdir()
            (package / "scripts/directory.py").mkdir()
            flow = RUNNER.resolve_markdown_flow(project, shared, "review")

            self.assertTrue(hasattr(RUNNER, "resolve_flow_resource"))
            with self.assertRaisesRegex(RUNNER.FlowError, "missing_flow_resource"):
                RUNNER.resolve_flow_resource(flow, "scripts/missing.py")
            with self.assertRaisesRegex(RUNNER.FlowError, "unsafe_flow_resource"):
                RUNNER.resolve_flow_resource(flow, "scripts/directory.py")

    def test_user_input_does_not_declare_a_package_resource(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            package.mkdir()
            (package / "FLOW.md").write_text("Review the input.\n", encoding="utf-8", newline="\n")
            (package / "scripts").mkdir()
            (package / "scripts/check.py").write_text(
                "print('not declared')\n", encoding="utf-8"
            )

            invocation = RUNNER.prepare_markdown_run(
                project, shared, "review", "Use scripts/check.py"
            )

            self.assertEqual("Use scripts/check.py", invocation.user_input)
            self.assertNotIn("scripts/check.py", invocation.flow.markdown)
            with self.assertRaisesRegex(
                RUNNER.FlowError, "undeclared_flow_resource"
            ):
                RUNNER.resolve_flow_resource(
                    invocation.flow, "scripts/check.py"
                )

    def test_flat_flow_resource_boundary_does_not_rebase_workspace_path(self):
        flow = RUNNER.load_markdown_flow(
            ROOT,
            ROOT / "usw/flows",
            "chat-review",
            origin="shared",
        )

        self.assertTrue(hasattr(RUNNER, "resolve_flow_resource"))
        with self.assertRaisesRegex(RUNNER.FlowError, "flat_flow_resource"):
            RUNNER.resolve_flow_resource(
                flow, "commands/usw-reviewer-llm-critic.md"
            )
        self.assertTrue((ROOT / "commands/usw-reviewer-llm-critic.md").is_file())

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

    def test_pathname_backend_reads_a_packaged_resource(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(os.path.realpath(directory))
            package = shared / "review"
            script = package / "scripts/check.py"
            script.parent.mkdir(parents=True)
            (package / "FLOW.md").write_text("Use scripts/check.py.\n", encoding="utf-8", newline="\n")
            script.write_text("print('ok')\n", encoding="utf-8", newline="\n")

            invocation = RUNNER.prepare_markdown_run(project, shared, "review", "input")
            expected = RUNNER.resolve_flow_resource(invocation.flow, "scripts/check.py")
            with self.as_pathname_platform():
                resource = RUNNER.resolve_flow_resource(
                    invocation.flow, "scripts/check.py"
                )

            self.assertEqual(b"print('ok')\n", resource.content)
            self.assertEqual(expected.identity, resource.identity)
            self.assertEqual(expected.path, resource.path)

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

    def test_cli_resource_binds_original_identity_and_entrypoint(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            script = package / "scripts/check.py"
            script.parent.mkdir(parents=True)
            (package / "FLOW.md").write_text(
                "Use scripts/check.py.\n", encoding="utf-8"
            )
            script.write_text("print('ok')\n", encoding="utf-8", newline="\n")
            flow = RUNNER.resolve_markdown_flow(project, shared, "review")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "resource",
                    str(project),
                    str(shared),
                    "review",
                    flow.identity,
                    str(flow.path),
                    "scripts/check.py",
                    "--origin",
                    "shared",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(os.path.realpath(script), report["resource_path"])
            self.assertEqual(flow.identity, report["identity"])
            self.assertEqual(str(flow.path), report["path"])
            self.assertEqual(
                b"print('ok')\n",
                base64.b64decode(report["content_base64"], validate=True),
            )
            self.assertEqual(
                "usw-resource:"
                + hashlib.sha256(b"print('ok')\n").hexdigest(),
                report["resource_identity"],
            )

            stale = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "resource",
                    str(project),
                    str(shared),
                    "review",
                    flow.identity,
                    str(package / "OTHER.md"),
                    "scripts/check.py",
                    "--origin",
                    "shared",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(2, stale.returncode)
            self.assertEqual("stale_flow_resource", json.loads(stale.stderr)["error"])

            stale_identity = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "resource",
                    str(project),
                    str(shared),
                    "review",
                    "usw-markdown:shared:" + "0" * 64,
                    str(flow.path),
                    "scripts/check.py",
                    "--origin",
                    "shared",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(2, stale_identity.returncode)
            self.assertEqual(
                "stale_flow_resource",
                json.loads(stale_identity.stderr)["error"],
            )

    def test_cli_resource_requires_exact_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            project, shared = self.project(directory)
            package = shared / "review"
            script = package / "scripts/check.py"
            script.parent.mkdir(parents=True)
            (package / "FLOW.md").write_text(
                "Use scripts/check.py.\n", encoding="utf-8"
            )
            script.write_text("print('ok')\n", encoding="utf-8", newline="\n")
            flow = RUNNER.resolve_markdown_flow(
                project, shared, "review", origin="shared"
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "resource",
                    str(project),
                    str(shared),
                    "review",
                    flow.identity,
                    str(flow.path),
                    "scripts/check.py",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(2, completed.returncode)
            self.assertEqual(
                "missing_flow_origin", json.loads(completed.stderr)["error"]
            )

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


if __name__ == "__main__":
    unittest.main()
