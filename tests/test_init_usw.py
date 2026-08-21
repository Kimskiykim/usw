import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


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
    def test_v1_defaults_include_project_owned_roots(self):
        config = INIT_USW.default_config()

        self.assertEqual(1, config.schema_version)
        self.assertEqual("usw", config.artifact_root)
        self.assertEqual("usw/flows", config.flow_root)
        self.assertEqual("usw/reviews", config.review_root)
        self.assertTrue(config.handoff)
        self.assertEqual(
            "schema_version: 1\n"
            "handoff: true\n"
            "artifacts:\n"
            "  root: usw\n"
            "flows:\n"
            "  root: usw/flows\n"
            "reviews:\n"
            "  root: usw/reviews\n",
            INIT_USW.render_default_config(),
        )

    def test_parse_config_preserves_unknown_fields_and_defaults(self):
        content = (
            "schema_version: 1\n"
            "future:\n"
            "  behavior: retained\n"
        )

        config = INIT_USW.parse_config(content)

        self.assertEqual("usw", config.artifact_root)
        self.assertEqual("usw/flows", config.flow_root)
        self.assertEqual("usw/reviews", config.review_root)
        self.assertTrue(config.handoff)
        self.assertEqual(content, config.raw_content)

    def test_handoff_accepts_only_boolean_and_defaults_true(self):
        self.assertTrue(INIT_USW.parse_config("schema_version: 1\n").handoff)
        self.assertFalse(
            INIT_USW.parse_config("schema_version: 1\nhandoff: false\n").handoff
        )
        for value in ('"false"', "'true'", "1", "yes", ""):
            content = f"schema_version: 1\nhandoff: {value}\n"
            with self.subTest(value=value), self.assertRaisesRegex(
                INIT_USW.ConfigError, "handoff must be a boolean"
            ):
                INIT_USW.parse_config(content)

    def test_legacy_refinement_root_is_ignored_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            legacy = project / "shared/refinements/example/session.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("legacy bytes\n", encoding="utf-8", newline="\n")
            before = legacy.read_bytes()
            (project / "usw.yaml").write_text(
                "schema_version: 1\n"
                "refinement:\n  root: shared/refinements\n",
                encoding="utf-8",
            )

            config = INIT_USW.load_config(project)
            completed = subprocess.run(
                ["python3", str(SCRIPT_PATH), str(project)],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertFalse(hasattr(config, "legacy_refinement_root"))
            self.assertNotIn("refinement.root", completed.stdout)
            self.assertEqual(before, legacy.read_bytes())
            self.assertFalse((project / ".usw/refinements").exists())

    def test_rejects_unsupported_schema_and_removed_provider(self):
        with self.assertRaises(INIT_USW.ConfigError) as schema_error:
            INIT_USW.parse_config("schema_version: 2\n")
        self.assertEqual("unsupported_schema_version", schema_error.exception.code)

        with self.assertRaises(INIT_USW.ConfigError) as provider_error:
            INIT_USW.parse_config(
                "schema_version: 1\nartifacts:\n  provider: legacy\n"
            )
        self.assertEqual("invalid_config", provider_error.exception.code)

    def test_validation_accepts_standalone_namespace_containment(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)

            validated = INIT_USW.validate_config(project, INIT_USW.default_config())

            self.assertEqual("usw/reviews", validated.review_root)
            self.assertEqual([], list(project.iterdir()))

    def test_validation_rejects_unsafe_and_conflicting_roots_without_writes(self):
        invalid_contents = (
            "schema_version: 1\nartifacts:\n  root: /tmp/outside\n",
            "schema_version: 1\nartifacts:\n  root: ../outside\n",
            (
                "schema_version: 1\n"
                "reviews:\n  root: usw/flows\n"
            ),
            "schema_version: 1\nartifacts:\n  root: .git/generated\n",
            "schema_version: 1\nreviews:\n  root: .usw/reviews\n",
        )
        for content in invalid_contents:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                config = INIT_USW.parse_config(content)

                with self.assertRaises(INIT_USW.ConfigError):
                    INIT_USW.validate_config(project, config)

                self.assertEqual([], list(project.iterdir()))

    def test_validation_rejects_symlinked_managed_root_without_following_it(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            outside = Path(directory) / "outside"
            project.mkdir()
            outside.mkdir()
            os.symlink(outside, project / "usw")

            with self.assertRaisesRegex(INIT_USW.ConfigError, "symbolic link"):
                INIT_USW.validate_config(project, INIT_USW.default_config())

            self.assertEqual([], list(outside.iterdir()))

    def test_load_config_does_not_rewrite_existing_content(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            config_path = project / "usw.yaml"
            content = (
                "# keep this comment\n"
                "schema_version: 1\n"
                "future:\n  value: untouched\n"
            )
            config_path.write_text(content, encoding="utf-8", newline="\n")

            config = INIT_USW.load_config(project)

            self.assertEqual(content, config.raw_content)
            self.assertEqual(content, config_path.read_text(encoding="utf-8"))

    def test_partial_new_file_is_removed_and_retry_creates_complete_content(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            destination = project / "generated.md"
            real_fdopen = INIT_USW.os.fdopen

            class PartialWriter:
                def __init__(self, descriptor, *args, **kwargs):
                    self.handle = real_fdopen(descriptor, *args, **kwargs)

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    self.handle.close()

                def write(self, content):
                    self.handle.write(content[:4])
                    self.handle.flush()
                    raise OSError("simulated write failure")

            with (
                mock.patch.object(INIT_USW.os, "fdopen", side_effect=PartialWriter),
                self.assertRaisesRegex(OSError, "simulated write failure"),
            ):
                INIT_USW.create_file(project, destination, "complete content\n")

            self.assertFalse(destination.exists())
            self.assertTrue(
                INIT_USW.create_file(project, destination, "complete content\n")
            )
            self.assertEqual(
                "complete content\n", destination.read_text(encoding="utf-8")
            )

    def test_creates_standalone_workspace_and_local_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)

            results = INIT_USW.initialize_usw(project)
            expected_files = {
                ".usw/.gitignore",
                ".usw/HANDOFF.md",
                "usw.yaml",
                "usw/flows/examples/chat-review.md",
                "usw/flows/examples/dev-test.md",
                "usw/flows/examples/plan-small-steps.md",
                "usw/flows/examples/refine-intent.md",
            }
            actual_files = {
                path.relative_to(project).as_posix()
                for path in project.rglob("*")
                if path.is_file()
            }

            self.assertTrue(all(created for _, created in results))
            self.assertEqual(expected_files, actual_files)
            self.assertEqual(
                INIT_USW.render_default_config(),
                (project / "usw.yaml").read_text(encoding="utf-8"),
            )
            for name in (
                "chat-review.md",
                "dev-test.md",
                "plan-small-steps.md",
                "refine-intent.md",
            ):
                example = project / "usw/flows/examples" / name
                self.assertEqual(
                    INIT_USW.read_template(f"flows/examples/{name}"),
                    example.read_text(encoding="utf-8"),
                )
            self.assertFalse((project / "usw/refinements").exists())
            self.assertFalse((project / ".usw/refinements").exists())
            self.assertFalse((project / "usw/changes").exists())
            self.assertFalse((project / "usw/reviews").exists())
            self.assertFalse((project / "usw/templates").exists())
            self.assertEqual(
                "*\n", (project / ".usw/.gitignore").read_text(encoding="utf-8")
            )
            handoff_content = (project / ".usw/HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn("# Developer Handoff Router\n", handoff_content)
            self.assertIn("## Operations\n", handoff_content)
            self.assertIn("| No registered operations |", handoff_content)
            self.assertNotIn("- Status:", handoff_content)
            self.assertNotIn("| Subject | Role |", handoff_content)
            self.assertFalse((project / ".usw/handoffs").exists())

            self.assertFalse((project / "hello_world.py").exists())

    def test_uses_exact_project_root_inside_parent_git_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            (parent / ".git").mkdir()
            project = parent / "src" / "feature"
            project.mkdir(parents=True)

            results = INIT_USW.initialize_usw(project)

            for path, _ in results:
                self.assertTrue(path.is_relative_to(project.resolve()))
            self.assertEqual(project.resolve() / "usw.yaml", results[0][0])
            self.assertFalse((parent / "usw.yaml").exists())

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

    def test_reinitialization_restores_example_and_preserves_legacy_scenarios(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            INIT_USW.initialize_usw(project)
            flow_root = project / "usw/flows"
            examples = flow_root / "examples"
            chat_review = examples / "chat-review.md"
            dev_test = examples / "dev-test.md"
            chat_review.write_text("custom chat review\n", encoding="utf-8", newline="\n")
            dev_test.unlink()
            legacy = flow_root / "flow-scenario-analysis.md"
            legacy.write_text("legacy project scenario\n", encoding="utf-8", newline="\n")
            legacy_before = legacy.read_bytes()

            results = INIT_USW.initialize_usw(project)

            self.assertEqual(
                "custom chat review\n", chat_review.read_text(encoding="utf-8")
            )
            self.assertTrue(dev_test.is_file())
            self.assertEqual(legacy_before, legacy.read_bytes())
            created = {
                path.relative_to(project.resolve()).as_posix()
                for path, was_created in results
                if was_created
            }
            self.assertEqual({"usw/flows/examples/dev-test.md"}, created)

    def test_does_not_overwrite_existing_local_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            local_ignore_file = project / ".usw" / ".gitignore"
            local_ignore_file.parent.mkdir()
            local_ignore_file.write_text("existing ignore\n", encoding="utf-8", newline="\n")
            handoff_file = project / ".usw" / "HANDOFF.md"
            handoff_file.write_text("existing handoff\n", encoding="utf-8", newline="\n")

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
    def test_preserves_existing_ignore_without_enforcing_git_policy(self):
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
            (local_state / ".gitignore").write_text("*.tmp\n", encoding="utf-8", newline="\n")

            INIT_USW.initialize_usw(project)

            self.assertEqual(
                "*.tmp\n",
                (local_state / ".gitignore").read_text(encoding="utf-8"),
            )
            self.assertTrue((local_state / "HANDOFF.md").exists())

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
            (local_state / ".gitignore").write_text("*\n", encoding="utf-8", newline="\n")

            INIT_USW.initialize_usw(project)

            self.assertTrue((local_state / "HANDOFF.md").is_file())

    def test_preserves_tracked_local_handoff_without_enforcing_git_policy(self):
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
            (local_state / ".gitignore").write_text("*\n", encoding="utf-8", newline="\n")
            handoff = local_state / "HANDOFF.md"
            handoff.write_text("existing handoff\n", encoding="utf-8", newline="\n")
            subprocess.run(
                ["git", "add", "--force", ".usw/HANDOFF.md"],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )

            INIT_USW.initialize_usw(project)

            self.assertEqual("existing handoff\n", handoff.read_text(encoding="utf-8"))

    def test_cli_failure_reports_partial_workspace_retry_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            stderr = io.StringIO()
            with (
                mock.patch.object(
                    INIT_USW,
                    "parse_args",
                    return_value=SimpleNamespace(project=project),
                ),
                mock.patch.object(
                    INIT_USW,
                    "initialize_usw",
                    side_effect=OSError("disk full"),
                ),
                redirect_stderr(stderr),
            ):
                return_code = INIT_USW.main()

            self.assertEqual(1, return_code)
            self.assertIn("may be partially initialized", stderr.getvalue())
            self.assertIn("rerun /usw-init", stderr.getvalue())
            self.assertIn("existing files will be preserved", stderr.getvalue())

    def test_local_state_is_ignored_but_standalone_config_is_visible_to_git(self):
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
            self.assertIn("usw.yaml", result.stdout)
            ignored = subprocess.run(
                [
                    "git", "check-ignore", "--quiet", "--no-index", "--",
                    ".usw/refinements/.privacy-check",
                ],
                cwd=project,
                check=False,
            )
            self.assertEqual(0, ignored.returncode)

    def test_renders_deterministic_empty_handoff_router(self):
        content = INIT_USW.render_handoff()

        self.assertEqual(
            "# Developer Handoff Router\n\n"
            "## Operations\n\n"
            "| Task | Flow | Status | Operation | Updated |\n"
            "|---|---|---|---|---|\n"
            "| No registered operations | — | — | — | — |\n\n"
            "## Cleanup\n\n"
            "Completed and failed operations remain visible until explicit cleanup.\n\n"
            "Remove all terminal operations: `/usw-handoff cleanup`\n\n"
            "Remove one operation: `/usw-handoff finish <operation-id>`\n",
            content,
        )

    def test_handoff_false_skips_existing_or_missing_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "usw.yaml").write_text(
                "schema_version: 1\nhandoff: false\n", encoding="utf-8"
            )

            results = INIT_USW.initialize_usw(project)

            self.assertFalse((project / ".usw/HANDOFF.md").exists())
            self.assertNotIn(
                ".usw/HANDOFF.md",
                {
                    path.relative_to(project.resolve()).as_posix()
                    for path, _ in results
                },
            )

            existing = project / ".usw/HANDOFF.md"
            existing.write_bytes(b"\xff user bytes")
            before = existing.read_bytes()
            INIT_USW.initialize_usw(project)
            self.assertEqual(before, existing.read_bytes())

    def test_enabling_handoff_creates_missing_generic_idle_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            config = project / "usw.yaml"
            config.write_text(
                "schema_version: 1\nhandoff: false\n", encoding="utf-8"
            )
            INIT_USW.initialize_usw(project)
            handoff = project / ".usw/HANDOFF.md"
            self.assertFalse(handoff.exists())

            config.write_text(
                "schema_version: 1\nhandoff: true\n", encoding="utf-8"
            )
            INIT_USW.initialize_usw(project)
            self.assertEqual(
                INIT_USW.render_handoff(),
                handoff.read_text(encoding="utf-8"),
            )
            self.assertFalse((project / ".usw/handoffs").exists())

if __name__ == "__main__":
    unittest.main()
