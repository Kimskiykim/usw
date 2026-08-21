import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
RUNNER_PATH = ROOT / "skills/usw-run-flow/scripts/run_flow.py"
RUNNER_SPEC = importlib.util.spec_from_file_location(
    "scenario_text_flow_runner", RUNNER_PATH
)
RUNNER = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC.loader is not None
sys.modules[RUNNER_SPEC.name] = RUNNER
RUNNER_SPEC.loader.exec_module(RUNNER)


class TextFlowContractTests(unittest.TestCase):
    def test_nested_results_stay_root_bound_and_preserve_status(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            shared = project / "usw/flows"
            shared.mkdir(parents=True)
            for name in ("root", "frontend", "backend"):
                (shared / f"{name}.md").write_text(
                    f"{name}\n", encoding="utf-8"
                )
            root = RUNNER.bind_root_execution(
                RUNNER.prepare_markdown_run(
                    project, shared, "root", "coordinate"
                ),
                handoff_enabled=True,
                operation="usw-operation:" + "1" * 64,
            )
            children = [
                RUNNER.prepare_nested_run(
                    project,
                    shared,
                    name,
                    f"{name} input",
                    parent=root.context,
                    branch_label=name,
                    assert_current=lambda *_: None,
                )
                for name in ("frontend", "backend")
            ]
            results = (
                RUNNER.record_nested_result(
                    children[0],
                    status="completed",
                    factual_result="Frontend complete.",
                    checks=("frontend tests passed",),
                ),
                RUNNER.record_nested_result(
                    children[1],
                    status="decision_required",
                    factual_result="Backend reached a permission boundary.",
                    blocker="Deployment permission is required.",
                    next_action="Ask the user for permission.",
                ),
            )

            aggregate = RUNNER.collect_nested_results(
                root.context, results
            )

            self.assertEqual(results, aggregate.results)
            self.assertEqual(
                ("decision_required",), aggregate.unresolved_statuses
            )
            self.assertFalse(aggregate.automatic_retry)

            other_root = RUNNER.bind_root_execution(
                root.invocation,
                handoff_enabled=True,
                operation="usw-operation:" + "2" * 64,
            )
            with self.assertRaisesRegex(
                RUNNER.FlowError, "another root"
            ):
                RUNNER.collect_nested_results(
                    other_root.context, results
                )

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
            {"recipes.md", "version-2.md"},
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
        structured = (
            ROOT / "skills/usw-create-flow/references/version-2.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`markdown`", run)
        self.assertIn("`assert-current`", run)
        self.assertIn("`version-2`", create)
        self.assertIn("version-2", structured)
        self.assertNotIn("--experimental-structured", create)

    def test_examples_are_isolated_text_flows(self):
        examples = ROOT / "skills/usw-initialize-project/templates/flows/examples"
        self.assertEqual(
            {
                "chat-review.md",
                "dev-test.md",
                "plan-small-steps.md",
                "refine-intent.md",
            },
            {path.name for path in examples.glob("*.md")},
        )
        for path in examples.glob("*.md"):
            content = path.read_text(encoding="utf-8")
            self.assertIn("# Flow:", content)
            self.assertNotIn("--experimental-structured", content)

    def test_chat_review_declares_adaptive_quorum_contract(self):
        content = (ROOT / "usw/flows/chat-review.md").read_text(encoding="utf-8")
        required = (
            "--reviewers auto|2|3",
            "Review profile: llm-critic | custom",
            "CALL COMMAND `/usw-reviewer-llm-critic`",
            "выполняет ровно одно read-only discovery review",
            "Неизвестный profile",
            "Scope отсутствует или пуст",
            "high-impact trigger",
            "uncertainty factors",
            "support",
            "reject",
            "abstain",
            "1:1",
            "reviewer-c",
            "Не запускать четвёртого reviewer-а",
            "voting-specific `Scope`, `Review focus` и `Output contract`",
            "возобновить flow сразу с `GATE finding-decisions`",
            "fix-finding",
            "reject-finding",
            "не считать голосом\n`reject`",
            "evidence, vote provenance и human decision",
            "отдельного implementation flow",
        )

        for fragment in required:
            self.assertIn(fragment, content)

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
