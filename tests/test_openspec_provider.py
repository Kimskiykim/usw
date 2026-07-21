import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "skills/usw-manage-artifacts/scripts/provider_artifacts.py"
SPEC = importlib.util.spec_from_file_location("openspec_provider", SCRIPT)
PROVIDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = PROVIDER
SPEC.loader.exec_module(PROVIDER)

INIT_SCRIPT = ROOT / "skills/usw-initialize-project/scripts/init_usw.py"
INIT_SPEC = importlib.util.spec_from_file_location("openspec_provider_init", INIT_SCRIPT)
INIT = importlib.util.module_from_spec(INIT_SPEC)
assert INIT_SPEC.loader is not None
sys.modules[INIT_SPEC.name] = INIT
INIT_SPEC.loader.exec_module(INIT)


@unittest.skipUnless(
    os.environ.get("OPENSPEC_COMPAT_MODE") in {"pinned", "latest"},
    "real OpenSpec provider tests run only in the compatibility environment",
)
class OpenSpecProviderTests(unittest.TestCase):
    def run_cli(self, project: Path, *args: str):
        return subprocess.run(
            ["openspec", *args], cwd=project, check=True, capture_output=True, text=True
        )

    def workspace(self, directory: str) -> Path:
        project = Path(directory)
        self.run_cli(project, "init", "--tools", "none", str(project))
        self.run_cli(project, "new", "change", "example")
        return project

    def write(self, project: Path, role: str, path: str, content: str):
        return PROVIDER.write_planning_artifact(
            project,
            provider="openspec",
            artifact_root="openspec",
            role=role,
            relative_path=path,
            content=content,
            permitted_roles=frozenset({role}),
            change="example",
        )

    def test_role_frontier_follows_native_status_graph(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.workspace(directory)
            proposal = self.write(
                project,
                "proposal",
                "proposal.md",
                "## Why\n\nTest.\n\n## What Changes\n\n- Add example.\n\n"
                "## Capabilities\n\n### New Capabilities\n\n- `example`: Test.\n\n"
                "### Modified Capabilities\n\nNone.\n\n## Impact\n\nTests.\n",
            )
            self.assertEqual("completed", proposal.status)
            spec = self.write(
                project,
                "capability-specs",
                "specs/example/spec.md",
                "## ADDED Requirements\n\n### Requirement: Example\n"
                "The system SHALL work.\n\n#### Scenario: Works\n"
                "- **WHEN** invoked\n- **THEN** it works\n",
            )
            self.assertEqual("completed", spec.status)

            analysis = PROVIDER.openspec_frontier(
                PROVIDER.discover_openspec(project, "example"), "Analysis"
            )
            self.assertEqual("analysis-frontier-ready", analysis.outcome)

            development = PROVIDER.openspec_frontier(
                PROVIDER.discover_openspec(project, "example"), "Development"
            )
            self.assertEqual("create-design", development.outcome)
            design = self.write(project, "technical-design", "design.md", "## Context\n\nTest.\n")
            self.assertEqual("completed", design.status)
            next_development = PROVIDER.openspec_frontier(
                PROVIDER.discover_openspec(project, "example"), "Development"
            )
            self.assertEqual("create-tasks", next_development.outcome)
            tasks = self.write(project, "task-index", "tasks.md", "## 1. Work\n\n- [ ] 1.1 Test\n")
            self.assertEqual("completed", tasks.status)

    def test_config_selection_detection_and_dispatch_use_openspec_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.workspace(directory)
            (project / "usw.yaml").write_text(
                "schema_version: 1\nartifacts:\n  provider: openspec\n",
                encoding="utf-8",
            )
            self.assertTrue(INIT.detect_openspec_workspace(project))
            config = INIT.load_config(project)
            self.assertEqual("openspec", config.provider)
            self.assertEqual("openspec", config.artifact_root)

            outcome = PROVIDER.write_planning_artifact(
                project,
                provider=config.provider,
                artifact_root=config.artifact_root,
                role="proposal",
                relative_path="proposal.md",
                content=(
                    "## Why\n\nTest.\n\n## What Changes\n\n- Add example.\n\n"
                    "## Capabilities\n\n### New Capabilities\n\n- `example`: Test.\n\n"
                    "### Modified Capabilities\n\nNone.\n\n## Impact\n\nTests.\n"
                ),
                permitted_roles=frozenset({"proposal"}),
                change="example",
            )
            self.assertEqual("completed", outcome.status)
            self.assertTrue((project / "openspec/changes/example/proposal.md").is_file())
            self.assertFalse((project / "usw/changes/example/proposal.md").exists())

    def test_missing_required_optional_and_unsupported_operations_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.workspace(directory)
            discovery = PROVIDER.discover_openspec(project, "example")
            required = PROVIDER.resolve_openspec_artifact(discovery, "proposal", required=True)
            optional = PROVIDER.resolve_openspec_artifact(discovery, "design", required=False)
            unsupported = self.write(project, "task-contract", "tasks/1/task.md", "x")
            self.assertEqual("missing_required_artifact", required.outcome)
            self.assertEqual("missing_optional_artifact", optional.outcome)
            self.assertEqual("unsupported_provider_operation", unsupported.outcome)
            self.assertFalse((project / "usw/changes/example").exists())

    def test_review_receipt_stays_outside_openspec_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.workspace(directory)
            proposal = project / "openspec/changes/example/proposal.md"
            proposal.write_text("proposal\n", encoding="utf-8")
            before = {
                path.relative_to(project): path.read_bytes()
                for path in (project / "openspec").rglob("*") if path.is_file()
            }
            result = PROVIDER.write_review_receipt(
                project,
                project / "usw/reviews",
                receipt_id="review-1",
                gate="internal",
                owner_role="Analysis",
                subject="change/example",
                reviewed_scope="proposal",
                reviewer="human",
                verdict="accepted",
                artifacts=[proposal],
            )
            after = {
                path.relative_to(project): path.read_bytes()
                for path in (project / "openspec").rglob("*") if path.is_file()
            }
            self.assertEqual(before, after)
            self.assertEqual(frozenset({"review-receipt"}), result.written_roles)
            self.assertTrue((project / "usw/reviews/change/example/review-1.md").is_file())

    def test_standalone_operation_does_not_resolve_openspec_executable(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            PROVIDER.shutil, "which", side_effect=AssertionError("must not run")
        ):
            project = Path(directory)
            result = PROVIDER.write_planning_artifact(
                project,
                provider="standalone",
                artifact_root="usw",
                role="proposal",
                relative_path="changes/example/proposal.md",
                content="proposal\n",
                permitted_roles=frozenset({"proposal"}),
            )
            self.assertEqual("completed", result.status)


if __name__ == "__main__":
    unittest.main()
