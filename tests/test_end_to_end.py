import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load(name, relative):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


INIT = load("e2e_init", "skills/usw-initialize-project/scripts/init_usw.py")
HANDOFF = load("e2e_handoff", "skills/usw-manage-handoff/scripts/handoff_state.py")
ARTIFACTS = load("e2e_artifacts", "skills/usw-initialize-project/scripts/artifact_contract.py")
FLOWS = load("e2e_flows", "skills/usw-initialize-project/scripts/flow_scenario.py")
RUNNER = load("e2e_runner", "skills/usw-run-flow/scripts/run_flow.py")


class EndToEndWorkflowTests(unittest.TestCase):
    def git(self, project, *args):
        return subprocess.run(
            ["git", "-C", str(project), *args], check=True,
            capture_output=True, text=True,
        )

    def initialize_git(self, project):
        self.git(project, "init", "--quiet")
        self.git(project, "config", "user.name", "USW E2E")
        self.git(project, "config", "user.email", "usw@example.invalid")
        INIT.initialize_usw(project)
        (project / "product.txt").write_text("v1\n", encoding="utf-8")
        self.git(project, "add", "product.txt")
        self.git(project, "commit", "--quiet", "-m", "product")

    def active_checkpoint(self):
        return (
            "# Developer Handoff\n\n"
            "| Subject | Role | Attempt | Current operation | Status | Updated |\n"
            "|---|---|---|---|---|---|\n"
            "| task/example/1.1 | Development | 1 | implement | paused | 2026-07-21T12:00:00+03:00 |\n\n"
            "## Session journal\n\n"
            "| Event | Operation | Status | Fact | Changed areas |\n"
            "|---|---|---|---|---|\n"
            "| interrupted | implement | paused | partial implementation | `product.txt` |\n\n"
            "## Verification\n\n"
            "| Check | Result | Observation |\n|---|---|---|\n"
            "| unit test | not-run | source changed |\n\n"
            "## Next action\n\nRun the focused unit test.\n\n"
            "## References\n\n- `task/example/1.1`\n\n"
            "## Trusted source snapshot\n\n- Identity: none\n- Freshness: unknown\n"
        )

    def test_clean_init_interrupted_resume_and_workflow_only_freshness(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize_git(project)
            _, initial, status = HANDOFF.read_handoff(project)
            self.assertEqual("idle", status)
            self.assertIn("| Subject | Role |", initial)
            candidate = project / ".usw/HANDOFF.next.md"
            candidate.write_text(self.active_checkpoint(), encoding="utf-8")
            HANDOFF.save_handoff(project, candidate)
            content, report = HANDOFF.reconcile_handoff(project)
            self.assertEqual("fresh", report.freshness)
            self.assertIn("usw-source-v1:", content)

            flow = project / "usw/flows/examples/analysis.md"
            flow.write_text(flow.read_text() + "\n<!-- local policy note -->\n")
            self.assertEqual("fresh", HANDOFF.reconcile_handoff(project)[1].freshness)
            (project / "product.txt").write_text("v2\n", encoding="utf-8")
            self.assertEqual("stale", HANDOFF.reconcile_handoff(project)[1].freshness)

    def test_review_retry_is_immutable_and_planning_change_invalidates_old_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            task = project / "task.md"
            task.write_text("legacy contract\n", encoding="utf-8")
            contract_identity = "sha256:" + hashlib.sha256(task.read_bytes()).hexdigest()
            review_root = project / "usw/reviews"
            first = ARTIFACTS.write_receipt(
                project, review_root, receipt_id="review-1", gate="transition",
                owner_role="Testing", subject="task/example/1.1",
                reviewed_scope="task", reviewer="human", verdict="rejected",
                artifacts=[task], artifact_model="legacy",
                contract_identity=contract_identity,
                evidence_references=["unit tests passed"], sender="Development",
                receiver="Testing", findings=["implementation defect"],
            )
            second = ARTIFACTS.write_receipt(
                project, review_root, receipt_id="review-2", gate="transition",
                owner_role="Testing", subject="task/example/1.1",
                reviewed_scope="task", reviewer="human", verdict="accepted",
                artifacts=[task], artifact_model="legacy",
                contract_identity=contract_identity,
                evidence_references=["unit tests rerun and passed"], sender="Development",
                receiver="Testing", previous="review-1",
            )
            self.assertTrue(first.is_file() and second.is_file())
            self.assertNotIn("Product source identity", first.read_text())
            self.assertTrue(ARTIFACTS.receipt_is_current(project, second))
            task.write_text("changed planning contract\n", encoding="utf-8")
            self.assertFalse(ARTIFACTS.receipt_is_current(project, second))

    def test_scope_authority_and_delivery_permission_boundaries(self):
        scenario = FLOWS.validate_scenario(
            (ROOT / "tests/fixtures/flow-scenarios/flow-scenario-development.md").read_text()
        )
        called = []

        def invoke(scope):
            called.append(scope)
            return RUNNER.ActionOutcome("completed", "ok")

        executor = RUNNER.Executor(frozenset(), invoke)
        ambiguous = RUNNER.run_next(
            scenario, RUNNER.FlowState(), {"check-inputs": executor},
            allowed_scopes=("step/1", "task/1.1"),
        )
        self.assertEqual("scope_required", ambiguous.stop_reason)
        self.assertEqual([], called)
        denied = RUNNER.authorize_external_action(
            delivery_reached=True, action="push", explicit_permissions=frozenset()
        )
        self.assertEqual("external_permission_required", denied.stop_reason)

    def test_custom_flow_orders_skill_script_resume_and_preserves_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            INIT.initialize_usw(project)
            example_path = project / "usw/flows/examples/analysis.md"
            example_before = example_path.read_bytes()
            script = project / "scripts/check.py"
            script.parent.mkdir()
            script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            script.chmod(0o755)
            custom_path = project / "usw/flows/plan-check.md"
            custom_path.write_text(
                """# Flow: plan-check

## Контракт

- Версия: `1`

## Порядок действий

1. Скилл: `first-skill`
   - Пишет: нет
2. Скрипт: `scripts/check.py`
   - Аргументы: `--strict`
   - Пишет: нет
3. Скилл: `last-skill`
   - Пишет: нет

## Полномочия записи

- Нет.
""",
                encoding="utf-8",
            )
            flow = RUNNER.load_custom_flow(project / "usw/flows", "plan-check")
            calls = []

            def skill(label):
                def invoke(_scope):
                    calls.append(label)
                    return RUNNER.ActionOutcome("completed", "ok")

                return RUNNER.Executor(frozenset(), invoke)

            script_results = iter((1, 0))

            def run_script(argv, **_kwargs):
                calls.append("script")
                return subprocess.CompletedProcess(argv, next(script_results), "", "failed")

            executors = {
                "first-skill": skill("first"),
                "last-skill": skill("last"),
            }
            state = RUNNER.FlowState()
            first = RUNNER.run_custom_next(
                flow,
                state,
                executors,
                project_root=project,
                allowed_scopes=("task/x",),
                script_permissions=frozenset({"scripts/check.py"}),
                script_runner=run_script,
            )
            RUNNER.save_custom_checkpoint(
                project, flow, first.state, source_identity="source-1"
            )
            resumed = RUNNER.resume_custom_state(
                flow,
                RUNNER.load_custom_checkpoint(project),
                current_source_identity="source-1",
            )
            failed = RUNNER.run_custom_next(
                flow,
                resumed,
                executors,
                project_root=project,
                allowed_scopes=("task/x",),
                script_permissions=frozenset({"scripts/check.py"}),
                script_runner=run_script,
            )
            self.assertEqual(["first", "script"], calls)
            self.assertEqual("failed", failed.status)

            RUNNER.save_custom_checkpoint(
                project, flow, failed.state, source_identity="source-1"
            )
            resumed = RUNNER.resume_custom_state(
                flow,
                RUNNER.load_custom_checkpoint(project),
                current_source_identity="source-1",
            )
            script_passed = RUNNER.run_custom_next(
                flow,
                resumed,
                executors,
                project_root=project,
                allowed_scopes=("task/x",),
                script_permissions=frozenset({"scripts/check.py"}),
                script_runner=run_script,
            )
            last = RUNNER.run_custom_next(
                flow,
                script_passed.state,
                executors,
                project_root=project,
                allowed_scopes=("task/x",),
                script_permissions=frozenset({"scripts/check.py"}),
                script_runner=run_script,
            )
            self.assertEqual(["first", "script", "script", "last"], calls)
            self.assertEqual(3, last.state.action_index)
            self.assertEqual(example_before, example_path.read_bytes())
            self.assertIn("Ненормативный пример", example_path.read_text())

    def test_local_and_shared_custom_flows_keep_distinct_resume_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            INIT.initialize_usw(project)
            content = """# Flow: personal-check

## Контракт

- Версия: `1`

## Порядок действий

1. Скилл: `first-skill`
   - Пишет: нет

## Полномочия записи

- Нет.
"""
            shared_root = project / "usw/flows"
            local_root = RUNNER.local_custom_flow_root(project, create=True)
            for root in (shared_root, local_root):
                (root / "personal-check.md").write_text(content, encoding="utf-8")

            shared = RUNNER.load_custom_flow(shared_root, "personal-check")
            local = RUNNER.load_custom_flow(
                local_root, "personal-check", origin="local"
            )
            self.assertNotEqual(shared.identity, local.identity)

            RUNNER.save_custom_checkpoint(
                project,
                shared,
                RUNNER.FlowState(0, "task/x", False),
                source_identity=None,
            )
            with self.assertRaisesRegex(RUNNER.CustomFlowError, "stale_flow"):
                RUNNER.resume_custom_state(
                    local,
                    RUNNER.load_custom_checkpoint(project),
                    current_source_identity=None,
                )

    def test_package_manifests_all_describe_standalone_default(self):
        descriptions = []
        for path in (".codex-plugin/plugin.json", "qwen-extension.json", "gigacode-extension.json"):
            descriptions.append(json.loads((ROOT / path).read_text())["description"])
        self.assertTrue(all("standalone" in value.lower() for value in descriptions))


if __name__ == "__main__":
    unittest.main()
