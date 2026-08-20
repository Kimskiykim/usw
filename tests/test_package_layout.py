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
            "sys.version_info < (3, 10)",
            "references/llm-fallback.md",
        ):
            self.assertIn(fragment, skill)
        for fragment in (
            "`artifacts.provider`",
            "`flow-scenario-*.md`",
        ):
            self.assertIn(fragment, fallback)
        for obsolete in (
            "Stop on custom configuration",
            "git check-ignore",
        ):
            self.assertNotIn(obsolete, fallback)

    def test_removed_helpers_are_examples_not_skills(self):
        examples = ROOT / "usw/flows/examples"
        plan = (examples / "plan-small-steps.md").read_text(encoding="utf-8")
        refine = (examples / "refine-intent.md").read_text(encoding="utf-8")

        self.assertTrue(plan.strip())
        self.assertIn("decision_required", refine)
        for name in (
            "usw-plan-small-steps",
            "usw-refine-intent",
            "usw-explain-me",
            "usw-structured-review",
        ):
            self.assertFalse((ROOT / "skills" / name).exists())

    def test_create_flow_defaults_to_ordinary_and_has_one_optional_reference(self):
        skill_dir = ROOT / "skills" / "usw-create-flow"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_dir / "agents/openai.yaml").read_text(encoding="utf-8")

        for fragment in (
            "`--structured`",
            "`-s`",
            "`version-2`",
        ):
            self.assertIn(fragment, skill)
        self.assertEqual(
            {"recipes.md", "version-2.md"},
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

    def test_create_flow_prompt_contract_describes_safe_packaged_layout(self):
        skill = (ROOT / "skills/usw-create-flow/SKILL.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "`<flow-root>/<name>/FLOW.md`",
            "`ambiguous_flow_layout`",
            "`flows.root`",
        ):
            self.assertIn(fragment, skill)
        self.assertNotIn("Разрешить ровно один origin selector", skill)

    def test_find_flow_prompt_contract_describes_bounded_discovery(self):
        skill = (ROOT / "skills/usw-find-flow/SKILL.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "`<name>.md`",
            "`<name>/FLOW.md`",
            "`ambiguous_flow_layout`",
            "`resolve`",
        ):
            self.assertIn(fragment, skill)

    def test_assess_flow_prompt_contract_forbids_resource_reads(self):
        skill = (ROOT / "skills/usw-assess-flow/SKILL.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "`flow_directory`",
            "`unverified`",
            "`<name>/FLOW.md`",
        ):
            self.assertIn(fragment, skill)

    def test_readme_documents_packaged_flows_and_legacy_compatibility(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for fragment in (
            "review/FLOW.md",
            "review/scripts/check.py",
            "`<name>.md`",
            "`ambiguous_flow_layout`",
            "`flow_directory`",
        ):
            self.assertIn(fragment, readme)

    def test_create_flow_has_bounded_human_controlled_design_recipes(self):
        skill = (ROOT / "skills/usw-create-flow/SKILL.md").read_text(
            encoding="utf-8"
        )
        index = (
            ROOT / "skills/usw-create-flow/references/recipes.md"
        ).read_text(encoding="utf-8")
        recipes_dir = ROOT / "skills/usw-create-flow/references/recipes"

        recipe_files = {
            "Проверка результата": "result-check.md",
            "Human decision": "human-decision.md",
            "Подтверждение внешнего действия": "external-action-approval.md",
            "Обработка ошибки": "error-handling.md",
            "Ограниченная доработка": "bounded-refinement.md",
            "Независимые проверки": "independent-checks.md",
            "Ревью субагентами": "subagent-review.md",
            "Оркестрация с субагентами": "subagent-orchestration.md",
            "Эскалация": "escalation.md",
            "Выбор из вариантов": "variant-selection.md",
            "Сбор недостающих входов": "input-preflight.md",
            "Ожидание внешнего события": "external-event-wait.md",
            "Адаптивная интенсивность": "adaptive-intensity.md",
            "Обработка списка элементов": "list-processing.md",
            "Повторное использование capability": "capability-reuse.md",
        }
        self.assertEqual(
            set(recipe_files.values()),
            {path.name for path in recipes_dir.glob("*.md")},
        )
        for name, filename in recipe_files.items():
            with self.subTest(recipe=name):
                self.assertIn(name, index)
                self.assertIn(f"recipes/{filename}", index)
                content = (recipes_dir / filename).read_text(encoding="utf-8")
                self.assertTrue(content.startswith(f"# {name}"))

        self.assertIn("references/recipes.md", skill)
        for fragment in ("`применить`", "`изменить`", "`пропустить`"):
            self.assertIn(fragment, skill)

    def test_run_flow_has_one_text_path_and_local_precedence(self):
        skill_dir = ROOT / "skills/usw-run-flow"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        for fragment in (
            "--local",
            "`-l`",
            "--shared",
            ".usw/flows",
            "--origin local",
            "`markdown`",
            "`assert-current`",
        ):
            self.assertIn(fragment, skill)
        self.assertFalse((skill_dir / "references").exists())

    def test_readme_explains_routed_roots_nested_children_and_cleanup(self):
        readme = " ".join(
            (ROOT / "README.md").read_text(encoding="utf-8").split()
        )
        for fragment in (
            ".usw/HANDOFF.md",
            "/usw-handoff finish <operation-id>",
            "/usw-handoff cleanup",
        ):
            self.assertIn(fragment, readme)

    def test_find_flow_is_explicit_read_only_discovery(self):
        skill_dir = ROOT / "skills/usw-find-flow"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_dir / "agents/openai.yaml").read_text(encoding="utf-8")

        required_fragments = (
            "`match`",
            "`ambiguous`",
            "`no-match`",
            ".usw/flows",
            "$usw-run-flow",
        )
        for fragment in required_fragments:
            self.assertIn(fragment, skill)
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertFalse((skill_dir / "scripts").exists())
        self.assertFalse((ROOT / "skills/usw-route-task").exists())
        self.assertFalse((ROOT / "commands/usw-route-task.md").exists())

    def test_assess_flow_is_explicit_semantic_read_only_analysis(self):
        skill_dir = ROOT / "skills/usw-assess-flow"
        skill_path = skill_dir / "SKILL.md"
        metadata_path = skill_dir / "agents/openai.yaml"
        command_path = ROOT / "commands/usw-assess-flow.md"

        self.assertTrue(skill_path.is_file())
        self.assertTrue(metadata_path.is_file())
        self.assertTrue(command_path.is_file())

        skill = skill_path.read_text(encoding="utf-8")
        metadata = metadata_path.read_text(encoding="utf-8")
        command = command_path.read_text(encoding="utf-8")

        for fragment in (
            "`--local`",
            "`-l`",
            "`--shared`",
            "`inspect`",
            "`executable`",
            "`executable-with-risks`",
            "`not-executable`",
            "`insufficient-data`",
            "Terminal paths",
            "Dependencies",
            "Findings",
            "Scenario trace",
            "`blocking`",
            "`risk`",
            "`confirmed`",
            "`missing`",
            "`unverified`",
            "`LOOP`",
            "`decision_required`",
        ):
            self.assertIn(fragment, skill)

        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertIn("usw-assess-flow", command)
        self.assertFalse((skill_dir / "scripts").exists())

    def test_assess_flow_acceptance_evidence_is_checked_in(self):
        changes = ROOT / "openspec/changes"
        change = changes / "add-flow-assessment"
        if not change.is_dir():
            archived = sorted(
                (changes / "archive").glob("*-add-flow-assessment")
            )
            self.assertTrue(archived)
            change = archived[-1]
        acceptance = change / "tasks/4.1-acceptance"
        fixture_dir = acceptance / "fixtures"
        reports_path = acceptance / "semantic-reports.md"
        smoke = (acceptance / "smoke.md").read_text(encoding="utf-8")
        expected_fixtures = {
            "bounded-retry.md",
            "finite.md",
            "handled-missing-dependency.md",
            "missing-dependency.md",
            "unconditional-cycle.md",
            "uncertain-retry.md",
            "unsafe-repeat.md",
        }

        self.assertEqual(
            expected_fixtures,
            {path.name for path in fixture_dir.glob("*.md")},
        )
        self.assertTrue(reports_path.is_file())
        reports = reports_path.read_text(encoding="utf-8")
        for fixture in sorted(expected_fixtures):
            stem = Path(fixture).stem
            self.assertIn(f"[fixtures/{fixture}](fixtures/{fixture})", smoke)
            self.assertIn(f"## {stem}", reports)
        self.assertIn("[Raw semantic reports](semantic-reports.md)", smoke)
        self.assertNotIn("Expected and observed result", smoke)
        self.assertNotIn("were not added to the repository", smoke)

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
            "usw-assess-flow.md": "usw-assess-flow",
        }

        for command_name, skill_name in expectations.items():
            with self.subTest(command=command_name):
                command = (ROOT / "commands" / command_name).read_text(
                    encoding="utf-8"
                )
                self.assertIn(skill_name, command)

    def test_assess_flow_is_documented_in_package_metadata(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        plugin = json.loads(
            (ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        qwen = json.loads(
            (ROOT / "qwen-extension.json").read_text(encoding="utf-8")
        )
        gigacode = json.loads(
            (ROOT / "gigacode-extension.json").read_text(encoding="utf-8")
        )

        for fragment in (
            "$usw-assess-flow [--local|-l|--shared] <flow-name>",
            "`executable-with-risks`",
            "`not-executable`",
        ):
            self.assertIn(fragment, readme)

        self.assertIn("assess", plugin["description"])
        self.assertIn("assess", plugin["interface"]["shortDescription"])
        self.assertIn("assess", qwen["description"])
        self.assertIn("assess", gigacode["description"])

    def test_qwen_extension_points_to_shared_skills(self):
        manifest = json.loads((ROOT / "qwen-extension.json").read_text(encoding="utf-8"))

        skills_dir = ROOT / manifest["skills"]
        commands_dir = ROOT / manifest["commands"]

        self.assertEqual("usw", manifest["name"])
        self.assertTrue(
            (skills_dir / "usw-initialize-project" / "SKILL.md").is_file()
        )
        self.assertTrue((skills_dir / "usw-manage-handoff" / "SKILL.md").is_file())
        self.assertFalse((skills_dir / "usw-refine-task").exists())
        self.assertTrue((skills_dir / "usw-create-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-run-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-find-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-assess-flow" / "SKILL.md").is_file())
        for command_name in (
            "usw-init.md",
            "usw-handoff.md",
            "usw-resume.md",
            "usw-reviewer-llm-critic.md",
            "usw-find-flow.md",
            "usw-assess-flow.md",
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
        self.assertFalse((skills_dir / "usw-refine-task").exists())
        self.assertTrue((skills_dir / "usw-create-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-run-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-find-flow" / "SKILL.md").is_file())
        self.assertTrue((skills_dir / "usw-assess-flow" / "SKILL.md").is_file())
        for command_name in (
            "usw-init.md",
            "usw-handoff.md",
            "usw-resume.md",
            "usw-reviewer-llm-critic.md",
            "usw-find-flow.md",
            "usw-assess-flow.md",
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
        self.assertFalse((ROOT / "skills" / "usw-refine-task").exists())
        self.assertTrue((ROOT / "skills" / "usw-create-flow" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "skills" / "usw-run-flow" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "skills" / "usw-find-flow" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "skills" / "usw-assess-flow" / "SKILL.md").is_file())
        self.assertTrue((ROOT / "commands" / "usw-handoff.md").is_file())
        self.assertTrue((ROOT / "commands" / "usw-resume.md").is_file())
        self.assertTrue(
            (ROOT / "commands" / "usw-reviewer-llm-critic.md").is_file()
        )
        for command_name in (
            "usw-find-flow.md",
            "usw-assess-flow.md",
        ):
            self.assertTrue((ROOT / "commands" / command_name).is_file())

    def test_claude_plugin_points_to_shared_skills(self):
        manifest = json.loads(
            (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("usw", manifest["name"])
        self.assertIn("assess", manifest["description"])
        plugin = marketplace["plugins"][0]
        self.assertEqual("usw", plugin["name"])
        self.assertEqual("./", plugin["source"])
        for skill_name in (
            "usw-initialize-project",
            "usw-manage-handoff",
            "usw-create-flow",
            "usw-run-flow",
            "usw-find-flow",
            "usw-assess-flow",
        ):
            self.assertTrue((ROOT / "skills" / skill_name / "SKILL.md").is_file())
        for command_name in (
            "usw-init.md",
            "usw-handoff.md",
            "usw-resume.md",
            "usw-reviewer-llm-critic.md",
            "usw-find-flow.md",
            "usw-assess-flow.md",
        ):
            self.assertTrue((ROOT / "commands" / command_name).is_file())
        self.assertFalse((ROOT / "plugins").exists())


if __name__ == "__main__":
    unittest.main()
