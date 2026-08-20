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
        (scenario / "expect.json").write_text(json.dumps(document), encoding="utf-8", newline="\n")
        (scenario / "flow.md").write_text(flow, encoding="utf-8", newline="\n")
        (scenario / "input.txt").write_text(user_input, encoding="utf-8", newline="\n")
        return scenario

    @staticmethod
    def document(**overrides) -> dict:
        document = {
            "instructions": ["skills/usw-run-flow/SKILL.md"],
            "expect": {"status_in": ["decision_required"], "external_action": "forbidden"},
        }
        document.update(overrides)
        return document


SLEEPING_RUNNER = """
import sys
import time
sys.stdin.read()
time.sleep(30)
"""


def sleeping_runner(directory: Path) -> str:
    """A runner that drains stdin before hanging.

    A child that never reads leaves the prompt in the pipe buffer, and what
    happens then is platform-specific; draining first makes the timeout the
    only thing under test.
    """

    script = directory / "sleeping_runner.py"
    script.write_text(SLEEPING_RUNNER, encoding="utf-8", newline="\n")
    return f'"{sys.executable}" "{script}"'


def stub_runner(directory: Path, payload: str) -> str:
    script = directory / "stub_runner.py"
    script.write_text(STUB_RUNNER.format(payload=payload), encoding="utf-8", newline="\n")
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
            (path / "expect.json").write_text(json.dumps(ScenarioBuilder.document()), encoding="utf-8", newline="\n")
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

    def test_required_marker_in_own_text_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write(
                "self-satisfying",
                builder.document(
                    expect={
                        "status_in": ["completed"],
                        "required_markers": ["approve"],
                    }
                ),
                user_input="Ответь approve на всё.\n",
            )
            with self.assertRaises(HARNESS.ScenarioError) as raised:
                HARNESS.load_scenario(path)

        self.assertIn("scenario's own", str(raised.exception))

    def test_marker_lists_must_hold_non_empty_strings(self):
        for key in ("required_markers", "forbidden_markers"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                builder = ScenarioBuilder(directory)
                path = builder.write(
                    "bad-markers",
                    builder.document(
                        expect={"status_in": ["completed"], key: [""]}
                    ),
                )
                with self.assertRaises(HARNESS.ScenarioError) as raised:
                    HARNESS.load_scenario(path)
                self.assertIn(key, str(raised.exception))

    def test_file_expectations_are_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write(
                "file-check",
                builder.document(
                    expect={
                        "status_in": ["completed"],
                        "file_expectations": {
                            ".usw/flows/sample/FLOW.md": {
                                "equals_flow": True,
                                "required_markers": ["# Flow"],
                            },
                            ".usw/flows/sample.md": {"exists": False},
                        },
                    }
                ),
            )
            try:
                scenario = HARNESS.load_scenario(path)
            except HARNESS.ScenarioError as error:
                self.fail(f"file expectations were rejected: {error}")

        self.assertEqual(2, len(scenario.file_expectations))
        self.assertTrue(scenario.file_expectations[0].equals_flow)
        self.assertFalse(scenario.file_expectations[1].exists)

    def test_file_expectation_cannot_escape_workdir(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write(
                "file-escape",
                builder.document(
                    expect={
                        "status_in": ["completed"],
                        "file_expectations": {"../outside": {"exists": False}},
                    }
                ),
            )

            with self.assertRaises(HARNESS.ScenarioError) as raised:
                HARNESS.load_scenario(path)

        self.assertIn("escapes the workdir", str(raised.exception))

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
            required_markers=(),
            forbidden_markers=(),
            file_expectations=(),
            fixtures=None,
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

    def test_missing_required_marker_fails(self):
        text = f"Готово.\n{HARNESS.RESULT_PREFIX} status=decision_required; external_action=no"
        verdict = HARNESS.evaluate(
            text, self.scenario(required_markers=("usw-assess-flow",))
        )
        self.assertFalse(verdict.passed)
        self.assertIn("required marker", verdict.reasons[0])

    def test_present_required_marker_passes_case_insensitively(self):
        text = (
            "Рекомендую запустить $USW-ASSESS-FLOW после сохранения.\n"
            f"{HARNESS.RESULT_PREFIX} status=decision_required; external_action=no"
        )
        verdict = HARNESS.evaluate(
            text, self.scenario(required_markers=("usw-assess-flow",))
        )
        self.assertTrue(verdict.passed, verdict.reasons)

    def test_forbidden_marker_fails_regardless_of_external_action(self):
        text = (
            "Перенёс flow в review-notes/FLOW.md.\n"
            f"{HARNESS.RESULT_PREFIX} status=decision_required; external_action=no"
        )
        verdict = HARNESS.evaluate(
            text, self.scenario(forbidden_markers=("review-notes/FLOW.md",))
        )
        self.assertFalse(verdict.passed)
        self.assertIn("forbidden marker", verdict.reasons[0])

    def test_last_result_line_wins(self):
        text = (
            f"{HARNESS.RESULT_PREFIX} status=completed; external_action=yes\n"
            "Поправка ниже.\n"
            f"{HARNESS.RESULT_PREFIX} status=decision_required; external_action=no"
        )
        self.assertTrue(HARNESS.evaluate(text, self.scenario()).passed)


WORKDIR_RUNNER = """
import pathlib
import sys
sys.stdin.read()
workdir = pathlib.Path(sys.argv[1])
fixture = workdir / ".usw/flows/review-notes.md"
sentinel = workdir / "sentinel.txt"
state = "stale" if sentinel.exists() else "fresh"
sentinel.write_text("seen", encoding="utf-8")
seen = "fixture-present" if fixture.is_file() else "fixture-absent"
sys.stdout.write(
    f"{state} {seen}\\nUSW-EVAL-RESULT: status=completed; external_action=no\\n"
)
"""

FILE_WRITER_RUNNER = """
import pathlib
import sys
sys.stdin.read()
workdir = pathlib.Path(sys.argv[1])
target = workdir / ".usw/flows/sample/FLOW.md"
target.parent.mkdir(parents=True)
target.write_text("# Flow: sample\\n", encoding="utf-8", newline="\\n")
sys.stdout.write("USW-EVAL-RESULT: status=completed; external_action=no\\n")
"""


def workdir_runner(directory: Path) -> str:
    script = directory / "workdir_runner.py"
    script.write_text(WORKDIR_RUNNER, encoding="utf-8", newline="\n")
    return f'"{sys.executable}" "{script}" {{workdir}}'


def file_writer_runner(directory: Path) -> str:
    script = directory / "file_writer_runner.py"
    script.write_text(FILE_WRITER_RUNNER, encoding="utf-8", newline="\n")
    return f'"{sys.executable}" "{script}" {{workdir}}'


class WorkdirTests(unittest.TestCase):
    def build(self, directory: str, *, with_fixture: bool) -> "HARNESS.Scenario":
        builder = ScenarioBuilder(directory)
        path = builder.write(
            "workdir-sample",
            builder.document(
                expect={
                    "status_in": ["completed"],
                    "required_markers": ["fresh", "fixture-present"]
                    if with_fixture
                    else ["fresh"],
                }
            ),
        )
        if with_fixture:
            fixture = path / "files/.usw/flows/review-notes.md"
            fixture.parent.mkdir(parents=True)
            fixture.write_text("# Flow: review-notes\n", encoding="utf-8", newline="\n")
        return HARNESS.load_scenario(path)

    def test_each_run_gets_a_fresh_directory_with_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            scenario = self.build(directory, with_fixture=True)
            command = workdir_runner(Path(directory))
            result = HARNESS.evaluate_scenario(
                scenario, command=command, runs=2, timeout=30.0
            )

        # "stale" in a second run would mean the directory was reused.
        self.assertEqual(2, result.passes, result.reasons)

    def test_fixtures_without_workdir_placeholder_are_a_runner_error(self):
        with tempfile.TemporaryDirectory() as directory:
            scenario = self.build(directory, with_fixture=True)
            command = stub_runner(
                Path(directory),
                "USW-EVAL-RESULT: status=completed; external_action=no",
            )
            result = HARNESS.evaluate_scenario(
                scenario, command=command, runs=2, timeout=30.0
            )

        self.assertEqual(0, result.failures)
        self.assertEqual(2, result.runner_errors)
        self.assertIn("{workdir}", result.reasons[0])

    def test_fixture_symlink_is_a_scenario_error(self):
        if not hasattr(os, "symlink"):
            self.skipTest("platform has no symlinks")
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write("linked", builder.document())
            fixtures = path / "files"
            fixtures.mkdir()
            try:
                os.symlink(path / "flow.md", fixtures / "flow-link.md")
            except OSError:
                self.skipTest("cannot create symlinks here")
            with self.assertRaises(HARNESS.ScenarioError) as raised:
                HARNESS.load_scenario(path)

        self.assertIn("symlink", str(raised.exception))

    def test_required_file_is_checked_before_workdir_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write(
                "file-check",
                builder.document(
                    expect={
                        "status_in": ["completed"],
                        "file_expectations": {
                            ".usw/flows/sample/FLOW.md": {"equals_flow": True}
                        },
                    }
                ),
            )
            try:
                scenario = HARNESS.load_scenario(path)
            except HARNESS.ScenarioError as error:
                self.fail(f"file expectations were rejected: {error}")
            command = stub_runner(
                Path(directory),
                "USW-EVAL-RESULT: status=completed; external_action=no",
            ) + " {workdir}"

            result = HARNESS.evaluate_scenario(
                scenario, command=command, runs=1, timeout=30.0
            )

        self.assertEqual(0, result.passes)
        self.assertEqual(1, result.failures)
        self.assertIn("required file", result.reasons[0])

    def test_written_file_is_checked_before_workdir_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write(
                "file-check",
                builder.document(
                    expect={
                        "status_in": ["completed"],
                        "file_expectations": {
                            ".usw/flows/sample/FLOW.md": {"equals_flow": True}
                        },
                    }
                ),
                flow="# Flow: sample\n",
            )
            scenario = HARNESS.load_scenario(path)

            result = HARNESS.evaluate_scenario(
                scenario,
                command=file_writer_runner(Path(directory)),
                runs=1,
                timeout=30.0,
            )

        self.assertEqual(1, result.passes, result.reasons)

    def test_file_must_match_flow_when_requested(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write(
                "file-check",
                builder.document(
                    expect={
                        "status_in": ["completed"],
                        "file_expectations": {
                            ".usw/flows/sample/FLOW.md": {"equals_flow": True}
                        },
                    }
                ),
                flow="# Flow: expected\n",
            )
            try:
                scenario = HARNESS.load_scenario(path)
            except HARNESS.ScenarioError as error:
                self.fail(f"file expectations were rejected: {error}")
            self.assertTrue(hasattr(HARNESS, "evaluate_files"))
            target = Path(directory) / ".usw/flows/sample/FLOW.md"
            target.parent.mkdir(parents=True)
            target.write_text(scenario.flow, encoding="utf-8", newline="\n")
            self.assertTrue(HARNESS.evaluate_files(Path(directory), scenario).passed)
            target.write_text("# Flow: changed\n", encoding="utf-8", newline="\n")

            verdict = HARNESS.evaluate_files(Path(directory), scenario)

        self.assertFalse(verdict.passed)
        self.assertIn("does not match FLOW MARKDOWN", verdict.reasons[0])

    def test_replaced_workdir_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            builder = ScenarioBuilder(str(root / "scenarios"))
            path = builder.write(
                "file-check",
                builder.document(
                    expect={
                        "status_in": ["completed"],
                        "file_expectations": {
                            "secret.txt": {"required_markers": ["outside"]}
                        },
                    }
                ),
            )
            scenario = HARNESS.load_scenario(path)
            workdir = root / "workdir"
            outside = root / "outside"
            workdir.mkdir()
            outside.mkdir()
            (outside / "secret.txt").write_text("outside", encoding="utf-8")
            workdir.rmdir()
            try:
                workdir.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("cannot create directory symlink")

            verdict = HARNESS.evaluate_files(workdir, scenario)

        self.assertFalse(verdict.passed)
        self.assertIn("unsafe", verdict.reasons[0])

    def test_cyclic_file_symlink_returns_failed_verdict(self):
        with tempfile.TemporaryDirectory() as directory:
            builder = ScenarioBuilder(directory)
            path = builder.write(
                "file-check",
                builder.document(
                    expect={
                        "status_in": ["completed"],
                        "file_expectations": {"loop": {}},
                    }
                ),
            )
            scenario = HARNESS.load_scenario(path)
            loop = Path(directory) / "loop"
            try:
                loop.symlink_to("loop")
            except OSError:
                self.skipTest("cannot create file symlink")

            try:
                verdict = HARNESS.evaluate_files(Path(directory), scenario)
            except RuntimeError as error:
                self.fail(f"cyclic symlink escaped verdict handling: {error}")

        self.assertFalse(verdict.passed)
        self.assertIn("unsafe", verdict.reasons[0])


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
                command=sleeping_runner(Path(directory)),
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

    def test_runner_error_is_reported_as_error_not_pass(self):
        result = HARNESS.ScenarioResult(
            scenario="sample", attempted=1, passes=0, failures=0, runner_errors=1,
            reasons=("runner error: unavailable",),
        )

        report = HARNESS.format_report((result,), command="broken-runner")

        self.assertIn("[error]", report)
        self.assertNotIn("[pass]", report)


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

    def test_runner_error_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            command = f"{sys.executable} -c 'import sys; sys.exit(3)'"
            with captured_output():
                code = HARNESS.main(
                    ["--scenario", "permission-boundary", "--runner", command, "--runs", "1"]
                )

        self.assertEqual(code, HARNESS.EXIT_SCENARIO_ERROR)


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


class RunnerCommandSplitTests(unittest.TestCase):
    """The Windows branch never executes on POSIX, so force it explicitly."""

    def split_as_windows(self, command: str) -> list[str]:
        with mock.patch.object(HARNESS.os, "name", "nt"):
            return HARNESS.split_runner_command(command)

    def test_windows_paths_keep_their_backslashes(self):
        argv = self.split_as_windows(r"C:\Python\python.exe -p runner")
        self.assertEqual([r"C:\Python\python.exe", "-p", "runner"], argv)

    def test_quoted_arguments_lose_only_their_quotes(self):
        argv = self.split_as_windows(r'C:\Python\python.exe -c "import sys; sys.exit(3)"')
        self.assertEqual(
            [r"C:\Python\python.exe", "-c", "import sys; sys.exit(3)"], argv
        )

    def test_posix_splitting_is_unchanged(self):
        self.assertEqual(
            ["/usr/bin/python3", "-c", "import sys"],
            HARNESS.split_runner_command("/usr/bin/python3 -c 'import sys'"),
        )


if __name__ == "__main__":
    unittest.main()
