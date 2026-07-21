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
    def test_v1_defaults_include_provider_neutral_review_root(self):
        config = INIT_USW.default_config()

        self.assertEqual(1, config.schema_version)
        self.assertEqual("standalone", config.provider)
        self.assertEqual("usw", config.artifact_root)
        self.assertIsNone(config.legacy_refinement_root)
        self.assertEqual("usw/flows", config.flow_root)
        self.assertEqual("usw/reviews", config.review_root)
        self.assertEqual(
            "schema_version: 1\n"
            "artifacts:\n"
            "  provider: standalone\n"
            "  root: usw\n"
            "flows:\n"
            "  root: usw/flows\n"
            "reviews:\n"
            "  root: usw/reviews\n",
            INIT_USW.render_default_config(),
        )

    def test_parse_config_preserves_unknown_fields_and_provider_defaults(self):
        content = (
            "schema_version: 1\n"
            "artifacts:\n"
            "  provider: openspec\n"
            "future:\n"
            "  behavior: retained\n"
        )

        config = INIT_USW.parse_config(content)

        self.assertEqual("openspec", config.provider)
        self.assertEqual("openspec", config.artifact_root)
        self.assertIsNone(config.legacy_refinement_root)
        self.assertEqual("usw/flows", config.flow_root)
        self.assertEqual("usw/reviews", config.review_root)
        self.assertEqual(content, config.raw_content)

    def test_legacy_refinement_root_is_reported_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            legacy = project / "shared/refinements/example/session.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("legacy bytes\n", encoding="utf-8")
            before = legacy.read_bytes()
            (project / "usw.yaml").write_text(
                "schema_version: 1\nartifacts:\n  provider: standalone\n"
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

            self.assertEqual("shared/refinements", config.legacy_refinement_root)
            self.assertIn("Legacy refinement.root detected", completed.stdout)
            self.assertIn("explicit migration decision", completed.stdout)
            self.assertEqual(before, legacy.read_bytes())
            self.assertFalse((project / ".usw/refinements").exists())

    def test_rejects_unsupported_schema_and_provider_with_stable_codes(self):
        with self.assertRaises(INIT_USW.ConfigError) as schema_error:
            INIT_USW.parse_config("schema_version: 2\n")
        self.assertEqual("unsupported_schema_version", schema_error.exception.code)

        with self.assertRaises(INIT_USW.ConfigError) as provider_error:
            INIT_USW.parse_config(
                "schema_version: 1\nartifacts:\n  provider: external\n"
            )
        self.assertEqual("unsupported_provider", provider_error.exception.code)

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

    def test_openspec_defaults_require_explicit_provider(self):
        standalone = INIT_USW.parse_config("schema_version: 1\n")
        openspec = INIT_USW.parse_config(
            "schema_version: 1\nartifacts:\n  provider: openspec\n"
        )

        self.assertEqual("usw", standalone.artifact_root)
        self.assertEqual("openspec", openspec.artifact_root)
        with tempfile.TemporaryDirectory() as directory:
            INIT_USW.validate_config(Path(directory), openspec)

    def test_load_config_does_not_rewrite_existing_content(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            config_path = project / "usw.yaml"
            content = (
                "# keep this comment\n"
                "schema_version: 1\n"
                "future:\n  value: untouched\n"
            )
            config_path.write_text(content, encoding="utf-8")

            config = INIT_USW.load_config(project)

            self.assertEqual(content, config.raw_content)
            self.assertEqual(content, config_path.read_text(encoding="utf-8"))

    def test_creates_standalone_workspace_and_local_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)

            results = INIT_USW.initialize_usw(project)
            (
                (config_file, config_created),
                (artifact_directory, artifact_created),
                (changes_directory, changes_created),
                (artifact_template_directory, artifact_template_directory_created),
                *artifact_template_results,
                (flow_directory, flow_created),
                (review_directory, review_created),
                (analysis_scenario, analysis_created),
                (development_scenario, development_created),
                (testing_scenario, testing_created),
                (local_ignore_file, local_ignore_created),
                (handoff_file, handoff_created),
            ) = results

            self.assertTrue(config_created)
            self.assertEqual(project.resolve() / "usw.yaml", config_file)
            self.assertEqual(INIT_USW.render_default_config(), config_file.read_text())
            self.assertTrue(artifact_created)
            self.assertEqual(project.resolve() / "usw", artifact_directory)
            self.assertTrue(changes_created)
            self.assertEqual(artifact_directory / "changes", changes_directory)
            self.assertTrue(artifact_template_directory_created)
            self.assertEqual(artifact_directory / "templates", artifact_template_directory)
            self.assertEqual(
                set(INIT_USW.ARTIFACT_TEMPLATE_PATHS),
                {
                    path.relative_to(artifact_template_directory).as_posix()
                    for path, created in artifact_template_results
                    if created
                },
            )
            for path, created in artifact_template_results:
                self.assertTrue(created)
                relative = path.relative_to(artifact_template_directory).as_posix()
                self.assertEqual(
                    INIT_USW.read_template(relative),
                    path.read_text(encoding="utf-8"),
                )
            self.assertFalse((project / "usw/refinements").exists())
            self.assertFalse((project / ".usw/refinements").exists())
            self.assertTrue(flow_created)
            self.assertEqual(project.resolve() / "usw/flows", flow_directory)
            self.assertTrue(review_created)
            self.assertEqual(project.resolve() / "usw/reviews", review_directory)
            for scenario, created in (
                (analysis_scenario, analysis_created),
                (development_scenario, development_created),
                (testing_scenario, testing_created),
            ):
                self.assertTrue(created)
                self.assertEqual(flow_directory, scenario.parent)
                self.assertTrue(scenario.read_text(encoding="utf-8").startswith("# Flow scenario:"))

            self.assertTrue(local_ignore_created)
            self.assertEqual(project.resolve() / ".usw" / ".gitignore", local_ignore_file)
            self.assertEqual("*\n", local_ignore_file.read_text(encoding="utf-8"))
            self.assertTrue(handoff_created)
            self.assertEqual(project.resolve() / ".usw" / "HANDOFF.md", handoff_file)
            handoff_content = handoff_file.read_text(encoding="utf-8")
            self.assertIn("# Developer Handoff\n", handoff_content)
            self.assertIn("| Subject | Role | Attempt | Current operation | Status | Updated |", handoff_content)
            self.assertIn("## Session journal\n", handoff_content)
            self.assertIn("## Trusted source snapshot\n", handoff_content)

            self.assertFalse((project / "openspec").exists())
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
            self.assertEqual(project.resolve() / "usw.yaml", results[0][0])
            self.assertEqual(project.resolve() / ".usw" / "HANDOFF.md", results[-1][0])

    def test_detects_existing_openspec_workspace_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            openspec = project / "openspec"
            specs = openspec / "specs"
            specs.mkdir(parents=True)
            agents_file = openspec / "AGENTS.md"
            agents_file.write_text("existing OpenSpec instructions\n", encoding="utf-8")
            before = {
                path.relative_to(project): path.read_bytes()
                for path in openspec.rglob("*")
                if path.is_file()
            }

            results = INIT_USW.initialize_usw(project)

            self.assertTrue(INIT_USW.detect_openspec_workspace(project))
            self.assertTrue(all(created for _, created in results))
            after = {
                path.relative_to(project): path.read_bytes()
                for path in openspec.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)
            self.assertFalse((openspec / "changes").exists())

            completed = subprocess.run(
                ["python3", str(SCRIPT_PATH), str(project)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("left unchanged", completed.stdout)
            self.assertIn("artifacts.provider: openspec", completed.stdout)

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

    def test_reinitialization_preserves_and_restores_artifact_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            INIT_USW.initialize_usw(project)
            proposal = project / "usw/templates/change/proposal.md"
            task = project / "usw/templates/task/task.md"
            proposal.write_text("project-owned template\n", encoding="utf-8")
            task.unlink()

            results = INIT_USW.initialize_usw(project)

            self.assertEqual(
                "project-owned template\n", proposal.read_text(encoding="utf-8")
            )
            self.assertEqual(
                INIT_USW.read_template("task/task.md"),
                task.read_text(encoding="utf-8"),
            )
            created = {path for path, was_created in results if was_created}
            self.assertEqual({task.resolve()}, created)

    def test_openspec_provider_does_not_receive_usw_artifact_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "openspec").mkdir()
            (project / "usw.yaml").write_text(
                "schema_version: 1\nartifacts:\n  provider: openspec\n",
                encoding="utf-8",
            )

            INIT_USW.initialize_usw(project)

            self.assertFalse((project / "openspec/templates").exists())
            self.assertFalse((project / "usw/templates").exists())

    def test_rejects_symlinked_artifact_template_root_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            outside = Path(directory) / "outside"
            project.mkdir()
            outside.mkdir()
            (project / "usw").mkdir()
            os.symlink(outside, project / "usw/templates")

            with self.assertRaisesRegex(OSError, "symbolic links"):
                INIT_USW.initialize_usw(project)

            self.assertEqual([], list(outside.iterdir()))
            self.assertFalse((project / "usw.yaml").exists())

    def test_reinitialization_adds_only_missing_standard_scenario(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            INIT_USW.initialize_usw(project)
            flow_root = project / "usw/flows"
            analysis = flow_root / "flow-scenario-analysis.md"
            development = flow_root / "flow-scenario-development.md"
            testing = flow_root / "flow-scenario-testing.md"
            analysis.write_text("custom analysis\n", encoding="utf-8")
            development.unlink()
            testing_before = testing.read_bytes()

            results = INIT_USW.initialize_usw(project)

            self.assertEqual("custom analysis\n", analysis.read_text(encoding="utf-8"))
            self.assertTrue(development.is_file())
            self.assertEqual(testing_before, testing.read_bytes())
            created = {path.name for path, was_created in results if was_created}
            self.assertEqual({"flow-scenario-development.md"}, created)

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

    def test_does_not_follow_symlinked_openspec_hint(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            outside = Path(directory) / "outside"
            project.mkdir()
            outside.mkdir()
            os.symlink(outside, project / "openspec")

            INIT_USW.initialize_usw(project)

            self.assertFalse((outside / "specs").exists())
            self.assertFalse((outside / "changes").exists())
            self.assertTrue((project / "usw").is_dir())

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

    def test_renders_initial_handoff_with_supplied_timestamp(self):
        updated_at = datetime(2026, 7, 17, 9, 30, tzinfo=timezone.utc)

        content = INIT_USW.render_handoff(updated_at)

        self.assertIn(
            "| none | none | none | none | idle | 2026-07-17T09:30:00+00:00 |",
            content,
        )
        self.assertEqual(1, content.count("## Next action"))
        self.assertIn("- Freshness: unknown\n", content)

    def test_preserves_non_workspace_openspec_path(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "openspec").write_text("not a directory", encoding="utf-8")

            INIT_USW.initialize_usw(project)

            self.assertEqual("not a directory", (project / "openspec").read_text())
            self.assertTrue((project / "usw").is_dir())


if __name__ == "__main__":
    unittest.main()
