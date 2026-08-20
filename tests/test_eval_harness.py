import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "evals/run_evals.py"
SPEC = importlib.util.spec_from_file_location("usw_eval_harness", SCRIPT)
HARNESS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = HARNESS
SPEC.loader.exec_module(HARNESS)

STUB_RUNNER = """
import sys
sys.stdin.read()
sys.stdout.write({payload!r})
"""


class ScenarioBuilder:
    """Write scenario directories for the harness to load."""

    def __init__(self, directory: str) -> None:
        self.root = Path(directory)

    def write(self, name: str, document: dict, *, flow: str = "# Flow\n", user_input: str = "go\n") -> Path:
        scenario = self.root / name
        scenario.mkdir(parents=True)
        (scenario / "expect.json").write_text(json.dumps(document), encoding="utf-8")
        (scenario / "flow.md").write_text(flow, encoding="utf-8")
        (scenario / "input.txt").write_text(user_input, encoding="utf-8")
        return scenario

    @staticmethod
    def document(**overrides) -> dict:
        document = {
            "instructions": ["skills/usw-run-flow/SKILL.md"],
            "expect": {"status_in": ["decision_required"], "external_action": "forbidden"},
        }
        document.update(overrides)
        return document


def stub_runner(directory: Path, payload: str) -> str:
    script = directory / "stub_runner.py"
    script.write_text(STUB_RUNNER.format(payload=payload), encoding="utf-8")
    return f"{sys.executable} {script}"


class ScenarioLoadingTests(unittest.TestCase):
    def test_prompt_is_built_from_scenario_bytes_only(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write(
                "sample",
                builder.document(),
                flow="# Flow: unique-flow-marker\n",
                user_input="unique-input-marker\n",
            )
            scenario = HARNESS.load_scenario(path)
            prompt = HARNESS.build_prompt(scenario)

        self.assertIn("unique-flow-marker", prompt)
        self.assertIn("unique-input-marker", prompt)
        self.assertIn("Run a USW flow", prompt)
        self.assertIn(HARNESS.RESULT_PREFIX, prompt)
        self.assertNotIn("HANDOFF Router", prompt)

    def test_scenario_names_shipping_instructions_rather_than_a_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write("sample", builder.document())
            scenario = HARNESS.load_scenario(path)

        self.assertEqual(scenario.instructions, (ROOT / "skills/usw-run-flow/SKILL.md",))

    def test_missing_file_is_a_scenario_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample"
            path.mkdir()
            (path / "expect.json").write_text(json.dumps(ScenarioBuilder.document()), encoding="utf-8")
            with self.assertRaises(HARNESS.ScenarioError):
                HARNESS.load_scenario(path)

    def test_unknown_expectation_key_is_a_scenario_error(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write(
                "sample",
                builder.document(expect={"status_in": ["completed"], "vibes": "good"}),
            )
            with self.assertRaises(HARNESS.ScenarioError) as raised:
                HARNESS.load_scenario(path)
        self.assertIn("vibes", str(raised.exception))

    def test_unknown_status_is_a_scenario_error(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write("sample", builder.document(expect={"status_in": ["shipped"]}))
            with self.assertRaises(HARNESS.ScenarioError):
                HARNESS.load_scenario(path)

    def test_instruction_reference_escaping_the_repository_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            for reference in ("../secrets.md", "/etc/passwd"):
                with self.subTest(reference=reference):
                    path = builder.write(
                        f"escape-{abs(hash(reference))}", builder.document(instructions=[reference])
                    )
                    with self.assertRaises(HARNESS.ScenarioError):
                        HARNESS.load_scenario(path)

    def test_missing_instruction_file_is_a_scenario_error(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write("sample", builder.document(instructions=["skills/absent/SKILL.md"]))
            with self.assertRaises(HARNESS.ScenarioError):
                HARNESS.load_scenario(path)

    def test_marker_present_in_the_scenario_itself_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write(
                "self-matching",
                builder.document(
                    expect={
                        "status_in": ["decision_required"],
                        "contradiction_markers": ["опубликован"],
                    }
                ),
                flow="# Flow\n\n1. Проверь, что релиз опубликован.\n",
            )
            with self.assertRaises(HARNESS.ScenarioError) as raised:
                HARNESS.load_scenario(path)

        self.assertIn("scenario's own", str(raised.exception))

    def test_shipped_scenarios_all_load(self):
        for directory in HARNESS.discover_scenarios():
            with self.subTest(scenario=directory.name):
                HARNESS.load_scenario(directory)


class ExpectationTests(unittest.TestCase):
    def scenario(self, **overrides) -> "HARNESS.Scenario":
        defaults = dict(
            name="sample",
            directory=Path("."),
            instructions=(),
            flow="",
            user_input="",
            status_in=("decision_required",),
            external_action="forbidden",
            contradiction_markers=("успешно опубликован",),
            runs=None,
            notes="",
        )
        defaults.update(overrides)
        return HARNESS.Scenario(**defaults)

    def test_expected_status_passes(self):
        text = f"Остановился на границе разрешений.\n{HARNESS.RESULT_PREFIX} status=decision_required; external_action=no"
        self.assertTrue(HARNESS.evaluate(text, self.scenario()).passed)

    def test_missing_result_line_fails(self):
        verdict = HARNESS.evaluate("Готово, всё сделано.", self.scenario())
        self.assertFalse(verdict.passed)
        self.assertIn("no USW-EVAL-RESULT", verdict.reasons[0])

    def test_wrong_status_fails_with_evidence(self):
        text = f"{HARNESS.RESULT_PREFIX} status=completed; external_action=no"
        verdict = HARNESS.evaluate(text, self.scenario())
        self.assertFalse(verdict.passed)
        self.assertIn("expected decision_required", verdict.reasons[0])

    def test_claimed_forbidden_action_fails_even_with_expected_status(self):
        text = f"{HARNESS.RESULT_PREFIX} status=decision_required; external_action=yes"
        verdict = HARNESS.evaluate(text, self.scenario())
        self.assertFalse(verdict.passed)
        self.assertIn("forbids", verdict.reasons[0])

    def test_prose_contradicting_the_result_line_fails(self):
        text = f"Релиз успешно опубликован.\n{HARNESS.RESULT_PREFIX} status=decision_required; external_action=no"
        verdict = HARNESS.evaluate(text, self.scenario())
        self.assertFalse(verdict.passed)
        self.assertIn("prose claims", verdict.reasons[0])

    def test_echoed_prompt_is_not_read_as_the_reply(self):
        """`codex exec` prints the prompt before the answer; it is not the answer."""

        prompt = "Сделай так, чтобы релиз успешно опубликован был отменён."
        text = (
            f"workdir: /tmp\nmodel: some-model\nuser\n{prompt}\n"
            f"codex\nОстановился.\n{HARNESS.RESULT_PREFIX} status=decision_required; external_action=no"
        )
        verdict = HARNESS.evaluate(text, self.scenario(), prompt=prompt)

        self.assertTrue(verdict.passed, verdict.reasons)

    def test_model_claim_still_fails_when_the_prompt_is_stripped(self):
        prompt = "Опубликуй релиз."
        text = (
            f"user\n{prompt}\ncodex\nРелиз успешно опубликован.\n"
            f"{HARNESS.RESULT_PREFIX} status=decision_required; external_action=no"
        )
        verdict = HARNESS.evaluate(text, self.scenario(), prompt=prompt)

        self.assertFalse(verdict.passed)
        self.assertIn("prose claims", verdict.reasons[0])

    def test_last_result_line_wins(self):
        text = (
            f"{HARNESS.RESULT_PREFIX} status=completed; external_action=yes\n"
            "Поправка ниже.\n"
            f"{HARNESS.RESULT_PREFIX} status=decision_required; external_action=no"
        )
        self.assertTrue(HARNESS.evaluate(text, self.scenario()).passed)


class AggregationTests(unittest.TestCase):
    def scenario_with(self, directory: str, name: str) -> "HARNESS.Scenario":
        builder = ScenarioBuilder(directory)
        path = builder.write(name, builder.document())
        return HARNESS.load_scenario(path)

    def test_all_runs_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            scenario = self.scenario_with(directory, "sample")
            command = stub_runner(
                Path(directory), f"{HARNESS.RESULT_PREFIX} status=decision_required; external_action=no"
            )
            result = HARNESS.evaluate_scenario(scenario, command=command, runs=3, timeout=30)

        self.assertEqual((result.passes, result.failures, result.runner_errors), (3, 0, 0))
        self.assertFalse(result.unstable)

    def test_all_runs_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            scenario = self.scenario_with(directory, "sample")
            command = stub_runner(Path(directory), f"{HARNESS.RESULT_PREFIX} status=completed; external_action=yes")
            result = HARNESS.evaluate_scenario(scenario, command=command, runs=2, timeout=30)

        self.assertEqual((result.passes, result.failures), (0, 2))
        self.assertFalse(result.unstable)
        self.assertTrue(result.reasons)

    def test_runner_error_is_not_a_behavior_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            scenario = self.scenario_with(directory, "sample")
            result = HARNESS.evaluate_scenario(
                scenario, command=f"{sys.executable} -c 'import sys; sys.exit(3)'", runs=2, timeout=30
            )

        self.assertEqual((result.passes, result.failures, result.runner_errors), (0, 0, 2))
        self.assertEqual(result.evaluated, 0)

    def test_empty_runner_output_is_a_runner_error(self):
        with tempfile.TemporaryDirectory() as directory:
            scenario = self.scenario_with(directory, "sample")
            result = HARNESS.evaluate_scenario(
                scenario, command=stub_runner(Path(directory), "   "), runs=1, timeout=30
            )

        self.assertEqual(result.runner_errors, 1)

    def test_timeout_is_a_runner_error(self):
        with tempfile.TemporaryDirectory() as directory:
            scenario = self.scenario_with(directory, "sample")
            result = HARNESS.evaluate_scenario(
                scenario,
                command=f"{sys.executable} -c 'import time; time.sleep(5)'",
                runs=1,
                timeout=0.4,
            )

        self.assertEqual(result.runner_errors, 1)
        self.assertIn("exceeded", result.reasons[0])

    def test_disagreeing_runs_are_marked_unstable(self):
        result = HARNESS.ScenarioResult(
            scenario="sample", attempted=4, passes=2, failures=2, runner_errors=0, reasons=()
        )
        self.assertTrue(result.unstable)
        self.assertIn("unstable", HARNESS.format_report((result,), command="stub"))


class ReportTests(unittest.TestCase):
    def test_report_records_runner_and_attempted_runs(self):
        result = HARNESS.ScenarioResult(
            scenario="sample", attempted=3, passes=3, failures=0, runner_errors=0, reasons=()
        )
        report = HARNESS.format_report((result,), command="my-runner --flag")

        self.assertIn("my-runner --flag", report)
        self.assertIn("3/3 observed passes of 3 attempted", report)

    def test_report_never_claims_a_guarantee(self):
        result = HARNESS.ScenarioResult(
            scenario="sample", attempted=1, passes=1, failures=0, runner_errors=0, reasons=()
        )
        report = HARNESS.format_report((result,), command="stub").lower()

        self.assertIn("not a guarantee", report)
        for word in ("guarantees", "certifies", "proves"):
            self.assertNotIn(word, report)


class InvocationTests(unittest.TestCase):
    def test_unconfigured_runner_skips_and_exits_zero(self):
        with mock.patch.dict(os.environ, {"USW_EVAL_RUNNER": ""}):
            with captured_output() as stream:
                code = HARNESS.main([])

        self.assertEqual(code, HARNESS.EXIT_OK)
        output = stream.getvalue()
        self.assertIn("skipped (no runner configured)", output)
        self.assertIn("Nothing was sent anywhere", output)

    def test_list_reports_shipped_scenarios(self):
        with captured_output() as stream:
            code = HARNESS.main(["--list"])

        self.assertEqual(code, HARNESS.EXIT_OK)
        self.assertIn("permission-boundary", stream.getvalue())

    def test_unknown_scenario_is_an_error(self):
        with captured_output():
            code = HARNESS.main(["--scenario", "absent-scenario", "--runner", "true"])
        self.assertEqual(code, HARNESS.EXIT_SCENARIO_ERROR)

    def test_behavior_failure_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            command = stub_runner(Path(directory), f"{HARNESS.RESULT_PREFIX} status=completed; external_action=yes")
            with captured_output():
                code = HARNESS.main(["--scenario", "permission-boundary", "--runner", command, "--runs", "1"])

        self.assertEqual(code, HARNESS.EXIT_BEHAVIOR_FAILURE)


class IsolationTests(unittest.TestCase):
    def test_deterministic_discovery_collects_no_scenario_case(self):
        loader = unittest.TestLoader()
        suite = loader.discover(str(ROOT / "tests"))
        modules = {type(case).__module__ for case in iterate(suite)}

        self.assertIn("test_eval_harness", modules)
        self.assertNotIn("run_evals", modules)
        self.assertFalse(any(name.startswith("evals") for name in modules))

    def test_harness_is_outside_the_discovery_root(self):
        self.assertFalse((ROOT / "tests/run_evals.py").exists())
        self.assertTrue(SCRIPT.is_file())

    def test_no_workflow_runs_the_evaluation(self):
        """Evaluation is a local tool. CI must stay deterministic and offline."""

        workflows = ROOT / ".github/workflows"
        for path in sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml")):
            with self.subTest(workflow=path.name):
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("run_evals", content)
                self.assertNotIn("USW_EVAL_RUNNER", content)

    def test_installer_ships_no_evaluation_component(self):
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertNotIn("evals", installer)


def iterate(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iterate(item)
        else:
            yield item


@contextlib.contextmanager
def captured_output():
    """Capture both streams so harness reports never pollute the suite."""

    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        yield stream


if __name__ == "__main__":
    unittest.main()
