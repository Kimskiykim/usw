import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class PackageLayoutTests(unittest.TestCase):
    def test_initialize_skill_packages_standalone_execution_templates(self):
        templates = ROOT / "skills" / "usw-initialize-project" / "templates"
        expected_fragments = {
            "openspec/AGENTS.md": "completion checkboxes only in `tasks.md`",
            "change/proposal.md": "## Why",
            "change/design.md": "## Decisions",
            "change/spec.md": "## ADDED Requirements",
            "change/tasks.md": "tasks/1.1-{{task_slug}}/task.md",
            "task/task.md": "## Milestone log",
            "task/development-evidence.md": "Writer authority: Development only.",
            "task/testing-evidence.md": "Writer authority: Testing only.",
            "review/receipt.md": "## Reviewed artifact identities",
            "local/HANDOFF.md": "## Trusted source snapshot",
            "usw.yaml": "root: usw/reviews",
        }

        for relative_path, fragment in expected_fragments.items():
            with self.subTest(template=relative_path):
                content = (templates / relative_path).read_text(encoding="utf-8")
                self.assertIn(fragment, content)

    def test_brainstorm_skill_has_required_structure_and_implicit_invocation(self):
        skill_dir = ROOT / "skills" / "usw-brainstorm-solutions"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_dir / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        required_fragments = (
            "## Короткий формат — основной для MVP",
            "## Полный формат — для сложных задач",
            "### Контекст и ограничения",
            "### Проблема",
            "### Причина",
            "### Пути решения",
            "### 1. Рекомендуемый подход",
            "### Рекомендация",
            "### Первый шаг",
        )
        for fragment in required_fragments:
            self.assertIn(fragment, skill)
        self.assertIn("allow_implicit_invocation: true", metadata)

    def test_plan_small_steps_skill_has_microtask_workflow_and_implicit_invocation(self):
        skill_dir = ROOT / "skills" / "usw-plan-small-steps"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_dir / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        required_fragments = (
            "## Правила декомпозиции",
            "## Граница выполнения",
            "## Формат ответа",
            "## Проверка качества плана",
            "## Микротаски",
            "## Первый шаг",
            "не запускает микротаску и не вызывает",
        )
        for fragment in required_fragments:
            self.assertIn(fragment, skill)
        self.assertIn("allow_implicit_invocation: true", metadata)

    def test_refine_task_skill_persists_one_decision_case_per_turn(self):
        skill_dir = ROOT / "skills" / "usw-refine-task"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_dir / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        required_fragments = (
            "## Артефакты",
            "## Один ход диалога",
            "ровно один decision case",
            "decisions.md",
            "outcome.md",
            "## Инварианты",
        )
        for fragment in required_fragments:
            self.assertIn(fragment, skill)
        for artifact in ("session.md", "decisions.md", "outcome.md"):
            self.assertTrue((skill_dir / "assets" / artifact).is_file())
        self.assertIn("$usw-refine-task", metadata)
        self.assertIn("allow_implicit_invocation: true", metadata)

    def test_explain_me_has_levelled_workflow_and_implicit_invocation(self):
        skill_dir = ROOT / "skills" / "usw-explain-me"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_dir / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        required_fragments = (
            "## Выбор уровня",
            "Уровень 0 — «хлебушек»",
            "Уровень 1 — простой",
            "Уровень 2 — технический",
            "Уровень 3 — экспертный",
            "## Особые входные данные",
        )
        for fragment in required_fragments:
            self.assertIn(fragment, skill)
        self.assertIn("allow_implicit_invocation: true", metadata)

    def test_create_flow_skill_uses_validated_linear_contract(self):
        skill_dir = ROOT / "skills" / "usw-create-flow"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_dir / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "## Подготовка",
            "## Сборка контракта",
            "## Запись и проверка",
            "## Граница выполнения",
            "../usw-run-flow/scripts/run_flow.py",
            "$usw-run-flow <name>",
        ):
            self.assertIn(fragment, skill)
        self.assertIn("$usw-create-flow", metadata)
        self.assertIn("allow_implicit_invocation: true", metadata)

    def test_public_commands_delegate_to_internal_skills(self):
        expectations = {
            "usw-init.md": "usw-initialize-project",
            "usw-handoff.md": "usw-manage-handoff",
            "usw-resume.md": "usw-manage-handoff",
        }

        for command_name, skill_name in expectations.items():
            with self.subTest(command=command_name):
                command = (ROOT / "commands" / command_name).read_text(
                    encoding="utf-8"
                )
                self.assertIn(skill_name, command)

    def test_qwen_extension_points_to_shared_skills(self):
        manifest = json.loads((ROOT / "qwen-extension.json").read_text(encoding="utf-8"))

        skills_dir = ROOT / manifest["skills"]
        commands_dir = ROOT / manifest["commands"]

        self.assertEqual("usw", manifest["name"])
        self.assertTrue(
            (skills_dir / "usw-initialize-project" / "SKILL.md").is_file()
        )
        self.assertTrue((skills_dir / "usw-manage-handoff" / "SKILL.md").is_file())
        self.assertTrue(
            (skills_dir / "usw-brainstorm-solutions" / "SKILL.md").is_file()
        )
        self.assertTrue((skills_dir / "usw-plan-small-steps" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-refine-task" / "SKILL.md").is_file())
        self.assertTrue(
            (skills_dir / "usw-explain-me" / "SKILL.md").is_file()
        )
        self.assertTrue((skills_dir / "usw-create-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-run-flow" / "SKILL.md").is_file())
        for command_name in ("usw-init.md", "usw-handoff.md", "usw-resume.md"):
            self.assertTrue((commands_dir / command_name).is_file())

    def test_gigacode_extension_points_to_shared_skills(self):
        manifest = json.loads(
            (ROOT / "gigacode-extension.json").read_text(encoding="utf-8")
        )

        skills_dir = ROOT / manifest["skills"]
        commands_dir = ROOT / manifest["commands"]

        self.assertEqual("usw", manifest["name"])
        self.assertTrue(
            (skills_dir / "usw-initialize-project" / "SKILL.md").is_file()
        )
        self.assertTrue((skills_dir / "usw-manage-handoff" / "SKILL.md").is_file())
        self.assertTrue(
            (skills_dir / "usw-brainstorm-solutions" / "SKILL.md").is_file()
        )
        self.assertTrue((skills_dir / "usw-plan-small-steps" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-refine-task" / "SKILL.md").is_file())
        self.assertTrue(
            (skills_dir / "usw-explain-me" / "SKILL.md").is_file()
        )
        self.assertTrue((skills_dir / "usw-create-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-run-flow" / "SKILL.md").is_file())
        for command_name in ("usw-init.md", "usw-handoff.md", "usw-resume.md"):
            self.assertTrue((commands_dir / command_name).is_file())

    def test_codex_marketplace_points_to_plugin(self):
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        plugin = marketplace["plugins"][0]

        self.assertEqual("usw", marketplace["name"])
        self.assertEqual("url", plugin["source"]["source"])
        self.assertEqual(
            "https://github.com/Kimskiykim/usw.git", plugin["source"]["url"]
        )
        self.assertTrue((ROOT / ".codex-plugin" / "plugin.json").is_file())
        self.assertTrue((ROOT / "commands" / "usw-init.md").is_file())
        self.assertTrue(
            (ROOT / "skills" / "usw-initialize-project" / "SKILL.md").is_file()
        )
        self.assertTrue(
            (ROOT / "skills" / "usw-manage-handoff" / "SKILL.md").is_file()
        )
        self.assertTrue(
            (ROOT / "skills" / "usw-brainstorm-solutions" / "SKILL.md").is_file()
        )
        self.assertTrue(
            (ROOT / "skills" / "usw-plan-small-steps" / "SKILL.md").is_file()
        )
        self.assertTrue((ROOT / "skills" / "usw-refine-task" / "SKILL.md").is_file())
        self.assertTrue(
            (ROOT / "skills" / "usw-explain-me" / "SKILL.md").is_file()
        )
        self.assertTrue((ROOT / "skills" / "usw-create-flow" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "skills" / "usw-run-flow" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "commands" / "usw-handoff.md").is_file())
        self.assertTrue((ROOT / "commands" / "usw-resume.md").is_file())

    def test_claude_plugin_is_not_packaged(self):
        self.assertFalse((ROOT / ".claude-plugin").exists())
        self.assertFalse((ROOT / "plugins").exists())


if __name__ == "__main__":
    unittest.main()
