import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class TextFlowContractTests(unittest.TestCase):
    def test_removed_machine_runtime_is_not_in_production_skills(self):
        self.assertFalse(
            (ROOT / "skills/usw-run-flow/scripts/capability_registry.py").exists()
        )
        self.assertFalse(
            (ROOT / "skills/usw-initialize-project/scripts/flow_scenario.py").exists()
        )
        self.assertFalse(
            (ROOT / "skills/usw-run-flow/references/version-2.md").exists()
        )

    def test_create_flow_has_one_structured_authoring_reference(self):
        reference_root = ROOT / "skills/usw-create-flow/references"
        self.assertEqual(
            {"version-2.md"},
            {path.name for path in reference_root.glob("*.md")},
        )
        content = (reference_root / "version-2.md").read_text(encoding="utf-8")
        for marker in ("version-2", "CALL", "GATE", "LOOP", "PARALLEL"):
            self.assertIn(marker, content)
        for removed in (
            "run_flow.py",
            "checkpoint-save",
            "action-specific input",
        ):
            self.assertNotIn(removed, content)

    def test_run_and_create_contracts_use_one_text_path(self):
        run = (ROOT / "skills/usw-run-flow/SKILL.md").read_text(encoding="utf-8")
        create = (ROOT / "skills/usw-create-flow/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("один immutable logical invocation", run)
        self.assertIn("Использовать только возвращённый `markdown`", run)
        self.assertIn("не machine DSL", run)
        self.assertIn("больше не поддерживается", run)
        self.assertIn("человекочитаемый `version-2`", create)
        self.assertIn("Не добавлять `--experimental-structured`", create)

    def test_examples_are_non_normative_text_flows(self):
        examples = ROOT / "skills/usw-initialize-project/templates/flows/examples"
        self.assertEqual(
            {"chat-review.md", "dev-test.md"},
            {path.name for path in examples.glob("*.md")},
        )
        for path in examples.glob("*.md"):
            content = path.read_text(encoding="utf-8")
            self.assertIn("Ненормативный пример", content)
            self.assertNotIn("--experimental-structured", content)

    def test_active_project_flows_use_text_first_contracts(self):
        chat = (ROOT / "usw/flows/chat-review.md").read_text(encoding="utf-8")
        development = (ROOT / "usw/flows/dev-test.md").read_text(encoding="utf-8")

        for content in (chat, development):
            self.assertNotIn("--experimental-structured", content)
            self.assertNotIn("## Полномочия записи", content)
            self.assertNotIn("Пишет:", content)
        self.assertIn("не создают parser", chat)
        self.assertIn("Версия: `version-2`", development)
        self.assertIn("Flow не предоставляет полномочия", development)


if __name__ == "__main__":
    unittest.main()
