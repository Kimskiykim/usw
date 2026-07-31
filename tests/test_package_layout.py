import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class PackageLayoutTests(unittest.TestCase):
    def test_packaged_flow_dependencies_cover_literal_skill_calls(self):
        examples = (
            ROOT / "skills/usw-initialize-project/templates/flows/examples"
        )
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")
        installer_match = re.search(
            r'^SKILL_NAMES="([^"]*)"$', installer, re.MULTILINE
        )
        self.assertIsNotNone(installer_match)
        installed_skills = set(installer_match.group(1).split())
        call_pattern = re.compile(r"CALL SKILL `([^`]+)`")
        dependency_pattern = re.compile(
            r"^- (bundled|external) skill: `([^`]+)`$", re.MULTILINE
        )

        for path in examples.glob("*.md"):
            with self.subTest(example=path.name):
                content = path.read_text(encoding="utf-8")
                calls = set(call_pattern.findall(content))
                dependencies = dependency_pattern.findall(content)
                declared = {name: kind for kind, name in dependencies}

                self.assertEqual(len(dependencies), len(declared))
                self.assertEqual(calls, set(declared))
                for name, kind in declared.items():
                    if kind == "external":
                        self.assertNotIn(name, installed_skills)
                        continue
                    self.assertTrue((ROOT / "skills" / name / "SKILL.md").is_file())
                    self.assertIn(name, installed_skills)

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
            "local/HANDOFF.md": "## Operations",
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
            "## Создание и проверка",
            "`--structured`",
            "`-s`",
            "Без него не читать reference",
            "ordinary или `version-2` форму",
            "не выполнять описанный flow",
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
        self.assertIn("Применять только нужные маркеры", content)
        self.assertIn("human decision point", content)

    def test_create_flow_stays_within_authoring_scope(self):
        skill = (ROOT / "skills/usw-create-flow/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("$usw-run-flow --local", skill)
        self.assertIn("$usw-run-flow --shared", skill)
        for removed in (
            "Опциональный анализ",
            "retired validator",
            "--experimental-structured",
        ):
            self.assertNotIn(removed, skill)

    def test_create_flow_has_bounded_human_controlled_design_recipes(self):
        skill = (ROOT / "skills/usw-create-flow/SKILL.md").read_text(
            encoding="utf-8"
        )
        spec = (
            ROOT
            / "openspec/changes/add-guided-flow-authoring/specs"
            / "guided-flow-authoring/spec.md"
        ).read_text(encoding="utf-8")

        recipe_names = (
            "Проверка результата",
            "Human decision",
            "Подтверждение внешнего действия",
            "Обработка ошибки",
            "Ограниченная доработка",
            "Независимые проверки",
            "Повторное использование capability",
        )
        recipe_headings = [
            line.removeprefix("### ")
            for line in skill.splitlines()
            if line.startswith("### ")
        ]
        self.assertEqual(list(recipe_names), recipe_headings)

        for fragment in (
            "## Подсказки по проектированию",
            "три наиболее релевантные подсказки",
            "`применить`, `изменить` или `пропустить`",
            "Для ordinary Markdown",
            "Только для `version-2`",
            "`изменить` сначала показывает",
            "для его записи пользователь должен отдельно",
            "После revision не запускать design scan повторно",
            "Примеры в рецептах ниже показывают только `version-2` форму",
            "Не копировать их\nstructured markers в ordinary flow",
        ):
            self.assertIn(fragment, skill)

        self.assertLess(
            skill.index("Сообщить имя, origin, путь"),
            skill.index("После успешного сохранения и отчёта"),
        )

        verification = skill.split("### Проверка результата", 1)[1].split(
            "### Human decision", 1
        )[0]
        self.assertLess(
            verification.index("Сначала добавить наблюдаемую проверку"),
            verification.index("`GATE` предлагать только"),
        )

        human_decision = skill.split("### Human decision", 1)[1].split(
            "### Подтверждение внешнего действия", 1
        )[0]
        external_approval = skill.split(
            "### Подтверждение внешнего действия", 1
        )[1].split("### Обработка ошибки", 1)[0]
        error_handling = skill.split("### Обработка ошибки", 1)[1].split(
            "### Ограниченная доработка", 1
        )[0]
        for recipe in (human_decision, external_approval, error_handling):
            self.assertTrue(
                "только когда" in recipe or "только если" in recipe
            )

        refinement = skill.split("### Ограниченная доработка", 1)[1].split(
            "### Независимые проверки", 1
        )[0]
        for fragment in (
            "read-only, идемпотентны или безопасно обратимы",
            "критерий выхода и предел",
            "approval и внешнее действие\nоставлять после выхода из цикла",
        ):
            self.assertIn(fragment, refinement)

        parallel = skill.split("### Независимые проверки", 1)[1].split(
            "### Повторное использование capability", 1
        )[0]
        self.assertIn(
            "Не предлагать `PARALLEL` для зависимых действий", parallel
        )

        capability = skill.split(
            "### Повторное использование capability", 1
        )[1]
        self.assertIn("текущем списке доступных skills", capability)
        self.assertIn(
            "Одного имени без присутствия в текущем списке", capability
        )
        self.assertNotIn("или CALL FLOW", capability)
        self.assertIn("не предлагать `CALL FLOW`", capability)

        for fragment in (
            "`применить`, `изменить` and `пропустить`",
            "present in the current available-skills list",
            "does not write until a\n  later explicit `применить`",
            "keeps that action and its approval outside the loop",
        ):
            self.assertIn(fragment, spec)

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
            "independent top-level invocations",
            "Exact Begin operation ID является root execution identity",
            "`assert-current`",
            "Nested child не владеет durable state",
            "Только root пишет aggregate Outcome",
            "Новый Begin создаёт другую route",
        ):
            self.assertIn(fragment, skill)
        self.assertFalse((skill_dir / "references").exists())

    def test_readme_explains_routed_roots_nested_children_and_cleanup(self):
        readme = " ".join(
            (ROOT / "README.md").read_text(encoding="utf-8").split()
        )
        for fragment in (
            ".usw/HANDOFF.md` хранит только маршруты",
            "чат UI:",
            "чат backend:",
            "USW не обнаруживает и не разрешает конфликты в product files",
            "не получает собственную route",
            "Только root агрегирует результаты детей",
            "/usw-handoff finish <operation-id>",
            "Для rollback",
            "generic idle HANDOFF старой версии",
            "не создаёт scheduler",
        ):
            self.assertIn(fragment, readme)

    def test_find_flow_is_explicit_read_only_discovery(self):
        skill_dir = ROOT / "skills/usw-find-flow"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_dir / "agents/openai.yaml").read_text(encoding="utf-8")

        required_fragments = (
            "одно описание намерения",
            "Writes and side effects: none",
            "`match`, `ambiguous` или `no-match`",
            ".usw/flows",
            "configured shared",
            "safe kebab-case",
            "не следовать symlink",
            "safe `resolve`",
            "Не искать packaged examples",
            "готовую команду `$usw-run-flow`",
            "Не запускать эту команду",
            "не вызывать его",
            "не читает и не изменяет HANDOFF",
        )
        for fragment in required_fragments:
            self.assertIn(fragment, skill)
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertFalse((skill_dir / "scripts").exists())
        self.assertFalse((ROOT / "skills/usw-route-task").exists())
        self.assertFalse((ROOT / "commands/usw-route-task.md").exists())

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
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".pyo"}
        }
        self.assertEqual(38, len(preserved))
        archived_designs = tuple(
            (ROOT / "openspec/changes/archive").glob(
                "*-refocus-text-first-workflows/design.md"
            )
        )
        self.assertEqual(1, len(archived_designs))
        design = archived_designs[0].read_text(encoding="utf-8")
        for path in preserved:
            self.assertIn(f"`{path}`", design)

    def test_public_commands_delegate_to_internal_skills(self):
        expectations = {
            "usw-init.md": "usw-initialize-project",
            "usw-handoff.md": "usw-manage-handoff",
            "usw-resume.md": "usw-manage-handoff",
            "usw-find-flow.md": "usw-find-flow",
            "usw-refine-intent.md": "usw-refine-intent",
            "usw-plan-small-steps.md": "usw-plan-small-steps",
            "usw-explain-me.md": "usw-explain-me",
        }

        for command_name, skill_name in expectations.items():
            with self.subTest(command=command_name):
                command = (ROOT / "commands" / command_name).read_text(
                    encoding="utf-8"
                )
                self.assertIn(skill_name, command)
        handoff = (ROOT / "commands/usw-handoff.md").read_text(
            encoding="utf-8"
        )
        resume = (ROOT / "commands/usw-resume.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("exact current operation", handoff)
        self.assertIn("zero/one/many", handoff)
        self.assertIn("optional exact operation ID", resume)
        self.assertIn("zero/one/many", resume)

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
        self.assertTrue((skills_dir / "usw-find-flow" / "SKILL.md").is_file())
        for command_name in (
            "usw-init.md",
            "usw-handoff.md",
            "usw-resume.md",
            "usw-reviewer-llm-critic.md",
            "usw-find-flow.md",
            "usw-refine-intent.md",
            "usw-plan-small-steps.md",
            "usw-explain-me.md",
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
        self.assertTrue((skills_dir / "usw-find-flow" / "SKILL.md").is_file())
        for command_name in (
            "usw-init.md",
            "usw-handoff.md",
            "usw-resume.md",
            "usw-reviewer-llm-critic.md",
            "usw-find-flow.md",
            "usw-refine-intent.md",
            "usw-plan-small-steps.md",
            "usw-explain-me.md",
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
        self.assertTrue((ROOT / "skills" / "usw-find-flow" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "commands" / "usw-handoff.md").is_file())
        self.assertTrue((ROOT / "commands" / "usw-resume.md").is_file())
        self.assertTrue(
            (ROOT / "commands" / "usw-reviewer-llm-critic.md").is_file()
        )
        for command_name in (
            "usw-find-flow.md",
            "usw-refine-intent.md",
            "usw-plan-small-steps.md",
            "usw-explain-me.md",
        ):
            self.assertTrue((ROOT / "commands" / command_name).is_file())

    def test_claude_plugin_is_not_packaged(self):
        self.assertFalse((ROOT / ".claude-plugin").exists())
        self.assertFalse((ROOT / "plugins").exists())


if __name__ == "__main__":
    unittest.main()
