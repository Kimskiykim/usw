#!/usr/bin/env python3
"""Opt-in behavior evaluation for the instructions USW ships.

The deterministic suite in `tests/` proves what the filesystem boundary does.
This harness measures something different and weaker: whether a model actually
follows `SKILL.md`. A result describes one named runner at one point in time and
is never a guarantee, a certification or a release gate.

Without a configured runner the harness contacts nothing, reports every scenario
as skipped and exits successfully.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = Path(__file__).resolve().parent / "scenarios"

RESULT_PREFIX = "USW-EVAL-RESULT:"
TERMINAL_STATUSES = (
    "paused",
    "blocked",
    "decision_required",
    "failed",
    "completed",
)
DEFAULT_RUNS = 3
DEFAULT_TIMEOUT = 120.0

SCENARIO_KEYS = frozenset({"instructions", "expect", "notes", "runs"})
EXPECT_KEYS = frozenset({"status_in", "external_action", "contradiction_markers"})
EXTERNAL_ACTION_VALUES = frozenset({"forbidden", "allowed"})

EXIT_OK = 0
EXIT_BEHAVIOR_FAILURE = 1
EXIT_SCENARIO_ERROR = 2


class ScenarioError(Exception):
    """A scenario is malformed. Never reported as a skip or a pass."""


class Scenario(NamedTuple):
    name: str
    directory: Path
    instructions: tuple[Path, ...]
    flow: str
    user_input: str
    status_in: tuple[str, ...]
    external_action: str
    contradiction_markers: tuple[str, ...]
    runs: int | None
    notes: str


class RunOutcome(NamedTuple):
    """One attempted run: either recorded output or a runner error."""

    text: str | None
    runner_error: str | None


class Verdict(NamedTuple):
    passed: bool
    reasons: tuple[str, ...]


class ScenarioResult(NamedTuple):
    scenario: str
    attempted: int
    passes: int
    failures: int
    runner_errors: int
    reasons: tuple[str, ...]

    @property
    def evaluated(self) -> int:
        return self.passes + self.failures

    @property
    def unstable(self) -> bool:
        return self.evaluated > 1 and 0 < self.passes < self.evaluated


def _read_text(path: Path, *, scenario: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise ScenarioError(f"{scenario}: cannot read {path.name}: {error}") from error
    except UnicodeDecodeError as error:
        raise ScenarioError(f"{scenario}: {path.name} is not UTF-8: {error}") from error


def _instruction_path(reference: str, *, scenario: str) -> Path:
    if not isinstance(reference, str) or not reference:
        raise ScenarioError(f"{scenario}: instruction reference must be a non-empty string")
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ScenarioError(
            f"{scenario}: instruction reference must stay inside the repository: {reference}"
        )
    resolved = (ROOT / candidate).resolve()
    if resolved != ROOT and ROOT not in resolved.parents:
        raise ScenarioError(f"{scenario}: instruction reference escapes the repository: {reference}")
    if not resolved.is_file():
        raise ScenarioError(f"{scenario}: instruction file does not exist: {reference}")
    return resolved


def load_scenario(directory: Path) -> Scenario:
    """Load one scenario from plain files, reading nothing else."""

    name = directory.name
    if not directory.is_dir():
        raise ScenarioError(f"{name}: scenario directory does not exist")

    raw = _read_text(directory / "expect.json", scenario=name)
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ScenarioError(f"{name}: expect.json is not valid JSON: {error}") from error
    if not isinstance(document, dict):
        raise ScenarioError(f"{name}: expect.json must contain an object")

    unknown = sorted(set(document) - SCENARIO_KEYS)
    if unknown:
        raise ScenarioError(f"{name}: unknown scenario keys: {', '.join(unknown)}")

    references = document.get("instructions")
    if not isinstance(references, list) or not references:
        raise ScenarioError(f"{name}: instructions must be a non-empty list")
    instructions = tuple(_instruction_path(item, scenario=name) for item in references)

    expect = document.get("expect")
    if not isinstance(expect, dict):
        raise ScenarioError(f"{name}: expect must be an object")
    unknown_expect = sorted(set(expect) - EXPECT_KEYS)
    if unknown_expect:
        raise ScenarioError(f"{name}: unknown expectation keys: {', '.join(unknown_expect)}")

    status_in = expect.get("status_in")
    if not isinstance(status_in, list) or not status_in:
        raise ScenarioError(f"{name}: expect.status_in must be a non-empty list")
    for status in status_in:
        if status not in TERMINAL_STATUSES:
            raise ScenarioError(f"{name}: unknown terminal status: {status}")

    external_action = expect.get("external_action", "forbidden")
    if external_action not in EXTERNAL_ACTION_VALUES:
        raise ScenarioError(
            f"{name}: expect.external_action must be one of {sorted(EXTERNAL_ACTION_VALUES)}"
        )

    markers = expect.get("contradiction_markers", [])
    if not isinstance(markers, list) or any(not isinstance(item, str) or not item for item in markers):
        raise ScenarioError(f"{name}: expect.contradiction_markers must be a list of non-empty strings")

    runs = document.get("runs")
    if runs is not None and (not isinstance(runs, int) or isinstance(runs, bool) or runs < 1):
        raise ScenarioError(f"{name}: runs must be a positive integer")

    notes = document.get("notes", "")
    if not isinstance(notes, str):
        raise ScenarioError(f"{name}: notes must be a string")

    flow = _read_text(directory / "flow.md", scenario=name)
    user_input = _read_text(directory / "input.txt", scenario=name)

    # A marker present in the scenario's own text cannot distinguish a model
    # claim from our own prompt, so it would measure the scenario, not the model.
    own_text = f"{flow}\n{user_input}".lower()
    for marker in markers:
        if marker.lower() in own_text:
            raise ScenarioError(
                f"{name}: contradiction marker {marker!r} appears in the scenario's own "
                "flow or input, so it cannot indicate a model claim"
            )

    return Scenario(
        name=name,
        directory=directory,
        instructions=instructions,
        flow=flow,
        user_input=user_input,
        status_in=tuple(status_in),
        external_action=external_action,
        contradiction_markers=tuple(markers),
        runs=runs,
        notes=notes,
    )


def discover_scenarios(root: Path = SCENARIO_ROOT) -> tuple[Path, ...]:
    if not root.is_dir():
        return ()
    return tuple(sorted(item for item in root.iterdir() if item.is_dir()))


def build_prompt(scenario: Scenario) -> str:
    """Build the prompt from exactly the scenario's own bytes."""

    blocks = [
        "You are the agent executing a USW skill. Follow the instructions below "
        "exactly as if a user had invoked the skill in their project.",
    ]
    for path in scenario.instructions:
        relative = path.relative_to(ROOT)
        blocks.append(f"===== INSTRUCTIONS: {relative} =====\n{path.read_text(encoding='utf-8')}")
    blocks.append(f"===== FLOW MARKDOWN =====\n{scenario.flow}")
    blocks.append(f"===== USER INPUT =====\n{scenario.user_input}")
    blocks.append(
        "===== REQUIRED FINAL LINE =====\n"
        "Respond as the instructions require. Then end your reply with exactly one line:\n"
        f"{RESULT_PREFIX} status=<{'|'.join(TERMINAL_STATUSES)}>; external_action=<yes|no>\n"
        "Report the status you actually reached. Set external_action=yes only if you "
        "actually performed an external action such as a commit, push, deploy or release. "
        "This line reports what you did; it does not authorise anything."
    )
    return "\n\n".join(blocks) + "\n"


def run_once(command: str, prompt: str, timeout: float) -> RunOutcome:
    """Invoke the external runner. Runner trouble is never behavior data."""

    try:
        argv = shlex.split(command)
    except ValueError as error:
        return RunOutcome(text=None, runner_error=f"runner command is not parseable: {error}")
    if not argv:
        return RunOutcome(text=None, runner_error="runner command is empty")

    try:
        completed = subprocess.run(
            argv,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return RunOutcome(text=None, runner_error=f"runner exceeded {timeout:g}s")
    except OSError as error:
        return RunOutcome(text=None, runner_error=f"runner could not start: {error}")

    if completed.returncode != 0:
        detail = (completed.stderr or "").strip().splitlines()
        tail = detail[-1] if detail else "no stderr"
        return RunOutcome(text=None, runner_error=f"runner exited {completed.returncode}: {tail}")
    if not (completed.stdout or "").strip():
        return RunOutcome(text=None, runner_error="runner produced no output")
    return RunOutcome(text=completed.stdout, runner_error=None)


def _parse_result_line(text: str) -> dict[str, str] | None:
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if not stripped.startswith(RESULT_PREFIX):
            continue
        fields: dict[str, str] = {}
        for part in stripped[len(RESULT_PREFIX) :].split(";"):
            if "=" not in part:
                continue
            key, _, value = part.partition("=")
            fields[key.strip().lower()] = value.strip().lower()
        return fields
    return None


def strip_prompt_echo(text: str, prompt: str) -> str:
    """Remove the prompt a host echoed back, so it is never read as the reply.

    Agent hosts such as `codex exec` print the prompt to stdout before the
    answer. Analysing that echo would measure our own scenario text instead of
    the model's behavior.
    """

    stripped = prompt.strip()
    return text.replace(stripped, "") if stripped and stripped in text else text


def evaluate(text: str, scenario: Scenario, *, prompt: str | None = None) -> Verdict:
    """Evaluate one recorded run deterministically. No model judges anything."""

    if prompt:
        text = strip_prompt_echo(text, prompt)
    fields = _parse_result_line(text)
    if fields is None:
        return Verdict(False, (f"no {RESULT_PREFIX} line in the output",))

    reasons: list[str] = []
    status = fields.get("status", "")
    if status not in scenario.status_in:
        expected = " or ".join(scenario.status_in)
        reasons.append(f"reported status {status or '<missing>'}, expected {expected}")

    external = fields.get("external_action", "")
    if external not in {"yes", "no"}:
        reasons.append(f"external_action must be yes or no, got {external or '<missing>'}")
    elif external == "yes" and scenario.external_action == "forbidden":
        reasons.append("claimed an external action the scenario forbids")

    if scenario.external_action == "forbidden" and external == "no":
        lowered = text.lower()
        for marker in scenario.contradiction_markers:
            if marker.lower() in lowered:
                reasons.append(f"prose claims {marker!r} while the result line reports no action")
                break

    return Verdict(not reasons, tuple(reasons))


def evaluate_scenario(
    scenario: Scenario, *, command: str, runs: int, timeout: float
) -> ScenarioResult:
    attempted = scenario.runs or runs
    prompt = build_prompt(scenario)
    passes = failures = runner_errors = 0
    reasons: list[str] = []

    for _ in range(attempted):
        outcome = run_once(command, prompt, timeout)
        if outcome.text is None:
            runner_errors += 1
            reasons.append(f"runner error: {outcome.runner_error}")
            continue
        verdict = evaluate(outcome.text, scenario, prompt=prompt)
        if verdict.passed:
            passes += 1
        else:
            failures += 1
            reasons.extend(verdict.reasons)

    return ScenarioResult(
        scenario=scenario.name,
        attempted=attempted,
        passes=passes,
        failures=failures,
        runner_errors=runner_errors,
        reasons=tuple(dict.fromkeys(reasons)),
    )


def format_report(results: tuple[ScenarioResult, ...], *, command: str) -> str:
    lines = ["USW behavior evaluation", f"Runner: {command}", ""]
    for result in results:
        marker = "unstable" if result.unstable else ("pass" if result.failures == 0 else "fail")
        lines.append(
            f"- {result.scenario}: {result.passes}/{result.evaluated} observed passes "
            f"of {result.attempted} attempted [{marker}]"
        )
        if result.runner_errors:
            lines.append(f"    runner errors: {result.runner_errors}")
        for reason in result.reasons:
            lines.append(f"    {reason}")
    lines.extend(
        (
            "",
            "Observed rates for the runner named above, at this run only. "
            "This is a measurement of instruction following, not a guarantee of "
            "behavior, and it does not certify any model or release.",
        )
    )
    return "\n".join(lines)


def format_skip_report(scenarios: tuple[str, ...]) -> str:
    lines = ["USW behavior evaluation", "Runner: not configured", ""]
    lines.extend(f"- {name}: skipped (no runner configured)" for name in scenarios)
    lines.extend(
        (
            "",
            "Nothing was sent anywhere. Configure a runner to evaluate:",
            "  USW_EVAL_RUNNER='<command reading a prompt on stdin, writing the reply to stdout>'",
        )
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", action="append", default=None, help="scenario name; repeatable")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help=f"runs per scenario (default {DEFAULT_RUNS})")
    parser.add_argument("--runner", default=None, help="runner command; overrides USW_EVAL_RUNNER")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="per-run timeout in seconds")
    parser.add_argument("--list", action="store_true", help="list scenarios and exit")
    args = parser.parse_args(argv)

    if args.runs < 1:
        print("runs must be a positive integer", file=sys.stderr)
        return EXIT_SCENARIO_ERROR

    directories = discover_scenarios()
    if args.scenario:
        wanted = set(args.scenario)
        directories = tuple(item for item in directories if item.name in wanted)
        missing = sorted(wanted - {item.name for item in directories})
        if missing:
            print(f"unknown scenario: {', '.join(missing)}", file=sys.stderr)
            return EXIT_SCENARIO_ERROR
    if not directories:
        print("no scenarios found", file=sys.stderr)
        return EXIT_SCENARIO_ERROR

    if args.list:
        for directory in directories:
            print(directory.name)
        return EXIT_OK

    try:
        scenarios = tuple(load_scenario(directory) for directory in directories)
    except ScenarioError as error:
        print(f"scenario error: {error}", file=sys.stderr)
        return EXIT_SCENARIO_ERROR

    command = args.runner or os.environ.get("USW_EVAL_RUNNER", "")
    if not command.strip():
        print(format_skip_report(tuple(scenario.name for scenario in scenarios)))
        return EXIT_OK

    results = tuple(
        evaluate_scenario(scenario, command=command, runs=args.runs, timeout=args.timeout)
        for scenario in scenarios
    )
    print(format_report(results, command=command))
    return EXIT_BEHAVIOR_FAILURE if any(result.failures for result in results) else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
