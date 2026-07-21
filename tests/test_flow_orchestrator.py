import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FLOWS = load("orchestrator_flow_scenario", ROOT / "skills/usw-initialize-project/scripts/flow_scenario.py")
RUNNER = load("run_flow", ROOT / "skills/usw-run-flow/scripts/run_flow.py")
TEMPLATES = ROOT / "skills/usw-initialize-project/templates/flows"


class FlowOrchestratorTests(unittest.TestCase):
    def scenario(self, name: str = "analysis"):
        return FLOWS.validate_scenario(
            (TEMPLATES / f"flow-scenario-{name}.md").read_text(encoding="utf-8")
        )

    def executor(self, writes=(), *, outcome="ok", status="completed", calls=None, stub=False):
        def invoke(scope):
            if calls is not None:
                calls.append(scope)
            return RUNNER.ActionOutcome(status, outcome, frozenset(writes), ("artifact.md",))

        return RUNNER.Executor(frozenset(writes), invoke, True, stub)

    def custom(self, actions: str, authority: str = "- Нет."):
        return RUNNER.parse_custom_flow(
            f"""# Flow: custom-check

## Контракт

- Версия: `1`

## Порядок действий

{actions}

## Полномочия записи

{authority}
""",
            "custom-check",
        )

    def test_runs_exactly_one_atomic_action_and_returns_control(self):
        scenario = self.scenario()
        calls = []
        result = RUNNER.run_next(
            scenario,
            RUNNER.FlowState(),
            {"check-inputs": self.executor(calls=calls)},
            allowed_scopes=("change/example",),
        )

        self.assertEqual(["change/example"], calls)
        self.assertEqual("action_completed", result.status)
        self.assertEqual("check-inputs", result.action)
        self.assertEqual(1, result.state.action_index)

    def test_ambiguous_scope_stops_before_executor(self):
        calls = []
        result = RUNNER.run_next(
            self.scenario(),
            RUNNER.FlowState(),
            {"check-inputs": self.executor(calls=calls)},
            allowed_scopes=("step/1", "task/1.1"),
        )
        self.assertEqual("decision_required", result.status)
        self.assertEqual("scope_required", result.stop_reason)
        self.assertIn("step/1", result.next_action)
        self.assertEqual([], calls)

    def test_missing_executor_and_stub_stop_before_mutation(self):
        scenario = self.scenario()
        missing = RUNNER.run_next(
            scenario, RUNNER.FlowState(), {}, allowed_scopes=("change/x",)
        )
        self.assertEqual("missing_executor", missing.stop_reason)

        calls = []
        stub = RUNNER.run_next(
            scenario,
            RUNNER.FlowState(),
            {"check-inputs": self.executor(calls=calls, stub=True)},
            allowed_scopes=("change/x",),
        )
        self.assertEqual("missing_executor", stub.stop_reason)
        self.assertEqual([], calls)

    def test_contract_compatible_stub_can_drive_sequencing_test(self):
        calls = []
        result = RUNNER.run_next(
            self.scenario(),
            RUNNER.FlowState(),
            {"check-inputs": self.executor(calls=calls, stub=True)},
            allowed_scopes=("change/x",),
            allow_stubs=True,
        )
        self.assertEqual("action_completed", result.status)
        self.assertEqual(["change/x"], calls)

    def test_write_authority_is_checked_before_invocation(self):
        calls = []
        result = RUNNER.run_next(
            self.scenario(),
            RUNNER.FlowState(),
            {"check-inputs": self.executor(("implementation",), calls=calls)},
            allowed_scopes=("change/x",),
        )
        self.assertEqual("authority_mismatch", result.stop_reason)
        self.assertEqual([], calls)

    def test_reported_writes_are_checked_after_invocation(self):
        result = RUNNER.run_next(
            self.scenario(),
            RUNNER.FlowState(),
            {
                "check-inputs": RUNNER.Executor(
                    frozenset(),
                    lambda _scope: RUNNER.ActionOutcome(
                        "completed", "ok", frozenset({"implementation"})
                    ),
                )
            },
            allowed_scopes=("change/x",),
        )
        self.assertEqual("failed", result.status)
        self.assertEqual("executor_contract_violation", result.stop_reason)

    def test_branching_to_repair_and_stop_is_deterministic(self):
        scenario = self.scenario("development")
        review_index = scenario.actions.index("internal-review")
        rejected = RUNNER.run_next(
            scenario,
            RUNNER.FlowState(review_index, "task/1.1"),
            {"internal-review": self.executor(("review-receipt",), outcome="rejected")},
            allowed_scopes=("task/1.1",),
        )
        self.assertEqual(scenario.actions.index("execute-bounded-scope"), rejected.state.action_index)

        transition_index = scenario.actions.index("transition-review-testing")
        accepted = RUNNER.run_next(
            scenario,
            RUNNER.FlowState(transition_index, "task/1.1"),
            {"transition-review-testing": self.executor(("review-receipt",), outcome="accepted")},
            allowed_scopes=("task/1.1",),
        )
        self.assertEqual("scope-complete", accepted.stop_reason)
        self.assertTrue(accepted.state.stopped)

    def test_blocker_returns_observable_reason_and_next_action(self):
        result = RUNNER.run_next(
            self.scenario(),
            RUNNER.FlowState(),
            {"check-inputs": self.executor(outcome="invalid-artifact-state", status="blocked")},
            allowed_scopes=("change/x",),
        )
        self.assertEqual("blocked", result.status)
        self.assertEqual("invalid-artifact-state", result.stop_reason)
        self.assertTrue(result.next_action)

    def test_custom_skills_resolve_by_exact_name_and_run_linearly(self):
        flow = self.custom(
            "1. Скилл: `first-skill`\n"
            "   - Пишет: нет\n"
            "2. Скилл: `second-skill`\n"
            "   - Пишет: нет"
        )
        calls = []
        skills = {
            "first-skill": self.executor(calls=calls),
            "second-skill": self.executor(calls=calls),
        }
        with tempfile.TemporaryDirectory() as directory:
            first = RUNNER.run_custom_next(
                flow,
                RUNNER.FlowState(),
                skills,
                project_root=Path(directory),
                allowed_scopes=("task/x",),
            )
            second = RUNNER.run_custom_next(
                flow,
                first.state,
                skills,
                project_root=Path(directory),
                allowed_scopes=("task/x",),
            )
        self.assertEqual(["task/x", "task/x"], calls)
        self.assertEqual(2, second.state.action_index)

    def test_custom_skill_contract_is_validated_before_any_call(self):
        flow = self.custom(
            "1. Скилл: `first-skill`\n"
            "   - Пишет: нет\n"
            "2. Скилл: `missing-skill`\n"
            "   - Пишет: нет"
        )
        calls = []
        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(
            RUNNER.CustomFlowError, "missing_skill"
        ):
            RUNNER.run_custom_next(
                flow,
                RUNNER.FlowState(),
                {"first-skill": self.executor(calls=calls)},
                project_root=Path(directory),
                allowed_scopes=("task/x",),
            )
        self.assertEqual([], calls)

    def test_script_requires_permission_and_uses_argv_without_shell(self):
        flow = self.custom(
            "1. Скрипт: `scripts/check.py`\n"
            "   - Аргументы: `--quick` `one argument`\n"
            "   - Пишет: нет"
        )
        calls = []

        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            return RUNNER.subprocess.CompletedProcess(argv, 0, "ok", "")

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            script = project / "scripts/check.py"
            script.parent.mkdir()
            script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            script.chmod(0o755)
            denied = RUNNER.run_custom_next(
                flow,
                RUNNER.FlowState(),
                {},
                project_root=project,
                allowed_scopes=("task/x",),
                script_runner=runner,
            )
            allowed = RUNNER.run_custom_next(
                flow,
                RUNNER.FlowState(),
                {},
                project_root=project,
                allowed_scopes=("task/x",),
                script_permissions=frozenset({"scripts/check.py"}),
                script_runner=runner,
            )
        self.assertEqual("permission_required", denied.status)
        self.assertEqual("action_completed", allowed.status)
        self.assertEqual(1, len(calls))
        argv, kwargs = calls[0]
        self.assertEqual([str(script.resolve()), "--quick", "one argument"], argv)
        self.assertNotIn("shell", kwargs)

    def test_script_rejects_traversal_symlink_and_command_string(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            target = project / "check.py"
            target.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            target.chmod(0o755)
            (project / "linked.py").symlink_to(target)
            for value in ("../check.py", "linked.py", "check.py;echo"):
                flow = self.custom(
                    f"1. Скрипт: `{value}`\n"
                    "   - Пишет: нет"
                )
                with self.subTest(value=value), self.assertRaises(RUNNER.CustomFlowError):
                    RUNNER.resolve_custom_executors(flow, {}, project_root=project)

    def test_custom_failure_stops_before_following_step(self):
        flow = self.custom(
            "1. Скилл: `first-skill`\n"
            "   - Пишет: нет\n"
            "2. Скилл: `second-skill`\n"
            "   - Пишет: нет"
        )
        calls = []
        skills = {
            "first-skill": self.executor(status="failed", outcome="failed", calls=calls),
            "second-skill": self.executor(calls=calls),
        }
        with tempfile.TemporaryDirectory() as directory:
            failed = RUNNER.run_custom_next(
                flow,
                RUNNER.FlowState(),
                skills,
                project_root=Path(directory),
                allowed_scopes=("task/x",),
            )
            stopped = RUNNER.run_custom_next(
                flow,
                failed.state,
                skills,
                project_root=Path(directory),
                allowed_scopes=("task/x",),
            )
        self.assertEqual("failed", failed.status)
        self.assertEqual("flow_already_stopped", stopped.stop_reason)
        self.assertEqual(["task/x"], calls)

    def test_custom_checkpoint_round_trip_and_fresh_resume(self):
        flow = self.custom(
            "1. Скилл: `first-skill`\n"
            "   - Пишет: нет\n"
            "2. Скилл: `second-skill`\n"
            "   - Пишет: нет"
        )
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".usw").mkdir()
            path = RUNNER.save_custom_checkpoint(
                project,
                flow,
                RUNNER.FlowState(1, "task/x", True),
                source_identity="source-1",
            )
            checkpoint = RUNNER.load_custom_checkpoint(project)
            resumed = RUNNER.resume_custom_state(
                flow, checkpoint, current_source_identity="source-1"
            )
            self.assertEqual(project / ".usw/FLOW.json", path)
            self.assertEqual(RUNNER.FlowState(1, "task/x", False), resumed)
            self.assertEqual(0o600, path.stat().st_mode & 0o777)

    def test_custom_resume_rejects_changed_flow_or_source(self):
        flow = self.custom(
            "1. Скилл: `first-skill`\n"
            "   - Пишет: нет"
        )
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".usw").mkdir()
            RUNNER.save_custom_checkpoint(
                project,
                flow,
                RUNNER.FlowState(0, "task/x", True),
                source_identity="source-1",
            )
            checkpoint = RUNNER.load_custom_checkpoint(project)
            changed_flow = self.custom(
                "1. Скилл: `other-skill`\n"
                "   - Пишет: нет"
            )
            with self.assertRaisesRegex(RUNNER.CustomFlowError, "stale_flow"):
                RUNNER.resume_custom_state(
                    changed_flow, checkpoint, current_source_identity="source-1"
                )
            with self.assertRaisesRegex(RUNNER.CustomFlowError, "stale_source_context"):
                RUNNER.resume_custom_state(
                    flow, checkpoint, current_source_identity="source-2"
                )
            with self.assertRaisesRegex(RUNNER.CustomFlowError, "unknown_source_context"):
                RUNNER.resume_custom_state(
                    flow, checkpoint, current_source_identity=None
                )

    def test_delivery_does_not_authorize_external_actions(self):
        denied = RUNNER.authorize_external_action(
            delivery_reached=True,
            action="push",
            explicit_permissions=frozenset(),
        )
        self.assertEqual("permission_required", denied.status)
        self.assertEqual("external_permission_required", denied.stop_reason)

        allowed = RUNNER.authorize_external_action(
            delivery_reached=True,
            action="push",
            explicit_permissions=frozenset({"push"}),
        )
        self.assertEqual("authorized", allowed.status)


if __name__ == "__main__":
    unittest.main()
