import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
TEMPLATES = ROOT / "skills/usw-initialize-project/templates/flows"
SCRIPT = ROOT / "skills/usw-initialize-project/scripts/flow_scenario.py"
SPEC = importlib.util.spec_from_file_location("flow_scenario", SCRIPT)
FLOWS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = FLOWS
SPEC.loader.exec_module(FLOWS)

CUSTOM_SCRIPT = ROOT / "skills/usw-run-flow/scripts/run_flow.py"
CUSTOM_SPEC = importlib.util.spec_from_file_location("custom_flow", CUSTOM_SCRIPT)
CUSTOM = importlib.util.module_from_spec(CUSTOM_SPEC)
assert CUSTOM_SPEC.loader is not None
sys.modules[CUSTOM_SPEC.name] = CUSTOM
CUSTOM_SPEC.loader.exec_module(CUSTOM)


class FlowScenarioTests(unittest.TestCase):
    def content(self, name: str) -> str:
        return (TEMPLATES / f"flow-scenario-{name}.md").read_text(encoding="utf-8")

    def test_exactly_three_initial_role_scenarios_are_valid(self):
        files = sorted(path.name for path in TEMPLATES.glob("flow-scenario-*.md"))
        self.assertEqual(
            [
                "flow-scenario-analysis.md",
                "flow-scenario-development.md",
                "flow-scenario-testing.md",
            ],
            files,
        )
        roles = {
            FLOWS.validate_scenario(self.content(name)).role
            for name in ("analysis", "development", "testing")
        }
        self.assertEqual({"Analysis", "Development", "Testing"}, roles)

    def test_each_scenario_has_internal_and_receiving_transition_gates(self):
        expected_transition = {
            "analysis": "transition-review-development",
            "development": "transition-review-testing",
            "testing": "transition-review-delivery",
        }
        for name, transition in expected_transition.items():
            with self.subTest(name=name):
                scenario = FLOWS.validate_scenario(self.content(name))
                self.assertIn("internal-review", scenario.actions)
                self.assertIn(transition, scenario.actions)
                self.assertIn("review-receipt", scenario.artifact_roles)

    def test_missing_authority_and_stop_are_rejected(self):
        valid = self.content("analysis")
        authority_start = valid.index("## Write authority")
        stop_start = valid.index("## Stop conditions")
        outputs_start = valid.index("## Outputs")
        no_authority = valid[:authority_start] + "## Write authority\n\n" + valid[stop_start:]
        no_stop = valid[:stop_start] + "## Stop conditions\n\n" + valid[outputs_start:]
        for content in (no_authority, no_stop):
            with self.assertRaises(FLOWS.ScenarioError):
                FLOWS.validate_scenario(content)

    def test_invalid_branch_and_unknown_action_are_rejected(self):
        valid = self.content("development")
        invalid_branch = valid.replace("`stop:scope-complete`", "`missing-action`")
        unknown_action = valid.replace("1. `check-inputs`", "1. `secret-action`")
        for content in (invalid_branch, unknown_action):
            with self.assertRaises(FLOWS.ScenarioError):
                FLOWS.validate_scenario(content)

    def test_fourth_review_flow_is_rejected(self):
        review = self.content("analysis").replace("- Role: `Analysis`", "- Role: `Review`")
        with self.assertRaisesRegex(FLOWS.ScenarioError, "three role flows"):
            FLOWS.validate_scenario(review)

    def test_role_cannot_claim_another_roles_actions_or_writes(self):
        analysis = self.content("analysis")
        unauthorized_action = analysis.replace(
            "10. `transition-review-development`",
            "10. `transition-review-development`\n11. `execute-bounded-scope`",
        )
        unauthorized_write = analysis.replace(
            "- `local-checkpoint`", "- `local-checkpoint`\n- `testing-evidence`"
        )
        for content in (unauthorized_action, unauthorized_write):
            with self.subTest(content=content), self.assertRaisesRegex(
                FLOWS.ScenarioError, "unauthorized"
            ):
                FLOWS.validate_scenario(content)

    def test_missing_project_scenario_has_no_packaged_runtime_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            flow_root = Path(directory)
            with self.assertRaisesRegex(FLOWS.ScenarioError, "project scenario is missing"):
                FLOWS.load_project_scenario(flow_root, "analysis")

    def test_project_scenario_filename_must_match_declared_role(self):
        with tempfile.TemporaryDirectory() as directory:
            flow_root = Path(directory)
            (flow_root / "flow-scenario-analysis.md").write_text(
                self.content("testing"), encoding="utf-8"
            )
            with self.assertRaisesRegex(FLOWS.ScenarioError, "expected Analysis"):
                FLOWS.load_project_scenario(flow_root, "analysis")


class CustomFlowTests(unittest.TestCase):
    def structured_content(self) -> str:
        return """# Flow: prepare-and-review

Prepare, review, and verify a plan.

## Контракт

- Версия: `version-2`

## Порядок действий

1. `prepare-plan` — подготовить план: CALL SKILL `usw-plan-small-steps`.
2. `review-plan` — CALL HUMAN `reviewer`; GATE: выбрать `accepted` или `needs-work`.
   - IF `accepted`: продолжить к `independent-checks`.
   - ELIF `needs-work`: продолжить LOOP `revise-plan`.
   - ELSE: запросить один из объявленных вариантов.
3. `revise-plan` — LOOP не более 2 попыток, пока `review-plan` не вернёт `accepted`.
   - Каждая попытка дорабатывает план: CALL SKILL `usw-plan-small-steps`.
   - После попытки: снова `review-plan`.
   - При исчерпании: передать решение человеку.
4. `independent-checks` — PARALLEL:
   - `check-scope` — CALL SUBAGENT `scope-reviewer`.
     - Действия субагента:
       1. `analyze-scope` — CALL SKILL `usw-brainstorm-solutions`.
   - `check-safety` — CALL HUMAN `security-reviewer`.
5. `run-check` — CALL SCRIPT `scripts/check.py`.
   - Аргументы: `--strict` `one argument`
6. `final-review` — CALL FLOW `review-flow`.
"""

    def concise_content(self) -> str:
        return """# Flow: plan-check

## Контракт

- Версия: `1`

## Порядок действий

1. Скилл: `usw-plan-small-steps`
2. Скрипт: `scripts/check_plan.py`
   - Аргументы: `--strict` `one argument`
"""

    def content(self) -> str:
        return """# Flow: plan-check

Free-form documentation is ignored by the executor.

## Контракт

- Версия: `1`

## Порядок действий

1. Скилл: `usw-plan-small-steps`
   - Пишет: `task-index`
2. Скрипт: `scripts/check_plan.py`
   - Аргументы: `--strict` `one argument`
   - Пишет: нет

## Полномочия записи

- `task-index`

## Notes

This remains ordinary Markdown.
"""

    def test_parses_minimal_linear_markdown_contract(self):
        flow = CUSTOM.parse_custom_flow(self.content(), "plan-check")

        self.assertEqual(("1", "2"), flow.actions)
        self.assertEqual((), flow.branches)
        self.assertEqual(frozenset({"task-index"}), flow.artifact_roles)
        self.assertEqual("shared", flow.origin)
        self.assertEqual("skill", flow.steps[0].kind)
        self.assertEqual(("--strict", "one argument"), flow.steps[1].arguments)
        self.assertTrue(flow.identity.startswith("usw-flow-v1:"))

    def test_chat_review_defaults_to_whole_markdown_input(self):
        content = (ROOT / "usw/flows/chat-review.md").read_text(encoding="utf-8")
        flow = CUSTOM.parse_custom_flow(content, "chat-review")

        self.assertEqual(
            ("parallel-reviews", "prepare-presentation", "handle-follow-up"),
            flow.actions,
        )
        self.assertEqual(
            (
                ("prepare-presentation", "iterate-findings", "handle-follow-up"),
                ("prepare-presentation", "show-proposal", "handle-follow-up"),
                ("prepare-presentation", "make-decision", "handle-follow-up"),
            ),
            flow.branches,
        )
        self.assertIn("Reviewer A:", content)
        self.assertIn("Reviewer B:", content)
        self.assertIn("## Режим запуска", content)
        self.assertIn("без action map", content)
        self.assertIn("--experimental-structured", content)

    def test_parses_concise_contract_without_write_metadata(self):
        flow = CUSTOM.parse_custom_flow(self.concise_content(), "plan-check")

        self.assertIsNone(flow.artifact_roles)
        self.assertTrue(all(step.declared_writes is None for step in flow.steps))
        self.assertEqual(("--strict", "one argument"), flow.steps[1].arguments)

    def test_parses_structured_calls_and_control_blocks(self):
        flow = CUSTOM.parse_custom_flow(
            self.structured_content(), "prepare-and-review"
        )

        self.assertEqual("version-2", flow.version)
        self.assertEqual(
            (
                "prepare-plan",
                "review-plan",
                "revise-plan",
                "independent-checks",
                "run-check",
                "final-review",
            ),
            flow.actions,
        )
        self.assertEqual(
            ("skill", "human", "skill", "parallel", "script", "flow"),
            tuple(step.kind for step in flow.steps),
        )
        self.assertEqual(
            (
                ("review-plan", "accepted", "independent-checks"),
                ("review-plan", "needs-work", "revise-plan"),
            ),
            flow.branches,
        )
        self.assertEqual(2, flow.steps[2].loop.max_attempts)
        subagent = flow.steps[3].payload[0]
        self.assertEqual("subagent", subagent.kind)
        self.assertEqual("analyze-scope", subagent.payload[0].name)
        self.assertEqual(("--strict", "one argument"), flow.steps[4].arguments)
        self.assertTrue(flow.identity.startswith("usw-flow-v2:"))

    def test_rejects_invalid_structured_contracts(self):
        valid = self.structured_content()
        invalid = {
            "model": valid.replace("CALL FLOW `review-flow`", "CALL MODEL `gpt`"),
            "duplicate name": valid.replace("`final-review`", "`prepare-plan`"),
            "missing payload": valid.replace(
                "     - Действия субагента:\n"
                "       1. `analyze-scope` — CALL SKILL `usw-brainstorm-solutions`.\n",
                "",
            ),
            "incomplete gate": valid.replace(
                "   - ELIF `needs-work`: продолжить LOOP `revise-plan`.\n", ""
            ),
            "unbounded loop": valid.replace("не более 2 попыток", "без ограничений"),
            "single parallel child": valid.replace(
                "   - `check-safety` — CALL HUMAN `security-reviewer`.\n", ""
            ),
            "unknown target": valid.replace(
                "продолжить к `independent-checks`",
                "продолжить к `missing-action`",
            ),
        }
        for label, content in invalid.items():
            with self.subTest(label=label), self.assertRaises(CUSTOM.CustomFlowError):
                CUSTOM.parse_custom_flow(content, "prepare-and-review")

    def test_local_origin_is_distinct_and_rejects_standard_flows(self):
        shared = CUSTOM.parse_custom_flow(self.content(), "plan-check")
        local = CUSTOM.parse_custom_flow(
            self.content(), "plan-check", origin="local"
        )

        self.assertEqual("local", local.origin)
        self.assertNotEqual(shared.identity, local.identity)
        with self.assertRaisesRegex(
            CUSTOM.CustomFlowError, "unsupported_local_standard_flow"
        ):
            CUSTOM.parse_custom_flow(self.content(), "analysis", origin="local")

    def test_rejects_invalid_contract_before_execution(self):
        invalid = {
            "missing section": self.content().replace("## Контракт", "## Other"),
            "unknown version": self.content().replace("- Версия: `1`", "- Версия: `2`"),
            "branch": self.content() + "\n## Branches\n\n- `1:ok` -> `2`\n",
            "step gap": self.content().replace("2. Скрипт", "3. Скрипт"),
            "unknown step": self.content().replace("1. Скилл", "1. Команда"),
            "excess writes": self.content().replace("- Пишет: нет", "- Пишет: `implementation`"),
            "partial write contract": self.concise_content().replace(
                "2. Скрипт:", "   - Пишет: нет\n2. Скрипт:"
            ),
        }
        for label, content in invalid.items():
            with self.subTest(label=label), self.assertRaises(CUSTOM.CustomFlowError):
                CUSTOM.parse_custom_flow(content, "plan-check")

    def test_loads_safe_name_and_rejects_paths_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            flow_root = Path(directory)
            (flow_root / "plan-check.md").write_text(self.content(), encoding="utf-8")
            self.assertEqual("plan-check", CUSTOM.load_custom_flow(flow_root, "plan-check").name)

            for name in ("../outside", "/outside", "Plan Check"):
                with self.subTest(name=name), self.assertRaisesRegex(
                    CUSTOM.CustomFlowError, "invalid_flow_name"
                ):
                    CUSTOM.load_custom_flow(flow_root, name)

            (flow_root / "linked.md").symlink_to(flow_root / "plan-check.md")
            with self.assertRaisesRegex(CUSTOM.CustomFlowError, "invalid_flow_file"):
                CUSTOM.load_custom_flow(flow_root, "linked")

    def test_default_markdown_run_accepts_plain_content_and_prefers_local(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            local_root = project / ".usw/flows"
            shared_root = project / "usw/flows"
            local_root.mkdir(parents=True)
            shared_root.mkdir(parents=True)
            local_path = local_root / "review-anything.md"
            shared_path = shared_root / "review-anything.md"
            local_path.write_text("# Local\n\nDo the task in two useful steps.\n", encoding="utf-8")
            shared_path.write_text(
                "# Shared\n\n- Версия: `unknown`\n\nNo strict schema here.\n",
                encoding="utf-8",
            )
            before = local_path.read_bytes()

            invocation = CUSTOM.prepare_markdown_run(
                project,
                shared_root,
                "review-anything",
                "Review the current change",
            )
            seen = []
            outcome = CUSTOM.run_markdown_flow(
                invocation,
                lambda value: seen.append(value)
                or CUSTOM.ActionOutcome("completed", "done"),
            )
            shared = CUSTOM.resolve_markdown_flow(
                project, shared_root, "review-anything", origin="shared"
            )
            after = local_path.read_bytes()

        self.assertEqual("local", invocation.flow.origin)
        self.assertEqual("shared", shared.origin)
        self.assertEqual("Review the current change", invocation.task)
        self.assertEqual("completed", outcome.status)
        self.assertEqual([invocation], seen)
        self.assertEqual(before, after)

    def test_default_markdown_cli_does_not_enable_strict_parser(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            shared_root = project / "flows"
            shared_root.mkdir()
            (shared_root / "free-form.md").write_text(
                "# Anything\n\n- Версия: `version-2`\n\nThis is not the strict contract.\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CUSTOM_SCRIPT),
                    "resolve",
                    str(project),
                    str(shared_root),
                    "free-form",
                    "Do the task",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(completed.stdout)
            strict = subprocess.run(
                [
                    sys.executable,
                    str(CUSTOM_SCRIPT),
                    "validate",
                    str(shared_root),
                    "free-form",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual("shared", report["origin"])
        self.assertEqual("Do the task", report["task"])
        self.assertEqual(2, strict.returncode)
        self.assertEqual(
            "experimental_opt_in_required", json.loads(strict.stderr)["error"]
        )

    def test_default_markdown_rejects_symlinked_root(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            real_root = project / "real-flows"
            real_root.mkdir()
            (real_root / "unsafe.md").write_text("# Flow\n", encoding="utf-8")
            linked_root = project / "linked-flows"
            linked_root.symlink_to(real_root, target_is_directory=True)

            with self.assertRaisesRegex(
                CUSTOM.CustomFlowError, "invalid_flow_root"
            ):
                CUSTOM.resolve_markdown_flow(
                    project,
                    linked_root,
                    "unsafe",
                    origin="shared",
                )

    def test_resolves_only_safe_local_flow_root(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".usw").mkdir()
            flow_root = CUSTOM.local_custom_flow_root(project, create=True)
            self.assertEqual(project.resolve() / ".usw/flows", flow_root)
            self.assertTrue(flow_root.is_dir())

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            outside = project / "outside"
            outside.mkdir()
            (project / ".usw").symlink_to(outside)
            with self.assertRaisesRegex(CUSTOM.CustomFlowError, "invalid_local_state"):
                CUSTOM.local_custom_flow_root(project)

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            outside = project / "outside"
            outside.mkdir()
            (project / ".usw").mkdir()
            (project / ".usw/flows").symlink_to(outside)
            with self.assertRaisesRegex(
                CUSTOM.CustomFlowError, "invalid_local_flow_root"
            ):
                CUSTOM.local_custom_flow_root(project)

    def test_validation_cli_returns_structured_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            flow_root = Path(directory)
            (flow_root / "plan-check.md").write_text(self.content(), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CUSTOM_SCRIPT),
                    "validate",
                    "--experimental-structured",
                    str(flow_root),
                    "plan-check",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(completed.stdout)
            self.assertEqual("plan-check", report["name"])
            self.assertEqual("shared", report["origin"])
            self.assertEqual(["skill", "script"], [step["kind"] for step in report["steps"]])

    def test_validation_cli_reports_version_2_control_and_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            flow_root = Path(directory)
            (flow_root / "prepare-and-review.md").write_text(
                self.structured_content(), encoding="utf-8"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CUSTOM_SCRIPT),
                    "validate",
                    "--experimental-structured",
                    str(flow_root),
                    "prepare-and-review",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(completed.stdout)

        self.assertEqual("version-2", report["version"])
        self.assertEqual("prepare-plan", report["steps"][0]["name"])
        self.assertEqual("accepted", report["branches"][0][1])
        self.assertEqual(
            "analyze-scope",
            report["steps"][3]["payload"][0]["payload"][0]["name"],
        )
        self.assertEqual(2, report["steps"][2]["loop"]["max_attempts"])

    def test_validation_cli_local_aliases_select_dot_usw(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            flow_root = project / ".usw/flows"
            flow_root.mkdir(parents=True)
            (flow_root / "plan-check.md").write_text(
                self.content(), encoding="utf-8"
            )

            identities = set()
            for flag in ("--local", "-l"):
                with self.subTest(flag=flag):
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(CUSTOM_SCRIPT),
                            "validate",
                            "--experimental-structured",
                            flag,
                            str(project),
                            "plan-check",
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    report = json.loads(completed.stdout)
                    self.assertEqual("local", report["origin"])
                    identities.add(report["identity"])
            self.assertEqual(1, len(identities))


if __name__ == "__main__":
    unittest.main()
