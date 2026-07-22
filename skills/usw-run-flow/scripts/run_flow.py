#!/usr/bin/env python3
"""Deterministic one-action orchestration for role and custom USW flows."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping, NamedTuple


CUSTOM_FLOW_VERSION = 1
CUSTOM_FLOW_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_CUSTOM_SECTIONS = ("Контракт", "Порядок действий")
CUSTOM_FLOW_ORIGINS = frozenset({"shared", "local"})
STANDARD_FLOW_NAMES = frozenset({"analysis", "development", "testing"})


class CustomFlowError(ValueError):
    def __init__(self, code: str, message: str, line: int | None = None) -> None:
        location = f" at line {line}" if line is not None else ""
        super().__init__(f"{code}{location}: {message}")
        self.code = code
        self.line = line


class CustomStep(NamedTuple):
    kind: str
    target: str
    arguments: tuple[str, ...]
    declared_writes: frozenset[str] | None


class CustomFlow(NamedTuple):
    name: str
    steps: tuple[CustomStep, ...]
    artifact_roles: frozenset[str] | None
    origin: str
    identity: str

    @property
    def actions(self) -> tuple[str, ...]:
        return tuple(str(index) for index in range(1, len(self.steps) + 1))

    @property
    def branches(self) -> tuple[tuple[str, str, str], ...]:
        return ()


def _markdown_sections(content: str) -> dict[str, tuple[int, str]]:
    headings = list(re.finditer(r"^## (.+?)\s*$", content, re.MULTILINE))
    sections: dict[str, tuple[int, str]] = {}
    for index, match in enumerate(headings):
        name = match.group(1).strip()
        if name in sections:
            raise CustomFlowError(
                "duplicate_section", f"duplicate section {name!r}", content.count("\n", 0, match.start()) + 1
            )
        end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
        line = content.count("\n", 0, match.start()) + 1
        sections[name] = (line, content[match.end() : end].strip())
    return sections


def _code_values(value: str, *, line: int, field: str) -> tuple[str, ...]:
    if value.strip().casefold().rstrip(".") == "нет":
        return ()
    values = tuple(re.findall(r"`([^`]+)`", value))
    remainder = re.sub(r"`[^`]+`", "", value).strip(" ,")
    if not values or remainder:
        raise CustomFlowError(
            "invalid_field", f"{field} must contain code values or 'нет'", line
        )
    return values


def _parse_step_fields(lines: list[str], start: int, section_line: int) -> tuple[dict[str, tuple[int, str]], int]:
    fields: dict[str, tuple[int, str]] = {}
    index = start
    while index < len(lines) and not re.match(r"^[0-9]+\. ", lines[index]):
        source = lines[index]
        if not source.strip():
            index += 1
            continue
        match = re.match(r"^\s{3}- (Пишет|Аргументы):\s*(.+)$", source)
        line = section_line + index + 1
        if not match:
            raise CustomFlowError("invalid_step_field", "unexpected step field", line)
        name, value = match.groups()
        if name in fields:
            raise CustomFlowError("duplicate_step_field", f"duplicate field {name!r}", line)
        fields[name] = (line, value)
        index += 1
    return fields, index


def parse_custom_flow(
    content: str, name: str, *, origin: str = "shared"
) -> CustomFlow:
    """Parse the strict executable subset of an otherwise ordinary Markdown file."""
    if not CUSTOM_FLOW_NAME.fullmatch(name):
        raise CustomFlowError("invalid_flow_name", f"unsafe flow name: {name!r}")
    if origin not in CUSTOM_FLOW_ORIGINS:
        raise CustomFlowError("invalid_flow_origin", f"unsupported flow origin: {origin!r}")
    if origin == "local" and name in STANDARD_FLOW_NAMES:
        raise CustomFlowError(
            "unsupported_local_standard_flow",
            f"standard flow cannot be developer-local: {name}",
        )
    sections = _markdown_sections(content)
    for forbidden in ("Branches", "Ветвления", "Переходы"):
        if forbidden in sections:
            raise CustomFlowError("unsupported_branch", "custom flows are linear", sections[forbidden][0])
    missing = [section for section in REQUIRED_CUSTOM_SECTIONS if section not in sections]
    if missing:
        raise CustomFlowError("missing_section", f"missing sections: {', '.join(missing)}")
    positions = [sections[section][0] for section in REQUIRED_CUSTOM_SECTIONS]
    if positions != sorted(positions):
        raise CustomFlowError("invalid_section_order", "required sections are out of order")

    contract_line, contract = sections["Контракт"]
    versions = re.findall(r"^- Версия: `([^`]+)`$", contract, re.MULTILINE)
    if versions != [str(CUSTOM_FLOW_VERSION)]:
        raise CustomFlowError(
            "unsupported_flow_schema",
            f"expected exactly one version {CUSTOM_FLOW_VERSION}",
            contract_line,
        )

    actions_line, actions = sections["Порядок действий"]
    authority_entry = sections.get("Полномочия записи")
    if authority_entry is None:
        artifact_roles = None
    else:
        authority_line, authority = authority_entry
        if authority_line < actions_line:
            raise CustomFlowError(
                "invalid_section_order", "write authority must follow actions", authority_line
            )
        authority_lines = [line for line in authority.splitlines() if line.strip()]
        if authority_lines == ["- Нет."] or authority_lines == ["- Нет"]:
            artifact_roles = frozenset()
        else:
            roles = [re.fullmatch(r"- `([^`]+)`", line) for line in authority_lines]
            if not roles or any(match is None for match in roles):
                raise CustomFlowError(
                    "invalid_write_authority", "expected '- `role`' entries or '- Нет.'", authority_line
                )
            artifact_roles = frozenset(match.group(1) for match in roles if match)

    lines = actions.splitlines()
    steps: list[CustomStep] = []
    index = 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        line_number = actions_line + index + 1
        match = re.fullmatch(r"([0-9]+)\. (Скилл|Скрипт): `([^`]+)`", lines[index])
        if not match:
            raise CustomFlowError("invalid_step", "expected a Skill or Script list item", line_number)
        number, label, target = match.groups()
        if int(number) != len(steps) + 1:
            raise CustomFlowError("invalid_step_number", "steps must be numbered consecutively", line_number)
        fields, index = _parse_step_fields(lines, index + 1, actions_line)
        if artifact_roles is None:
            if "Пишет" in fields:
                raise CustomFlowError(
                    "partial_write_contract",
                    "step write metadata requires a write authority section",
                    fields["Пишет"][0],
                )
            writes = None
        else:
            if "Пишет" not in fields:
                raise CustomFlowError("missing_step_field", "step is missing 'Пишет'", line_number)
            writes_line, writes_value = fields["Пишет"]
            writes = frozenset(_code_values(writes_value, line=writes_line, field="Пишет"))
        if writes is not None and artifact_roles is not None and not writes <= artifact_roles:
            raise CustomFlowError(
                "authority_mismatch", "step writes exceed flow write authority", writes_line
            )
        kind = "skill" if label == "Скилл" else "script"
        if kind == "skill" and "Аргументы" in fields:
            raise CustomFlowError(
                "invalid_step_field", "skill steps do not accept script arguments", fields["Аргументы"][0]
            )
        args: tuple[str, ...] = ()
        if "Аргументы" in fields:
            args_line, args_value = fields["Аргументы"]
            args = _code_values(args_value, line=args_line, field="Аргументы")
        steps.append(CustomStep(kind, target, args, writes))
    if not steps:
        raise CustomFlowError("missing_steps", "flow must contain at least one step", actions_line)

    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    identity = (
        f"usw-flow-v1:{digest}"
        if origin == "shared"
        else f"usw-flow-v1:local:{digest}"
    )
    return CustomFlow(name, tuple(steps), artifact_roles, origin, identity)


def load_custom_flow(
    flow_root: Path, name: str, *, origin: str = "shared"
) -> CustomFlow:
    """Load one selected custom flow without interpreting a path selector."""
    if not CUSTOM_FLOW_NAME.fullmatch(name):
        raise CustomFlowError("invalid_flow_name", f"unsafe flow name: {name!r}")
    path = flow_root / f"{name}.md"
    try:
        mode = os.lstat(path).st_mode
    except FileNotFoundError as error:
        raise CustomFlowError("missing_flow", f"custom flow is missing: {path}") from error
    if not stat.S_ISREG(mode):
        raise CustomFlowError("invalid_flow_file", f"custom flow is not a regular file: {path}")
    return parse_custom_flow(path.read_text(encoding="utf-8"), name, origin=origin)


def local_custom_flow_root(project_root: Path, *, create: bool = False) -> Path:
    """Resolve the fixed developer-local flow root without traversing symlinks."""
    local_root = project_root.resolve() / ".usw"
    try:
        local_mode = os.lstat(local_root).st_mode
    except FileNotFoundError as error:
        raise CustomFlowError(
            "missing_local_state", f"local state is missing: {local_root}"
        ) from error
    if not stat.S_ISDIR(local_mode) or stat.S_ISLNK(local_mode):
        raise CustomFlowError(
            "invalid_local_state", f"unsafe local state directory: {local_root}"
        )

    flow_root = local_root / "flows"
    try:
        flow_mode = os.lstat(flow_root).st_mode
    except FileNotFoundError:
        if create:
            flow_root.mkdir(mode=0o700)
        return flow_root
    if not stat.S_ISDIR(flow_mode) or stat.S_ISLNK(flow_mode):
        raise CustomFlowError(
            "invalid_local_flow_root", f"unsafe local flow directory: {flow_root}"
        )
    return flow_root


class ActionOutcome(NamedTuple):
    status: str
    outcome: str
    written_roles: frozenset[str] = frozenset()
    output_references: tuple[str, ...] = ()
    detail: str | None = None


class Executor(NamedTuple):
    declared_writes: frozenset[str]
    invoke: Callable[[str], ActionOutcome]
    available: bool = True
    is_stub: bool = False


def _resolve_project_script(project_root: Path, value: str) -> Path:
    if re.search(r"[\s;&|`$<>]", value) or "\\" in value:
        raise CustomFlowError("invalid_script_path", f"unsafe script path: {value!r}")
    path = PurePosixPath(value)
    if not value or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CustomFlowError("invalid_script_path", f"unsafe script path: {value!r}")
    current = project_root.resolve()
    for part in path.parts:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError as error:
            raise CustomFlowError("missing_script", f"script is missing: {current}") from error
        if stat.S_ISLNK(mode):
            raise CustomFlowError("invalid_script_path", f"script path traverses symlink: {current}")
    if not stat.S_ISREG(mode):
        raise CustomFlowError("invalid_script_path", f"script is not a regular file: {current}")
    if not os.access(current, os.X_OK):
        raise CustomFlowError("script_not_executable", f"script is not executable: {current}")
    return current


def _script_executor(
    project_root: Path,
    step: CustomStep,
    *,
    authorized: bool,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> Executor:
    script = _resolve_project_script(project_root, step.target)
    declared_writes = step.declared_writes or frozenset()

    def invoke(_scope: str) -> ActionOutcome:
        if not authorized:
            return ActionOutcome(
                "permission_required",
                "script_permission_required",
                detail=f"Ask for explicit permission to run {step.target}.",
            )
        try:
            completed = runner(
                [str(script), *step.arguments],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            return ActionOutcome(
                "failed", "script_failed", declared_writes, detail=str(error)
            )
        detail = (completed.stderr or completed.stdout or "").strip() or None
        if completed.returncode:
            return ActionOutcome(
                "failed", "script_failed", declared_writes, detail=detail
            )
        return ActionOutcome("completed", "passed", declared_writes, detail=detail)

    return Executor(declared_writes, invoke)


def resolve_custom_executors(
    flow: CustomFlow,
    skill_executors: Mapping[str, Executor],
    *,
    project_root: Path,
    script_permissions: frozenset[str] = frozenset(),
    script_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Executor]:
    """Resolve every custom step before the first executor can mutate state."""
    resolved: dict[str, Executor] = {}
    for index, step in enumerate(flow.steps, start=1):
        if step.kind == "skill":
            executor = skill_executors.get(step.target)
            if executor is None or not executor.available:
                raise CustomFlowError("missing_skill", f"skill is unavailable: {step.target}")
            if (
                step.declared_writes is not None
                and executor.declared_writes != step.declared_writes
            ):
                raise CustomFlowError(
                    "skill_contract_mismatch",
                    f"declared writes for {step.target} do not match its capability contract",
                )
            resolved[str(index)] = executor
            continue
        resolved[str(index)] = _script_executor(
            project_root,
            step,
            authorized=step.target in script_permissions,
            runner=script_runner,
        )
    return resolved


class FlowState(NamedTuple):
    action_index: int = 0
    selected_scope: str | None = None
    stopped: bool = False


class CustomFlowCheckpoint(NamedTuple):
    schema_version: int
    flow_name: str
    flow_identity: str
    selected_scope: str
    next_action_index: int
    source_identity: str | None


def _custom_checkpoint_path(project_root: Path) -> Path:
    local_root = project_root / ".usw"
    try:
        mode = os.lstat(local_root).st_mode
    except FileNotFoundError as error:
        raise CustomFlowError("missing_local_state", f"local state is missing: {local_root}") from error
    if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
        raise CustomFlowError("invalid_local_state", f"unsafe local state directory: {local_root}")
    path = local_root / "FLOW.json"
    try:
        path_mode = os.lstat(path).st_mode
    except FileNotFoundError:
        return path
    if not stat.S_ISREG(path_mode):
        raise CustomFlowError("invalid_local_state", f"unsafe flow checkpoint: {path}")
    return path


def save_custom_checkpoint(
    project_root: Path,
    flow: CustomFlow,
    state: FlowState,
    *,
    source_identity: str | None,
) -> Path:
    if state.selected_scope is None:
        raise CustomFlowError("missing_scope", "cannot checkpoint a flow without scope")
    if not 0 <= state.action_index <= len(flow.steps):
        raise CustomFlowError("invalid_checkpoint", "next action index is outside the flow")
    path = _custom_checkpoint_path(project_root)
    payload = {
        "schema_version": 1,
        "flow_name": flow.name,
        "flow_identity": flow.identity,
        "selected_scope": state.selected_scope,
        "next_action_index": state.action_index,
        "source_identity": source_identity,
    }
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix="FLOW.", suffix=".tmp", delete=False
        ) as temporary:
            temporary_name = temporary.name
            json.dump(payload, temporary, ensure_ascii=False, sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return path


def load_custom_checkpoint(project_root: Path) -> CustomFlowCheckpoint:
    path = _custom_checkpoint_path(project_root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CustomFlowError("missing_checkpoint", f"flow checkpoint is missing: {path}") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise CustomFlowError("invalid_checkpoint", f"invalid flow checkpoint: {path}") from error
    expected = {
        "schema_version", "flow_name", "flow_identity", "selected_scope",
        "next_action_index", "source_identity",
    }
    if not isinstance(data, dict) or set(data) != expected:
        raise CustomFlowError("invalid_checkpoint", "unexpected checkpoint fields")
    if (
        data["schema_version"] != 1
        or not isinstance(data["flow_name"], str)
        or not isinstance(data["flow_identity"], str)
        or not isinstance(data["selected_scope"], str)
        or not isinstance(data["next_action_index"], int)
        or (data["source_identity"] is not None and not isinstance(data["source_identity"], str))
    ):
        raise CustomFlowError("invalid_checkpoint", "invalid checkpoint values")
    return CustomFlowCheckpoint(
        data["schema_version"],
        data["flow_name"],
        data["flow_identity"],
        data["selected_scope"],
        data["next_action_index"],
        data["source_identity"],
    )


def resume_custom_state(
    flow: CustomFlow,
    checkpoint: CustomFlowCheckpoint,
    *,
    current_source_identity: str | None,
) -> FlowState:
    if checkpoint.flow_name != flow.name or checkpoint.flow_identity != flow.identity:
        raise CustomFlowError("stale_flow", "flow changed after the checkpoint was saved")
    if not 0 <= checkpoint.next_action_index <= len(flow.steps):
        raise CustomFlowError("invalid_checkpoint", "next action index is outside the flow")
    if checkpoint.source_identity is not None:
        if current_source_identity is None:
            raise CustomFlowError("unknown_source_context", "current source identity is unavailable")
        if checkpoint.source_identity != current_source_identity:
            raise CustomFlowError("stale_source_context", "product source changed after checkpoint")
    return FlowState(checkpoint.next_action_index, checkpoint.selected_scope, False)


class FlowResult(NamedTuple):
    state: FlowState
    status: str
    action: str | None
    output_references: tuple[str, ...]
    stop_reason: str | None
    next_action: str


def _branch_target(scenario, action: str, outcome: str) -> str | None:
    matches = [target for source, branch_outcome, target in scenario.branches if source == action and branch_outcome == outcome]
    if len(matches) > 1:
        raise ValueError(f"ambiguous branch for {action}:{outcome}")
    return matches[0] if matches else None


def run_next(
    scenario,
    state: FlowState,
    executors: Mapping[str, Executor],
    *,
    allowed_scopes: tuple[str, ...],
    selected_scope: str | None = None,
    allow_stubs: bool = False,
) -> FlowResult:
    """Run at most one action and always return control to the orchestrator."""
    if state.stopped:
        return FlowResult(state, "stopped", None, (), "flow_already_stopped", "Start a new scoped run.")
    scope = selected_scope or state.selected_scope
    if scope is None:
        if len(allowed_scopes) != 1:
            options = ", ".join(allowed_scopes) or "none"
            return FlowResult(state, "decision_required", None, (), "scope_required", f"Choose one scope: {options}.")
        scope = allowed_scopes[0]
    if scope not in allowed_scopes:
        return FlowResult(state, "decision_required", None, (), "invalid_scope", "Choose one of the currently allowed scopes.")
    if state.action_index >= len(scenario.actions):
        complete = FlowState(state.action_index, scope, True)
        return FlowResult(complete, "completed", None, (), "scope_complete", "Report the scoped result.")

    action = scenario.actions[state.action_index]
    executor = executors.get(action)
    if executor is None or not executor.available or (executor.is_stub and not allow_stubs):
        return FlowResult(
            FlowState(state.action_index, scope, False),
            "blocked",
            action,
            (),
            "missing_executor",
            f"Install or connect capability executor: {action}.",
        )
    artifact_roles = scenario.artifact_roles
    if artifact_roles is None:
        artifact_roles = executor.declared_writes
    unauthorized = executor.declared_writes - artifact_roles
    if unauthorized:
        return FlowResult(
            FlowState(state.action_index, scope, False),
            "blocked",
            action,
            (),
            "authority_mismatch",
            "Use an executor whose declared writes fit scenario authority.",
        )

    outcome = executor.invoke(scope)
    if outcome.written_roles - executor.declared_writes or outcome.written_roles - artifact_roles:
        return FlowResult(
            FlowState(state.action_index, scope, True),
            "failed",
            action,
            outcome.output_references,
            "executor_contract_violation",
            "Inspect the executor; it reported undeclared writes.",
        )
    if outcome.status != "completed":
        return FlowResult(
            FlowState(state.action_index, scope, True),
            outcome.status,
            action,
            outcome.output_references,
            outcome.outcome,
            outcome.detail or "Resolve the reported boundary before continuing.",
        )

    target = _branch_target(scenario, action, outcome.outcome)
    if target and target.startswith("stop:"):
        reason = target.removeprefix("stop:")
        return FlowResult(
            FlowState(state.action_index, scope, True),
            "completed" if reason in {"scope-complete", "delivery"} else "stopped",
            action,
            outcome.output_references,
            reason,
            "Report the scoped result." if reason in {"scope-complete", "delivery"} else "Resolve the stop condition.",
        )
    next_index = scenario.actions.index(target) if target else state.action_index + 1
    return FlowResult(
        FlowState(next_index, scope, False),
        "action_completed",
        action,
        outcome.output_references,
        None,
        "Run the next scenario action.",
    )


def run_custom_next(
    flow: CustomFlow,
    state: FlowState,
    skill_executors: Mapping[str, Executor],
    *,
    project_root: Path,
    allowed_scopes: tuple[str, ...],
    selected_scope: str | None = None,
    script_permissions: frozenset[str] = frozenset(),
    script_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> FlowResult:
    executors = resolve_custom_executors(
        flow,
        skill_executors,
        project_root=project_root,
        script_permissions=script_permissions,
        script_runner=script_runner,
    )
    return run_next(
        flow,
        state,
        executors,
        allowed_scopes=allowed_scopes,
        selected_scope=selected_scope,
    )


def authorize_external_action(
    *, delivery_reached: bool, action: str, explicit_permissions: frozenset[str]
) -> FlowResult:
    """Keep Delivery acceptance separate from external side-effect authority."""
    if not delivery_reached:
        return FlowResult(FlowState(stopped=True), "blocked", None, (), "delivery_not_reached", "Complete Testing handoff first.")
    if action not in explicit_permissions:
        return FlowResult(FlowState(stopped=True), "permission_required", None, (), "external_permission_required", f"Ask for explicit permission to {action}.")
    return FlowResult(FlowState(stopped=True), "authorized", None, (), None, f"Perform only the authorized action: {action}.")


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and support custom USW flows")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate")
    validate.add_argument("flow_root", type=Path)
    validate.add_argument("name")
    validate.add_argument("-l", "--local", action="store_true")

    run_script = commands.add_parser("run-script")
    run_script.add_argument("project_root", type=Path)
    run_script.add_argument("flow_root", type=Path)
    run_script.add_argument("name")
    run_script.add_argument("step", type=int)
    run_script.add_argument("--authorized", action="store_true")
    run_script.add_argument("-l", "--local", action="store_true")

    save = commands.add_parser("checkpoint-save")
    save.add_argument("project_root", type=Path)
    save.add_argument("flow_root", type=Path)
    save.add_argument("name")
    save.add_argument("next_action_index", type=int)
    save.add_argument("scope")
    save.add_argument("--source-identity")
    save.add_argument("-l", "--local", action="store_true")

    resume = commands.add_parser("checkpoint-resume")
    resume.add_argument("project_root", type=Path)
    resume.add_argument("flow_root", type=Path)
    resume.add_argument("name")
    resume.add_argument("--source-identity")
    resume.add_argument("-l", "--local", action="store_true")

    args = parser.parse_args(argv)
    try:
        flow_root = (
            local_custom_flow_root(
                args.project_root if hasattr(args, "project_root") else args.flow_root
            )
            if args.local
            else args.flow_root
        )
        flow = load_custom_flow(
            flow_root, args.name, origin="local" if args.local else "shared"
        )
        if args.command == "validate":
            _print_json(
                {
                    "name": flow.name,
                    "origin": flow.origin,
                    "identity": flow.identity,
                    "write_authority": (
                        None if flow.artifact_roles is None else sorted(flow.artifact_roles)
                    ),
                    "steps": [
                        {
                            "number": index,
                            "kind": step.kind,
                            "target": step.target,
                            "arguments": list(step.arguments),
                            "declared_writes": (
                                None
                                if step.declared_writes is None
                                else sorted(step.declared_writes)
                            ),
                        }
                        for index, step in enumerate(flow.steps, start=1)
                    ],
                }
            )
            return 0
        if args.command == "run-script":
            if not 1 <= args.step <= len(flow.steps):
                raise CustomFlowError("invalid_step_number", "script step is outside the flow")
            step = flow.steps[args.step - 1]
            if step.kind != "script":
                raise CustomFlowError("invalid_step_type", "selected step is not a script")
            outcome = _script_executor(
                args.project_root, step, authorized=args.authorized
            ).invoke("")
            _print_json(outcome._asdict())
            return 0 if outcome.status == "completed" else 2
        if args.command == "checkpoint-save":
            path = save_custom_checkpoint(
                args.project_root,
                flow,
                FlowState(args.next_action_index, args.scope, False),
                source_identity=args.source_identity,
            )
            _print_json({"checkpoint": str(path)})
            return 0
        checkpoint = load_custom_checkpoint(args.project_root)
        state = resume_custom_state(
            flow, checkpoint, current_source_identity=args.source_identity
        )
        _print_json(
            {
                "flow": flow.name,
                "next_action_index": state.action_index,
                "scope": state.selected_scope,
            }
        )
        return 0
    except CustomFlowError as error:
        print(
            json.dumps(
                {"error": error.code, "detail": str(error), "line": error.line},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
