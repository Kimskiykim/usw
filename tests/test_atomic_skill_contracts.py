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


ARTIFACTS = load(
    "atomic_artifacts",
    "research/structured-runtime/legacy/usw-manage-artifacts/scripts/artifact_writer.py",
)


class AtomicSkillContractTests(unittest.TestCase):
    def test_production_skills_do_not_import_research_runtime(self):
        for path in (ROOT / "skills").rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                self.assertNotIn(
                    "research/structured-runtime",
                    path.read_text(encoding="utf-8"),
                    path,
                )

    def test_atomic_skills_declare_input_write_output_and_return_boundaries(self):
        skills = (
            "usw-initialize-project", "usw-manage-handoff",
            "usw-create-flow",
            "usw-run-flow", "usw-find-flow",
        )
        for skill_name in skills:
            with self.subTest(skill=skill_name):
                content = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8").lower()
                self.assertTrue("return point" in content or "return control" in content)
                self.assertNotIn("call_next_skill", content)

    def test_handoff_skills_share_the_routed_operation_contract(self):
        manage = (ROOT / "skills/usw-manage-handoff/SKILL.md").read_text(
            encoding="utf-8"
        )
        run = (ROOT / "skills/usw-run-flow/SKILL.md").read_text(
            encoding="utf-8"
        )
        initialize = (
            ROOT / "skills/usw-initialize-project/SKILL.md"
        ).read_text(encoding="utf-8")
        fallback = (
            ROOT
            / "skills/usw-initialize-project/references/llm-fallback.md"
        ).read_text(encoding="utf-8")

        for content in (manage, run, initialize, fallback):
            self.assertIn(".usw/handoffs/", content)
        self.assertIn("assert-current", manage)
        self.assertIn("несколько routes без selector", manage)
        self.assertIn("independent top-level invocations", run)
        self.assertIn("Nested child не владеет durable state", run)
        self.assertIn("deterministic empty operation router", initialize)
        self.assertIn("deterministic empty router", fallback)
        self.assertNotIn("{{updated_at}}", fallback)

    def test_run_flow_keeps_packaged_resources_inside_resolved_context(self):
        run = (ROOT / "skills/usw-run-flow/SKILL.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "`flow_directory`",
            "`scripts/run_flow.py resource`",
            "`flow_identity` и exact `path`",
            "`resource_identity` и immutable `content_base64`",
            "не перечитывать `resource_path`",
            "только из `flow_markdown`",
            "не из `user_input`",
            "Flat flow сохраняет project/workspace-relative",
            "обычные tool и permission boundaries",
        ):
            self.assertIn(fragment, run)

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
