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
ARTIFACTS = load("atomic_artifacts", "skills/usw-manage-artifacts/scripts/artifact_writer.py")


class AtomicSkillContractTests(unittest.TestCase):
    def test_all_role_scenario_actions_resolve_to_production_capabilities(self):
        templates = ROOT / "tests/fixtures/flow-scenarios"
        actions = set()
        for path in templates.glob("flow-scenario-*.md"):
            actions.update(FLOWS.validate_scenario(path.read_text(encoding="utf-8")).actions)

        self.assertEqual(actions, set(REGISTRY.ACTION_CAPABILITIES))
        for action, skill_name in REGISTRY.ACTION_CAPABILITIES.items():
            with self.subTest(action=action):
                self.assertTrue((ROOT / "skills" / skill_name / "SKILL.md").is_file())
                self.assertNotIn("stub", skill_name)

        self.assertEqual(
            "usw-refine-intent", REGISTRY.ACTION_CAPABILITIES["clarify-intent"]
        )
        self.assertEqual(
            "usw-run-flow",
            REGISTRY.ACTION_CAPABILITIES["select-approach"],
        )
        self.assertNotEqual(
            REGISTRY.ACTION_CAPABILITIES["clarify-intent"],
            REGISTRY.ACTION_CAPABILITIES["select-approach"],
        )

    def test_atomic_skills_declare_input_write_output_and_return_boundaries(self):
        skills = (
            "usw-initialize-project", "usw-manage-handoff",
            "usw-refine-intent",
            "usw-plan-small-steps", "usw-explain-me", "usw-create-flow",
            "usw-run-flow",
            "usw-manage-artifacts",
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

    def test_writer_writes_only_authorized_planning_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            outcome = ARTIFACTS.write_planning_artifact(
                project,
                artifact_root="usw",
                role="proposal",
                relative_path="changes/example/proposal.md",
                content="proposal\n",
                permitted_roles=frozenset({"proposal"}),
            )
            self.assertEqual("completed", outcome.status)
            self.assertEqual(frozenset({"proposal"}), outcome.written_roles)
            self.assertEqual("proposal\n", (project / "usw/changes/example/proposal.md").read_text())

    def test_writer_rejects_symlinked_managed_path(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            actual = project / "usw/actual"
            actual.mkdir(parents=True)
            (project / "usw/link").symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                ARTIFACTS.write_planning_artifact(
                    project,
                    artifact_root="usw",
                    role="proposal",
                    relative_path="link/proposal.md",
                    content="proposal\n",
                    permitted_roles=frozenset({"proposal"}),
                )


if __name__ == "__main__":
    unittest.main()
