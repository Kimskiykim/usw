import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class PackageLayoutTests(unittest.TestCase):
    def test_initialize_skill_packages_standalone_execution_templates(self):
        templates = ROOT / "skills" / "usw-initialize-project" / "templates"
        expected_fragments = {
            "change/proposal.md": "## Why",
            "change/design.md": "## Decisions",
            "change/spec.md": "## ADDED Requirements",
            "change/tasks.md": "tasks/1.1-{{task_slug}}/task.md",
            "task/task.md": "## Milestone log",
            "task/development-evidence.md": "Writer authority: Development only.",
            "task/testing-evidence.md": "Writer authority: Testing only.",
            "review/receipt.md": "## Reviewed artifact identities",
            "flows/examples/chat-review.md": "# Flow: chat-review",
            "flows/examples/dev-test.md": "# Flow: dev-test",
            "local/HANDOFF.md": "## Active work",
            "usw.yaml": "root: usw/reviews",
        }

        for relative_path, fragment in expected_fragments.items():
            with self.subTest(template=relative_path):
                content = (templates / relative_path).read_text(encoding="utf-8")
                self.assertIn(fragment, content)
        self.assertEqual(
            set(),
            {path.name for path in (templates / "flows").glob("flow-scenario-*.md")},
        )

    def test_initialize_skill_selects_python_and_has_confirmed_llm_fallback(self):
        skill_dir = ROOT / "skills" / "usw-initialize-project"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        fallback = (skill_dir / "references" / "llm-fallback.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "Try `python3`, then `python`",
            "sys.version_info < (3, 10)",
            "never hide a script or configuration error with fallback",
            "not write anything until the user explicitly agrees",
            "references/llm-fallback.md",
        ):
            self.assertIn(fragment, skill)
        for fragment in (
            "reject the removed `artifacts.provider` field",
            "accept safe custom artifact, flow and review roots",
            "repository tracking policy belongs to the\nuser",
            "Preserve every existing regular file byte-for-byte",
            "Never overwrite, merge, delete, chmod, or follow links",
            "the two packaged examples",
            "Do not create, migrate, or remove legacy\n`flow-scenario-*.md` files",
        ):
            self.assertIn(fragment, fallback)
        for obsolete in (
            "Stop on custom configuration",
            "git check-ignore",
        ):
            self.assertNotIn(obsolete, fallback)

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

    def test_refine_intent_skill_persists_one_local_decision_case_per_turn(self):
        skill_dir = ROOT / "skills" / "usw-refine-intent"
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
            ".usw/refinements/",
            "ненормативные заметки",
        )
        for fragment in required_fragments:
            self.assertIn(fragment, skill)
        for artifact in ("session.md", "decisions.md", "outcome.md"):
            self.assertTrue((skill_dir / "assets" / artifact).is_file())
        self.assertIn("$usw-refine-intent", metadata)
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

    def test_create_flow_defaults_to_ordinary_and_has_one_optional_reference(self):
        skill_dir = ROOT / "skills" / "usw-create-flow"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_dir / "agents/openai.yaml").read_text(encoding="utf-8")

        for fragment in (
            "## Подготовка",
            "## Гарантии",
            "## Граница выполнения",
            "`--structured`",
            "`-s`",
            "не читать version-specific reference",
            "ordinary/structured style",
            "Никогда не вызывать `usw-run-flow`",
        ):
            self.assertIn(fragment, skill)
        self.assertEqual(
            {"version-2.md"},
            {path.name for path in (skill_dir / "references").glob("*.md")},
        )
        self.assertIn("allow_implicit_invocation: true", metadata)

    def test_structured_reference_is_model_readable_not_validator_backed(self):
        content = (
            ROOT / "skills/usw-create-flow/references/version-2.md"
        ).read_text(encoding="utf-8")
        for fragment in ("version-2", "`CALL`", "`GATE`", "`LOOP`", "`PARALLEL`"):
            self.assertIn(fragment, content)
        for removed in (
            "../usw-run-flow/scripts/run_flow.py",
            "checkpoint-save",
            "action-specific input map",
            "$usw-run-flow --experimental-structured",
        ):
            self.assertNotIn(removed, content)
        self.assertIn("не machine DSL", content)
        self.assertIn("Не заявлять parser или validator", content)

    def test_create_flow_keeps_optional_analysis_separate(self):
        skill = (ROOT / "skills/usw-create-flow/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("После успешного сохранения", skill)
        self.assertIn("Не проводить его без согласия", skill)
        self.assertIn("не изменять flow без отдельного одобрения", skill)

    def test_run_flow_has_one_text_path_and_local_precedence(self):
        skill_dir = ROOT / "skills/usw-run-flow"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        for fragment in (
            "--local",
            "`-l`",
            "--shared",
            ".usw/flows",
            "Без selector искать local flow первым, затем shared",
            "--origin local",
            "Использовать только возвращённый `markdown`",
            "не machine DSL",
            "уникального invocation token",
            "Допустимые Outcome statuses",
            "`in_progress` создаётся только Begin",
            "`idle` — только explicit Finish",
        ):
            self.assertIn(fragment, skill)
        self.assertFalse((skill_dir / "references").exists())

    def test_route_task_is_explicit_preview_first_orchestration(self):
        skill_dir = ROOT / "skills/usw-route-task"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_dir / "agents/openai.yaml").read_text(encoding="utf-8")

        required_fragments = (
            "одну исходную задачу",
            "Если задача простая",
            "Не выполнять задачу",
            ".usw/flows",
            "configured shared",
            "templates/flows/examples",
            "не следовать symlink",
            "`exact`",
            "`adapted`",
            "`new`",
            "при сомнении — `local`",
            "До preview ничего не записывать",
            "Если пользователь отклоняет preview",
            "не вызывать authoring capability",
            "Existing source flow никогда не изменяется",
            "обычные permission",
        )
        for fragment in required_fragments:
            self.assertIn(fragment, skill)
        approved = skill.split("## Approved continuation", 1)[1]
        self.assertLess(
            approved.index("`usw-create-flow`"),
            approved.index("`usw-run-flow`"),
        )
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertFalse((skill_dir / "scripts").exists())

    def test_research_snapshot_is_outside_package_surfaces(self):
        snapshot = ROOT / "research/structured-runtime"
        self.assertTrue((snapshot / "runtime/run_flow.py").is_file())
        self.assertTrue((snapshot / "README.md").is_file())
        self.assertFalse(snapshot.is_relative_to(ROOT / "skills"))
        self.assertFalse(snapshot.is_relative_to(ROOT / "commands"))
        preserved = {
            path.relative_to(snapshot).as_posix()
            for path in snapshot.rglob("*")
            if path.is_file()
        }
        self.assertEqual(34, len(preserved))
        design = (
            ROOT
            / "openspec/changes/refocus-text-first-workflows/design.md"
        ).read_text(encoding="utf-8")
        for path in preserved:
            self.assertIn(f"`{path}`", design)

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
        self.assertTrue((skills_dir / "usw-plan-small-steps" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-refine-intent" / "SKILL.md").is_file())
        self.assertFalse((skills_dir / "usw-refine-task").exists())
        self.assertTrue(
            (skills_dir / "usw-explain-me" / "SKILL.md").is_file()
        )
        self.assertTrue((skills_dir / "usw-create-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-run-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-route-task" / "SKILL.md").is_file())
        for command_name in (
            "usw-init.md",
            "usw-handoff.md",
            "usw-resume.md",
            "usw-reviewer-llm-critic.md",
        ):
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
        self.assertTrue((skills_dir / "usw-plan-small-steps" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-refine-intent" / "SKILL.md").is_file())
        self.assertFalse((skills_dir / "usw-refine-task").exists())
        self.assertTrue(
            (skills_dir / "usw-explain-me" / "SKILL.md").is_file()
        )
        self.assertTrue((skills_dir / "usw-create-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-run-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-route-task" / "SKILL.md").is_file())
        for command_name in (
            "usw-init.md",
            "usw-handoff.md",
            "usw-resume.md",
            "usw-reviewer-llm-critic.md",
        ):
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
            (ROOT / "skills" / "usw-plan-small-steps" / "SKILL.md").is_file()
        )
        self.assertTrue((ROOT / "skills" / "usw-refine-intent" / "SKILL.md").is_file())
        self.assertFalse((ROOT / "skills" / "usw-refine-task").exists())
        self.assertTrue(
            (ROOT / "skills" / "usw-explain-me" / "SKILL.md").is_file()
        )
        self.assertTrue((ROOT / "skills" / "usw-create-flow" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "skills" / "usw-run-flow" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "skills" / "usw-route-task" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "commands" / "usw-handoff.md").is_file())
        self.assertTrue((ROOT / "commands" / "usw-resume.md").is_file())
        self.assertTrue(
            (ROOT / "commands" / "usw-reviewer-llm-critic.md").is_file()
        )

    def test_claude_plugin_is_not_packaged(self):
        self.assertFalse((ROOT / ".claude-plugin").exists())
        self.assertFalse((ROOT / "plugins").exists())


if __name__ == "__main__":
    unittest.main()
