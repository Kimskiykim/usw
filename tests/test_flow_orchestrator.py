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


if __name__ == "__main__":
    unittest.main()
