import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FLOWS = load("atomic_flows", "skills/usw-initialize-project/scripts/flow_scenario.py")
REGISTRY = load("atomic_registry", "skills/usw-run-flow/scripts/capability_registry.py")
PROVIDERS = load("atomic_providers", "skills/usw-manage-artifacts/scripts/provider_artifacts.py")
DEVELOPMENT = load("atomic_development", "skills/usw-execute-task/scripts/execute_scope.py")
TESTING = load("atomic_testing", "skills/usw-verify-task/scripts/verify_scope.py")


class AtomicSkillContractTests(unittest.TestCase):
    def test_all_scenario_actions_resolve_to_packaged_production_capabilities(self):
        templates = ROOT / "skills/usw-initialize-project/templates/flows"
        actions = set()
        for path in templates.glob("flow-scenario-*.md"):
            actions.update(FLOWS.validate_scenario(path.read_text(encoding="utf-8")).actions)

        self.assertEqual(actions, set(REGISTRY.ACTION_CAPABILITIES))
        for action, skill_name in REGISTRY.ACTION_CAPABILITIES.items():
            with self.subTest(action=action):
                self.assertTrue((ROOT / "skills" / skill_name / "SKILL.md").is_file())
                self.assertNotIn("stub", skill_name)

    def test_atomic_skills_declare_input_write_output_and_return_boundaries(self):
        skills = (
            "usw-initialize-project", "usw-manage-handoff",
            "usw-brainstorm-solutions", "usw-refine-task",
            "usw-plan-small-steps", "usw-explain-me", "usw-create-flow",
            "usw-run-flow",
            "usw-manage-artifacts", "usw-execute-task", "usw-verify-task",
        )
        for skill_name in skills:
            with self.subTest(skill=skill_name):
                content = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8").lower()
                self.assertTrue("return point" in content or "return control" in content)
                self.assertNotIn("call_next_skill", content)

    def test_decomposition_does_not_execute_or_create_plan_handoff(self):
        content = (ROOT / "skills/usw-plan-small-steps/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("не запускает микротаску", content)
        self.assertIn("task-level `plan.md`/`handoff.md`", content)

    def test_standalone_adapter_writes_only_authorized_planning_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            outcome = PROVIDERS.write_planning_artifact(
                project,
                provider="standalone",
                artifact_root="usw",
                role="proposal",
                relative_path="changes/example/proposal.md",
                content="proposal\n",
                permitted_roles=frozenset({"proposal"}),
            )
            self.assertEqual("completed", outcome.status)
            self.assertEqual(frozenset({"proposal"}), outcome.written_roles)
            self.assertEqual("proposal\n", (project / "usw/changes/example/proposal.md").read_text())

    def test_unconnected_openspec_adapter_returns_error_without_fallback_write(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            outcome = PROVIDERS.write_planning_artifact(
                project,
                provider="openspec",
                artifact_root="openspec",
                role="proposal",
                relative_path="changes/example/proposal.md",
                content="proposal\n",
                permitted_roles=frozenset({"proposal"}),
            )
            self.assertEqual("unsupported_provider_operation", outcome.outcome)
            self.assertFalse((project / "openspec").exists())
            self.assertFalse((project / "usw/changes/example/proposal.md").exists())

    def test_development_and_testing_append_only_their_own_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            task = project / "usw/changes/example/tasks/1-test"
            task.mkdir(parents=True)
            (task / "task.md").write_text("task\n", encoding="utf-8")
            development_file = task / "development-evidence.md"
            testing_file = task / "testing-evidence.md"
            dev = DEVELOPMENT.append_development_evidence(
                project,
                task,
                evidence_id="dev-1",
                contract_revision="c1",
                source_identity="usw-source-v1:" + "a" * 64,
                command="unit-test",
                result="passed",
                timestamp="2026-07-21T12:00:00Z",
            )
            test = TESTING.append_testing_evidence(
                project,
                task,
                evidence_id="test-1",
                contract_revision="c1",
                source_identity="usw-source-v1:" + "a" * 64,
                command="acceptance-test",
                result="failed",
                finding="F-1",
                timestamp="2026-07-21T12:01:00Z",
            )
            self.assertEqual(frozenset({"development-evidence"}), dev.written_roles)
            self.assertEqual(frozenset({"testing-evidence"}), test.written_roles)
            self.assertIn("dev-1", development_file.read_text())
            self.assertNotIn("test-1", development_file.read_text())
            self.assertIn("test-1", testing_file.read_text())
            self.assertNotIn("dev-1", testing_file.read_text())

            wrong_role = DEVELOPMENT.append_development_evidence(
                project,
                testing_file,
                evidence_id="dev-2",
                contract_revision="c1",
                source_identity="usw-source-v1:" + "a" * 64,
                command="unit-test",
                result="passed",
                timestamp="2026-07-21T12:02:00Z",
            )
            self.assertEqual("invalid_evidence_path", wrong_role.outcome)

    def test_evidence_writer_rejects_task_root_outside_project(self):
        with tempfile.TemporaryDirectory() as project_dir, tempfile.TemporaryDirectory() as other_dir:
            project = Path(project_dir)
            task = Path(other_dir)
            (task / "task.md").write_text("task\n", encoding="utf-8")
            outcome = DEVELOPMENT.append_development_evidence(
                project,
                task,
                evidence_id="dev-1",
                contract_revision="c1",
                source_identity="usw-source-v1:" + "a" * 64,
                command="unit-test",
                result="passed",
                timestamp="2026-07-21T12:00:00Z",
            )
            self.assertEqual("invalid_evidence_path", outcome.outcome)

    def test_standalone_adapter_rejects_symlinked_managed_path(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            actual = project / "usw/actual"
            actual.mkdir(parents=True)
            (project / "usw/link").symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                PROVIDERS.write_planning_artifact(
                    project,
                    provider="standalone",
                    artifact_root="usw",
                    role="proposal",
                    relative_path="link/proposal.md",
                    content="proposal\n",
                    permitted_roles=frozenset({"proposal"}),
                )


if __name__ == "__main__":
    unittest.main()
