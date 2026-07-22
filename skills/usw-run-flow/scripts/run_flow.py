#!/usr/bin/env python3
"""Deterministic one-action orchestration for role and custom USW flows."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
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


CUSTOM_FLOW_VERSION = "1"
STRUCTURED_FLOW_VERSION = "version-2"
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


class LoopPolicy(NamedTuple):
    gate: str
    expected_outcome: str
    max_attempts: int
    exhaustion: str


class CustomStep(NamedTuple):
    kind: str
    target: str
    arguments: tuple[str, ...]
    declared_writes: frozenset[str] | None
    name: str | None = None
    payload: tuple[CustomStep, ...] = ()
    gate_outcomes: tuple[str, ...] = ()
    loop: LoopPolicy | None = None


class CustomFlow(NamedTuple):
    name: str
    steps: tuple[CustomStep, ...]
    artifact_roles: frozenset[str] | None
    origin: str
    identity: str
    version: str = CUSTOM_FLOW_VERSION
    branch_rules: tuple[tuple[str, str, str], ...] = ()

    @property
    def actions(self) -> tuple[str, ...]:
        return tuple(
            step.name or str(index) for index, step in enumerate(self.steps, start=1)
        )

    @property
    def branches(self) -> tuple[tuple[str, str, str], ...]:
        return self.branch_rules


class MarkdownFlow(NamedTuple):
    name: str
    content: str
    path: Path
    origin: str
    identity: str


class MarkdownInvocation(NamedTuple):
    task: str
    flow: MarkdownFlow


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


def _flow_identity(content: str, version: str, origin: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    prefix = "usw-flow-v1" if version == CUSTOM_FLOW_VERSION else "usw-flow-v2"
    return f"{prefix}:{digest}" if origin == "shared" else f"{prefix}:local:{digest}"


def _parse_v1_flow(
    content: str,
    name: str,
    origin: str,
    sections: dict[str, tuple[int, str]],
) -> CustomFlow:
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

    return CustomFlow(
        name,
        tuple(steps),
        artifact_roles,
        origin,
        _flow_identity(content, CUSTOM_FLOW_VERSION, origin),
    )


def _v2_call(text: str, *, line: int) -> tuple[str, str]:
    unknown = re.findall(r"\bCALL\s+([A-Z]+)\b", text)
    allowed = {"SKILL", "SCRIPT", "FLOW", "SUBAGENT", "HUMAN"}
    if any(kind not in allowed for kind in unknown):
        raise CustomFlowError("unsupported_call_type", "unsupported CALL type", line)
    calls = re.findall(
        r"\bCALL (SKILL|SCRIPT|FLOW|SUBAGENT|HUMAN) `([^`]+)`", text
    )
    if len(calls) != 1:
        raise CustomFlowError("invalid_call", "expected exactly one typed CALL", line)
    kind, target = calls[0]
    if kind == "FLOW" and not CUSTOM_FLOW_NAME.fullmatch(target):
        raise CustomFlowError("invalid_flow_name", f"unsafe nested flow name: {target!r}", line)
    return kind.casefold(), target


def _v2_arguments(lines: list[tuple[int, str]], *, kind: str) -> tuple[str, ...]:
    matches = [
        (line, match.group(1))
        for line, source in lines
        if (match := re.fullmatch(r"\s+- Аргументы:\s*(.+)", source))
    ]
    if len(matches) > 1:
        raise CustomFlowError("duplicate_step_field", "duplicate field 'Аргументы'", matches[1][0])
    if not matches:
        return ()
    line, value = matches[0]
    if kind != "script":
        raise CustomFlowError("invalid_step_field", "only SCRIPT accepts arguments", line)
    return _code_values(value, line=line, field="Аргументы")


def _payload_items(
    lines: list[tuple[int, str]], marker_index: int, names: set[str]
) -> tuple[CustomStep, ...]:
    marker_line, marker = lines[marker_index]
    marker_indent = len(marker) - len(marker.lstrip())
    payload_lines = lines[marker_index + 1 :]
    first = next((item for item in payload_lines if item[1].strip()), None)
    if first is None:
        raise CustomFlowError("missing_subagent_payload", "SUBAGENT payload is empty", marker_line)
    first_match = re.fullmatch(r"(\s+)([0-9]+)\. `([^`]+)` — (.+)", first[1])
    if first_match is None or len(first_match.group(1)) <= marker_indent:
        raise CustomFlowError("invalid_subagent_payload", "expected nested numbered actions", first[0])
    item_indent = len(first_match.group(1))
    starts: list[int] = []
    for index, (line, source) in enumerate(payload_lines):
        match = re.fullmatch(r"(\s+)([0-9]+)\. `([^`]+)` — (.+)", source)
        if match and len(match.group(1)) == item_indent:
            starts.append(index)
        elif source.strip() and len(source) - len(source.lstrip()) <= marker_indent:
            raise CustomFlowError("invalid_subagent_payload", "unexpected payload field", line)
    if not starts:
        raise CustomFlowError("missing_subagent_payload", "SUBAGENT payload is empty", marker_line)
    result: list[CustomStep] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(payload_lines)
        line, source = payload_lines[start]
        match = re.fullmatch(r"(\s+)([0-9]+)\. `([^`]+)` — (.+)", source)
        assert match is not None
        number, action_name, headline = match.group(2), match.group(3), match.group(4)
        if int(number) != position + 1:
            raise CustomFlowError("invalid_step_number", "nested steps must be consecutive", line)
        if not CUSTOM_FLOW_NAME.fullmatch(action_name) or action_name in names:
            raise CustomFlowError("invalid_action_name", "action names must be unique kebab-case", line)
        names.add(action_name)
        result.append(
            _parse_v2_call_step(
                action_name, headline, payload_lines[start + 1 : end], line, names
            )
        )
    return tuple(result)


def _parse_v2_call_step(
    name: str,
    headline: str,
    lines: list[tuple[int, str]],
    line: int,
    names: set[str],
) -> CustomStep:
    kind, target = _v2_call(headline, line=line)
    markers = [
        index
        for index, (_source_line, source) in enumerate(lines)
        if re.fullmatch(r"\s+- Действия субагента:", source)
    ]
    arguments = _v2_arguments(
        lines[: markers[0]] if markers else lines,
        kind=kind,
    )
    if kind == "subagent":
        if len(markers) != 1:
            raise CustomFlowError("missing_subagent_payload", "SUBAGENT requires one payload", line)
        payload = _payload_items(lines, markers[0], names)
    else:
        if markers:
            raise CustomFlowError("invalid_subagent_payload", "only SUBAGENT accepts nested actions", lines[markers[0]][0])
        payload = ()
    return CustomStep(kind, target, arguments, None, name, payload)


def _parse_v2_flow(
    content: str,
    name: str,
    origin: str,
    sections: dict[str, tuple[int, str]],
) -> CustomFlow:
    if "Полномочия записи" in sections:
        raise CustomFlowError(
            "unsupported_write_metadata",
            "version-2 does not accept write authority",
            sections["Полномочия записи"][0],
        )
    actions_line, actions = sections["Порядок действий"]
    sources = actions.splitlines()
    starts = [index for index, source in enumerate(sources) if re.fullmatch(r"[0-9]+\. `[^`]+` — .+", source)]
    if not starts:
        raise CustomFlowError("missing_steps", "flow must contain at least one action", actions_line)
    first_nonempty = next(index for index, source in enumerate(sources) if source.strip())
    if starts[0] != first_nonempty:
        raise CustomFlowError("invalid_step", "expected a named top-level action", actions_line + first_nonempty + 1)

    names: set[str] = set()
    steps: list[CustomStep] = []
    branches: list[tuple[str, str, str]] = []
    gates: dict[str, tuple[str, ...]] = {}
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(sources)
        line = actions_line + start + 1
        match = re.fullmatch(r"([0-9]+)\. `([^`]+)` — (.+)", sources[start])
        assert match is not None
        number, action_name, headline = match.groups()
        if int(number) != position + 1:
            raise CustomFlowError("invalid_step_number", "steps must be numbered consecutively", line)
        if not CUSTOM_FLOW_NAME.fullmatch(action_name) or action_name in names:
            raise CustomFlowError("invalid_action_name", "action names must be unique kebab-case", line)
        names.add(action_name)
        block = [(actions_line + index + 1, sources[index]) for index in range(start + 1, end)]

        if "PARALLEL" in headline:
            if headline.strip() != "PARALLEL:":
                raise CustomFlowError("invalid_parallel", "expected canonical PARALLEL block", line)
            child_starts = [
                index
                for index, (_child_line, source) in enumerate(block)
                if re.fullmatch(r"   - `[^`]+` — .+", source)
            ]
            if len(child_starts) < 2:
                raise CustomFlowError("invalid_parallel", "PARALLEL requires at least two children", line)
            children: list[CustomStep] = []
            for child_position, child_start in enumerate(child_starts):
                child_end = child_starts[child_position + 1] if child_position + 1 < len(child_starts) else len(block)
                child_line, child_source = block[child_start]
                child_match = re.fullmatch(r"   - `([^`]+)` — (.+)", child_source)
                assert child_match is not None
                child_name, child_headline = child_match.groups()
                if not CUSTOM_FLOW_NAME.fullmatch(child_name) or child_name in names:
                    raise CustomFlowError("invalid_action_name", "action names must be unique kebab-case", child_line)
                names.add(child_name)
                children.append(
                    _parse_v2_call_step(
                        child_name,
                        child_headline,
                        block[child_start + 1 : child_end],
                        child_line,
                        names,
                    )
                )
            steps.append(CustomStep("parallel", action_name, (), None, action_name, tuple(children)))
            continue

        if "LOOP" in headline:
            loop_match = re.fullmatch(
                r"LOOP не более ([1-9][0-9]*) попыт\w*, пока `([^`]+)` не вернёт `([^`]+)`\.",
                headline,
            )
            if loop_match is None:
                raise CustomFlowError("invalid_loop", "expected a bounded canonical LOOP", line)
            maximum, gate, expected = loop_match.groups()
            attempt = [item for item in block if re.fullmatch(r"   - Каждая попытка .+CALL .+", item[1])]
            returns = [item for item in block if re.fullmatch(r"   - После попытки: снова `[^`]+`\.", item[1])]
            exhausted = [item for item in block if re.fullmatch(r"   - При исчерпании: .+", item[1])]
            if len(attempt) != 1 or len(returns) != 1 or len(exhausted) != 1:
                raise CustomFlowError("invalid_loop", "LOOP requires attempt, return, and exhaustion fields", line)
            return_target = re.search(r"`([^`]+)`", returns[0][1])
            assert return_target is not None
            if return_target.group(1) != gate:
                raise CustomFlowError("invalid_loop", "LOOP return must target its gate", returns[0][0])
            kind, target = _v2_call(attempt[0][1], line=attempt[0][0])
            if kind == "subagent":
                raise CustomFlowError(
                    "invalid_loop",
                    "SUBAGENT loop attempts require an explicit payload block",
                    attempt[0][0],
                )
            arguments = _v2_arguments(block, kind=kind)
            exhaustion = exhausted[0][1].split(":", 1)[1].strip()
            steps.append(
                CustomStep(
                    kind,
                    target,
                    arguments,
                    None,
                    action_name,
                    (),
                    (),
                    LoopPolicy(gate, expected, int(maximum), exhaustion),
                )
            )
            continue

        if "GATE" in headline:
            gate_match = re.fullmatch(
                r"(.*CALL HUMAN `[^`]+`); GATE: (.+)", headline
            )
            if gate_match is None:
                raise CustomFlowError("invalid_gate", "GATE must use CALL HUMAN", line)
            kind, target = _v2_call(gate_match.group(1), line=line)
            outcomes = tuple(re.findall(r"`([^`]+)`", gate_match.group(2)))
            if len(outcomes) < 2 or len(set(outcomes)) != len(outcomes):
                raise CustomFlowError("invalid_gate", "GATE requires unique finite outcomes", line)
            routes: dict[str, str] = {}
            has_else = False
            for child_line, source in block:
                route = re.fullmatch(
                    r"   - (IF|ELIF) `([^`]+)`: продолжить (?:к|LOOP) `([^`]+)`\.", source
                )
                if route:
                    outcome, destination = route.group(2), route.group(3)
                    if outcome in routes:
                        raise CustomFlowError("invalid_gate", "duplicate gate outcome", child_line)
                    routes[outcome] = destination
                elif re.fullmatch(r"   - ELSE: .+", source):
                    has_else = True
                elif source.strip():
                    raise CustomFlowError("invalid_gate", "unexpected GATE field", child_line)
            if set(routes) != set(outcomes) or not has_else:
                raise CustomFlowError("invalid_gate", "GATE requires complete routes and ELSE", line)
            branches.extend((action_name, outcome, routes[outcome]) for outcome in outcomes)
            gates[action_name] = outcomes
            steps.append(CustomStep(kind, target, (), None, action_name, (), outcomes))
            continue

        if any(marker in headline for marker in ("IF", "ELIF", "ELSE")):
            raise CustomFlowError("invalid_control", "control marker is outside its block", line)
        steps.append(_parse_v2_call_step(action_name, headline, block, line, names))

    top_names = {step.name for step in steps}
    for _source, _outcome, target in branches:
        if target not in top_names:
            raise CustomFlowError("unknown_action", f"unknown branch target: {target}")
    for step in steps:
        if step.loop is None:
            continue
        gate_outcomes = gates.get(step.loop.gate)
        if gate_outcomes is None or step.loop.expected_outcome not in gate_outcomes:
            raise CustomFlowError("invalid_loop", "LOOP must reference an existing compatible GATE")
        if not any(source == step.loop.gate and target == step.name for source, _outcome, target in branches):
            raise CustomFlowError("invalid_loop", "GATE must route an outcome to its LOOP")

    return CustomFlow(
        name,
        tuple(steps),
        None,
        origin,
        _flow_identity(content, STRUCTURED_FLOW_VERSION, origin),
        STRUCTURED_FLOW_VERSION,
        tuple(branches),
    )


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
    missing = [section for section in REQUIRED_CUSTOM_SECTIONS if section not in sections]
    if missing:
        raise CustomFlowError("missing_section", f"missing sections: {', '.join(missing)}")
    positions = [sections[section][0] for section in REQUIRED_CUSTOM_SECTIONS]
    if positions != sorted(positions):
        raise CustomFlowError("invalid_section_order", "required sections are out of order")
    contract_line, contract = sections["Контракт"]
    versions = re.findall(r"^- Версия: `([^`]+)`$", contract, re.MULTILINE)
    if versions == [CUSTOM_FLOW_VERSION]:
        for forbidden in ("Branches", "Ветвления", "Переходы"):
            if forbidden in sections:
                raise CustomFlowError("unsupported_branch", "custom flows are linear", sections[forbidden][0])
        return _parse_v1_flow(content, name, origin, sections)
    if versions == [STRUCTURED_FLOW_VERSION]:
        return _parse_v2_flow(content, name, origin, sections)
    raise CustomFlowError(
        "unsupported_flow_schema",
        f"expected exactly one version {CUSTOM_FLOW_VERSION} or {STRUCTURED_FLOW_VERSION}",
        contract_line,
    )


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


def load_markdown_flow(
    flow_root: Path, name: str, *, origin: str = "shared"
) -> MarkdownFlow:
    """Load any named Markdown flow without interpreting its contents."""
    if not CUSTOM_FLOW_NAME.fullmatch(name):
        raise CustomFlowError("invalid_flow_name", f"unsafe flow name: {name!r}")
    if origin not in CUSTOM_FLOW_ORIGINS:
        raise CustomFlowError("invalid_flow_origin", f"unsupported flow origin: {origin!r}")
    try:
        root_mode = os.lstat(flow_root).st_mode
    except FileNotFoundError as error:
        raise CustomFlowError(
            "missing_flow_root", f"Markdown flow root is missing: {flow_root}"
        ) from error
    if not stat.S_ISDIR(root_mode) or stat.S_ISLNK(root_mode):
        raise CustomFlowError(
            "invalid_flow_root", f"unsafe Markdown flow root: {flow_root}"
        )
    path = flow_root / f"{name}.md"
    try:
        mode = os.lstat(path).st_mode
    except FileNotFoundError as error:
        raise CustomFlowError("missing_flow", f"Markdown flow is missing: {path}") from error
    if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
        raise CustomFlowError("invalid_flow_file", f"Markdown flow is not a regular file: {path}")
    content = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return MarkdownFlow(
        name,
        content,
        path,
        origin,
        f"usw-markdown:{origin}:{digest}",
    )


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


def resolve_markdown_flow(
    project_root: Path,
    shared_root: Path,
    name: str,
    *,
    origin: str | None = None,
) -> MarkdownFlow:
    """Resolve a Markdown flow with local-first default precedence."""
    if origin not in {None, *CUSTOM_FLOW_ORIGINS}:
        raise CustomFlowError("invalid_flow_origin", f"unsupported flow origin: {origin!r}")
    if origin in {None, "local"}:
        try:
            local_root = local_custom_flow_root(project_root)
            return load_markdown_flow(local_root, name, origin="local")
        except CustomFlowError as error:
            if origin == "local" or error.code not in {
                "missing_local_state",
                "missing_flow_root",
                "missing_flow",
            }:
                raise
    return load_markdown_flow(shared_root, name, origin="shared")


def prepare_markdown_run(
    project_root: Path,
    shared_root: Path,
    name: str,
    task: str,
    *,
    origin: str | None = None,
) -> MarkdownInvocation:
    """Prepare the default task + Markdown invocation without strict parsing."""
    if not isinstance(task, str) or not task.strip():
        raise CustomFlowError("missing_task", "Markdown flow task must be non-empty")
    return MarkdownInvocation(
        task,
        resolve_markdown_flow(project_root, shared_root, name, origin=origin),
    )


class ActionOutcome(NamedTuple):
    status: str
    outcome: str
    written_roles: frozenset[str] = frozenset()
    output_references: tuple[str, ...] = ()
    detail: str | None = None
    children: tuple[tuple[str, ActionOutcome], ...] = ()


def run_markdown_flow(
    invocation: MarkdownInvocation,
    executor: Callable[[MarkdownInvocation], ActionOutcome],
) -> ActionOutcome:
    """Run one default Markdown operation boundary through a generic executor."""
    return executor(invocation)


class Executor(NamedTuple):
    declared_writes: frozenset[str]
    invoke: Callable[[str], ActionOutcome]
    available: bool = True
    is_stub: bool = False


class CallInvocation(NamedTuple):
    action: str
    kind: str
    target: str
    scope: str
    arguments: tuple[str, ...] = ()
    payload: tuple[CustomStep, ...] = ()
    input: str | None = None
    results: tuple[tuple[str, ActionOutcome], ...] = ()
    task: str | None = None


class TypedExecutor(NamedTuple):
    declared_writes: frozenset[str]
    invoke: Callable[[CallInvocation], ActionOutcome]
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
    typed_executors: Mapping[tuple[str, str], TypedExecutor] | None = None,
    action_inputs: Mapping[str, str] | None = None,
    completed_results: tuple[tuple[str, ActionOutcome], ...] = (),
    task: str | None = None,
    script_permissions: frozenset[str] = frozenset(),
    script_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Executor]:
    """Resolve every custom step before the first executor can mutate state."""
    typed_executors = typed_executors or {}
    action_inputs = action_inputs or {}

    def resolve(step: CustomStep) -> Executor:
        if step.kind == "parallel":
            children = tuple(resolve(child) for child in step.payload)
            child_names = tuple(child.name or child.target for child in step.payload)

            def invoke_parallel(scope: str) -> ActionOutcome:
                with ThreadPoolExecutor(max_workers=len(children)) as pool:
                    futures = [pool.submit(executor.invoke, scope) for executor in children]
                    outcomes: list[ActionOutcome] = []
                    for future in futures:
                        try:
                            outcomes.append(future.result())
                        except Exception as error:  # executor boundary
                            outcomes.append(
                                ActionOutcome("failed", "parallel_child_failed", detail=str(error))
                            )
                written = frozenset().union(*(outcome.written_roles for outcome in outcomes))
                references = tuple(
                    reference
                    for outcome in outcomes
                    for reference in outcome.output_references
                )
                named_outcomes = tuple(zip(child_names, outcomes))
                violation = next(
                    (
                        outcome
                        for executor, outcome in zip(children, outcomes)
                        if outcome.written_roles - executor.declared_writes
                    ),
                    None,
                )
                if violation:
                    return ActionOutcome(
                        "failed",
                        "executor_contract_violation",
                        written,
                        references,
                        "A parallel child reported undeclared writes.",
                        named_outcomes,
                    )
                failed = next(
                    (outcome for outcome in outcomes if outcome.status != "completed"),
                    None,
                )
                if failed:
                    return ActionOutcome(
                        failed.status,
                        failed.outcome,
                        written,
                        references,
                        failed.detail,
                        named_outcomes,
                    )
                return ActionOutcome(
                    "completed",
                    "parallel_completed",
                    written,
                    references,
                    children=named_outcomes,
                )

            return Executor(
                frozenset().union(*(executor.declared_writes for executor in children)),
                invoke_parallel,
                all(executor.available for executor in children),
                any(executor.is_stub for executor in children),
            )

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
            return executor

        if step.kind == "script":
            return _script_executor(
                project_root,
                step,
                authorized=step.target in script_permissions,
                runner=script_runner,
            )

        executor = typed_executors.get((step.kind, step.target))
        if executor is None or not executor.available:
            raise CustomFlowError(
                "missing_executor",
                f"{step.kind} executor is unavailable: {step.target}",
            )
        for child in step.payload:
            resolve(child)

        def invoke_typed(scope: str) -> ActionOutcome:
            return executor.invoke(
                CallInvocation(
                    step.name or step.target,
                    step.kind,
                    step.target,
                    scope,
                    step.arguments,
                    step.payload,
                    action_inputs.get(step.name or step.target),
                    completed_results,
                    task,
                )
            )

        return Executor(
            executor.declared_writes,
            invoke_typed,
            executor.available,
            executor.is_stub,
        )

    resolved: dict[str, Executor] = {}
    for action, step in zip(flow.actions, flow.steps):
        resolved[action] = resolve(step)
    return resolved


class FlowState(NamedTuple):
    action_index: int = 0
    selected_scope: str | None = None
    stopped: bool = False
    loop_counts: tuple[tuple[str, int], ...] = ()
    action_inputs: tuple[tuple[str, str], ...] = ()
    results: tuple[tuple[str, ActionOutcome], ...] = ()


class CustomFlowCheckpoint(NamedTuple):
    schema_version: int
    flow_name: str
    flow_identity: str
    selected_scope: str
    next_action_index: int
    source_identity: str | None
    loop_counts: tuple[tuple[str, int], ...] = ()
    action_inputs: tuple[tuple[str, str], ...] = ()
    results: tuple[tuple[str, ActionOutcome], ...] = ()


def _input_action_names(steps: tuple[CustomStep, ...]) -> tuple[str, ...]:
    names: list[str] = []
    for step in steps:
        if step.name is not None and step.kind in {"human", "subagent", "flow"}:
            names.append(step.name)
        names.extend(_input_action_names(step.payload))
    return tuple(names)


def _bind_action_inputs(
    flow: CustomFlow,
    state: FlowState,
    supplied: Mapping[str, str] | None,
) -> FlowState:
    if flow.version != STRUCTURED_FLOW_VERSION:
        if state.action_inputs or supplied:
            raise CustomFlowError(
                "unsupported_binding", "action inputs require flow version-2"
            )
        return state
    names = _input_action_names(flow.steps)
    known = frozenset(names)
    if supplied is None:
        inputs = state.action_inputs
    else:
        if any(
            not isinstance(name, str) or not isinstance(value, str)
            for name, value in supplied.items()
        ):
            raise CustomFlowError(
                "invalid_action_input", "action inputs must map names to Markdown strings"
            )
        unknown = set(supplied) - known
        if unknown:
            raise CustomFlowError(
                "unknown_action_input",
                f"unknown action input: {sorted(unknown)[0]}",
            )
        normalized = tuple((name, supplied[name]) for name in names if name in supplied)
        if state.action_inputs and normalized != state.action_inputs:
            raise CustomFlowError(
                "stale_action_input", "action inputs changed after flow start"
            )
        if not state.action_inputs and (state.action_index or state.results) and normalized:
            raise CustomFlowError(
                "late_action_input", "action inputs must be bound before the first action"
            )
        inputs = state.action_inputs or normalized
    if (
        len({name for name, _value in inputs}) != len(inputs)
        or any(
            name not in known or not isinstance(value, str)
            for name, value in inputs
        )
    ):
        raise CustomFlowError(
            "unknown_action_input", "state contains an invalid action input"
        )
    return state._replace(action_inputs=inputs)


def _validated_results(
    flow: CustomFlow, results: tuple[tuple[str, ActionOutcome], ...]
) -> tuple[tuple[str, ActionOutcome], ...]:
    steps = {step.name: step for step in flow.steps}
    known = frozenset(steps)
    names = tuple(name for name, _outcome in results)
    if len(set(names)) != len(names) or any(name not in known for name in names):
        raise CustomFlowError("invalid_bound_result", "invalid completed result names")
    if any(outcome.status != "completed" for _name, outcome in results):
        raise CustomFlowError("invalid_bound_result", "only completed results may be bound")
    for name, outcome in results:
        expected_children = (
            tuple(child.name for child in steps[name].payload)
            if steps[name].kind == "parallel"
            else ()
        )
        if tuple(child_name for child_name, _child in outcome.children) != expected_children:
            raise CustomFlowError(
                "invalid_bound_result", "bound child results do not match flow"
            )
        if any(child.status != "completed" for _child_name, child in outcome.children):
            raise CustomFlowError(
                "invalid_bound_result", "only completed child results may be bound"
            )
    by_name = dict(results)
    return tuple((name, by_name[name]) for name in flow.actions if name in by_name)


def _record_result(
    flow: CustomFlow, state: FlowState, action: str, outcome: ActionOutcome
) -> FlowState:
    if flow.version != STRUCTURED_FLOW_VERSION:
        return state
    results = dict(state.results)
    results[action] = outcome
    return state._replace(
        results=tuple((name, results[name]) for name in flow.actions if name in results)
    )


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


def _outcome_data(outcome: ActionOutcome) -> dict[str, object]:
    return {
        "status": outcome.status,
        "outcome": outcome.outcome,
        "written_roles": sorted(outcome.written_roles),
        "output_references": list(outcome.output_references),
        "detail": outcome.detail,
        "children": [
            [name, _outcome_data(child)] for name, child in outcome.children
        ],
    }


def _outcome_from_data(value: object) -> ActionOutcome:
    expected = {
        "status",
        "outcome",
        "written_roles",
        "output_references",
        "detail",
        "children",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise CustomFlowError("invalid_checkpoint", "invalid bound result")
    written = value["written_roles"]
    references = value["output_references"]
    children = value["children"]
    if (
        not isinstance(value["status"], str)
        or not isinstance(value["outcome"], str)
        or not isinstance(written, list)
        or any(not isinstance(item, str) for item in written)
        or len(set(written)) != len(written)
        or not isinstance(references, list)
        or any(not isinstance(item, str) for item in references)
        or (value["detail"] is not None and not isinstance(value["detail"], str))
        or not isinstance(children, list)
    ):
        raise CustomFlowError("invalid_checkpoint", "invalid bound result")
    parsed_children: list[tuple[str, ActionOutcome]] = []
    for item in children:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not CUSTOM_FLOW_NAME.fullmatch(item[0])
        ):
            raise CustomFlowError("invalid_checkpoint", "invalid child result")
        parsed_children.append((item[0], _outcome_from_data(item[1])))
    if len({name for name, _child in parsed_children}) != len(parsed_children):
        raise CustomFlowError("invalid_checkpoint", "duplicate child result")
    return ActionOutcome(
        value["status"],
        value["outcome"],
        frozenset(written),
        tuple(references),
        value["detail"],
        tuple(parsed_children),
    )


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
    state = _bind_action_inputs(flow, state, None)
    results = _validated_results(flow, state.results)
    loop_limits = {
        step.name: step.loop.max_attempts
        for step in flow.steps
        if step.loop is not None and step.name is not None
    }
    if any(
        name not in loop_limits or count < 0 or count > loop_limits[name]
        for name, count in state.loop_counts
    ) or (flow.version == CUSTOM_FLOW_VERSION and state.loop_counts):
        raise CustomFlowError("invalid_checkpoint", "invalid loop counters for flow")
    path = _custom_checkpoint_path(project_root)
    schema_version = (
        3
        if flow.version == STRUCTURED_FLOW_VERSION
        and (state.action_inputs or results)
        else 2
        if flow.version == STRUCTURED_FLOW_VERSION
        else 1
    )
    payload: dict[str, object] = {
        "schema_version": schema_version,
        "flow_name": flow.name,
        "flow_identity": flow.identity,
        "selected_scope": state.selected_scope,
        "next_action_index": state.action_index,
        "source_identity": source_identity,
    }
    if schema_version in {2, 3}:
        payload["loop_counts"] = [list(item) for item in state.loop_counts]
    if schema_version == 3:
        payload["action_inputs"] = [list(item) for item in state.action_inputs]
        payload["results"] = [
            [name, _outcome_data(outcome)] for name, outcome in results
        ]
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
    if not isinstance(data, dict) or data.get("schema_version") not in {1, 2, 3}:
        raise CustomFlowError("invalid_checkpoint", "invalid checkpoint values")
    if data["schema_version"] in {2, 3}:
        expected.add("loop_counts")
    if data["schema_version"] == 3:
        expected.update(("action_inputs", "results"))
    if set(data) != expected:
        raise CustomFlowError("invalid_checkpoint", "unexpected checkpoint fields")
    if (
        not isinstance(data["flow_name"], str)
        or not isinstance(data["flow_identity"], str)
        or not isinstance(data["selected_scope"], str)
        or not isinstance(data["next_action_index"], int)
        or (data["source_identity"] is not None and not isinstance(data["source_identity"], str))
    ):
        raise CustomFlowError("invalid_checkpoint", "invalid checkpoint values")
    loop_counts: tuple[tuple[str, int], ...] = ()
    if data["schema_version"] in {2, 3}:
        raw_counts = data["loop_counts"]
        if (
            not isinstance(raw_counts, list)
            or any(
                not isinstance(item, list)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not isinstance(item[1], int)
                or item[1] < 0
                for item in raw_counts
            )
            or len({item[0] for item in raw_counts}) != len(raw_counts)
        ):
            raise CustomFlowError("invalid_checkpoint", "invalid loop counters")
        loop_counts = tuple((item[0], item[1]) for item in raw_counts)
    action_inputs: tuple[tuple[str, str], ...] = ()
    results: tuple[tuple[str, ActionOutcome], ...] = ()
    if data["schema_version"] == 3:
        raw_inputs = data["action_inputs"]
        raw_results = data["results"]
        if (
            not isinstance(raw_inputs, list)
            or any(
                not isinstance(item, list)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not isinstance(item[1], str)
                for item in raw_inputs
            )
            or len({item[0] for item in raw_inputs}) != len(raw_inputs)
            or not isinstance(raw_results, list)
            or any(
                not isinstance(item, list)
                or len(item) != 2
                or not isinstance(item[0], str)
                for item in raw_results
            )
            or len({item[0] for item in raw_results}) != len(raw_results)
        ):
            raise CustomFlowError("invalid_checkpoint", "invalid binding state")
        action_inputs = tuple((item[0], item[1]) for item in raw_inputs)
        results = tuple(
            (item[0], _outcome_from_data(item[1])) for item in raw_results
        )
    return CustomFlowCheckpoint(
        data["schema_version"],
        data["flow_name"],
        data["flow_identity"],
        data["selected_scope"],
        data["next_action_index"],
        data["source_identity"],
        loop_counts,
        action_inputs,
        results,
    )


def resume_custom_state(
    flow: CustomFlow,
    checkpoint: CustomFlowCheckpoint,
    *,
    current_source_identity: str | None,
) -> FlowState:
    if checkpoint.flow_name != flow.name or checkpoint.flow_identity != flow.identity:
        raise CustomFlowError("stale_flow", "flow changed after the checkpoint was saved")
    expected_schemas = (
        {2, 3} if flow.version == STRUCTURED_FLOW_VERSION else {1}
    )
    if checkpoint.schema_version not in expected_schemas:
        raise CustomFlowError("invalid_checkpoint", "checkpoint schema does not match flow version")
    if not 0 <= checkpoint.next_action_index <= len(flow.steps):
        raise CustomFlowError("invalid_checkpoint", "next action index is outside the flow")
    if checkpoint.source_identity is not None:
        if current_source_identity is None:
            raise CustomFlowError("unknown_source_context", "current source identity is unavailable")
        if checkpoint.source_identity != current_source_identity:
            raise CustomFlowError("stale_source_context", "product source changed after checkpoint")
    if flow.version == STRUCTURED_FLOW_VERSION:
        loop_limits = {
            step.name: step.loop.max_attempts
            for step in flow.steps
            if step.loop is not None and step.name is not None
        }
        if any(
            name not in loop_limits or count > loop_limits[name]
            for name, count in checkpoint.loop_counts
        ):
            raise CustomFlowError("invalid_checkpoint", "invalid loop counters for flow")
    state = FlowState(
        checkpoint.next_action_index,
        checkpoint.selected_scope,
        False,
        checkpoint.loop_counts,
        checkpoint.action_inputs,
        checkpoint.results,
    )
    state = _bind_action_inputs(flow, state, None)
    return state._replace(results=_validated_results(flow, state.results))


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


def _next_state(
    previous: FlowState, action_index: int, scope: str, stopped: bool
) -> FlowState:
    return previous._replace(
        action_index=action_index,
        selected_scope=scope,
        stopped=stopped,
    )


def _loop_count(state: FlowState, action: str) -> int:
    return dict(state.loop_counts).get(action, 0)


def _increment_loop(state: FlowState, action: str) -> tuple[tuple[str, int], ...]:
    counts = dict(state.loop_counts)
    counts[action] = counts.get(action, 0) + 1
    return tuple(sorted(counts.items()))


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
        complete = _next_state(state, state.action_index, scope, True)
        return FlowResult(complete, "completed", None, (), "scope_complete", "Report the scoped result.")

    action = scenario.actions[state.action_index]
    step = (
        scenario.steps[state.action_index]
        if getattr(scenario, "version", CUSTOM_FLOW_VERSION) == STRUCTURED_FLOW_VERSION
        else None
    )
    if step is not None and step.loop is not None and _loop_count(state, action) >= step.loop.max_attempts:
        return FlowResult(
            _next_state(state, state.action_index, scope, True),
            "decision_required",
            action,
            (),
            "loop_exhausted",
            step.loop.exhaustion,
        )
    executor = executors.get(action)
    if executor is None or not executor.available or (executor.is_stub and not allow_stubs):
        return FlowResult(
            _next_state(state, state.action_index, scope, False),
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
            _next_state(state, state.action_index, scope, False),
            "blocked",
            action,
            (),
            "authority_mismatch",
            "Use an executor whose declared writes fit scenario authority.",
        )

    outcome = executor.invoke(scope)
    if outcome.written_roles - executor.declared_writes or outcome.written_roles - artifact_roles:
        return FlowResult(
            _next_state(state, state.action_index, scope, True),
            "failed",
            action,
            outcome.output_references,
            "executor_contract_violation",
            "Inspect the executor; it reported undeclared writes.",
        )
    if outcome.status != "completed":
        return FlowResult(
            _next_state(state, state.action_index, scope, True),
            outcome.status,
            action,
            outcome.output_references,
            outcome.outcome,
            outcome.detail or "Resolve the reported boundary before continuing.",
        )

    if step is not None and step.gate_outcomes and outcome.outcome not in step.gate_outcomes:
        return FlowResult(
            _next_state(state, state.action_index, scope, True),
            "decision_required",
            action,
            outcome.output_references,
            "unknown_gate_outcome",
            f"Choose one declared outcome: {', '.join(step.gate_outcomes)}.",
        )

    target = _branch_target(scenario, action, outcome.outcome)
    if target and target.startswith("stop:"):
        reason = target.removeprefix("stop:")
        completed_state = _next_state(state, state.action_index, scope, True)
        if step is not None:
            completed_state = _record_result(scenario, completed_state, action, outcome)
        return FlowResult(
            completed_state,
            "completed" if reason in {"scope-complete", "delivery"} else "stopped",
            action,
            outcome.output_references,
            reason,
            "Report the scoped result." if reason in {"scope-complete", "delivery"} else "Resolve the stop condition.",
        )
    if step is not None and step.loop is not None:
        next_index = scenario.actions.index(step.loop.gate)
        next_state = state._replace(
            action_index=next_index,
            selected_scope=scope,
            stopped=False,
            loop_counts=_increment_loop(state, action),
        )
    else:
        next_index = scenario.actions.index(target) if target else state.action_index + 1
        next_state = _next_state(state, next_index, scope, False)
    if step is not None:
        next_state = _record_result(scenario, next_state, action, outcome)
    return FlowResult(
        next_state,
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
    typed_executors: Mapping[tuple[str, str], TypedExecutor] | None = None,
    action_inputs: Mapping[str, str] | None = None,
    task: str | None = None,
    script_permissions: frozenset[str] = frozenset(),
    script_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> FlowResult:
    state = _bind_action_inputs(flow, state, action_inputs)
    completed_results = _validated_results(flow, state.results)
    executors = resolve_custom_executors(
        flow,
        skill_executors,
        project_root=project_root,
        typed_executors=typed_executors,
        action_inputs=dict(state.action_inputs),
        completed_results=completed_results,
        task=task,
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


def _step_report(step: CustomStep, number: int) -> dict[str, object]:
    return {
        "number": number,
        "name": step.name,
        "kind": step.kind,
        "target": step.target,
        "arguments": list(step.arguments),
        "declared_writes": (
            None if step.declared_writes is None else sorted(step.declared_writes)
        ),
        "gate_outcomes": list(step.gate_outcomes),
        "loop": None
        if step.loop is None
        else {
            "gate": step.loop.gate,
            "expected_outcome": step.loop.expected_outcome,
            "max_attempts": step.loop.max_attempts,
            "exhaustion": step.loop.exhaustion,
        },
        "payload": [
            _step_report(child, index)
            for index, child in enumerate(step.payload, start=1)
        ],
    }


def _cli_loop_counts(values: list[str]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for value in values:
        match = re.fullmatch(r"([a-z0-9]+(?:-[a-z0-9]+)*)=([0-9]+)", value)
        if match is None or match.group(1) in counts:
            raise CustomFlowError(
                "invalid_checkpoint", "loop count must be a unique NAME=COUNT"
            )
        counts[match.group(1)] = int(match.group(2))
    return tuple(sorted(counts.items()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and support custom USW flows")
    commands = parser.add_subparsers(dest="command", required=True)

    resolve = commands.add_parser("resolve")
    resolve.add_argument("project_root", type=Path)
    resolve.add_argument("shared_root", type=Path)
    resolve.add_argument("name")
    resolve.add_argument("task")
    resolve.add_argument("--origin", choices=sorted(CUSTOM_FLOW_ORIGINS))

    validate = commands.add_parser("validate")
    validate.add_argument("flow_root", type=Path)
    validate.add_argument("name")
    validate.add_argument("-l", "--local", action="store_true")
    validate.add_argument("--experimental-structured", action="store_true")

    run_script = commands.add_parser("run-script")
    run_script.add_argument("project_root", type=Path)
    run_script.add_argument("flow_root", type=Path)
    run_script.add_argument("name")
    run_script.add_argument("step", type=int)
    run_script.add_argument("--authorized", action="store_true")
    run_script.add_argument("-l", "--local", action="store_true")
    run_script.add_argument("--experimental-structured", action="store_true")

    save = commands.add_parser("checkpoint-save")
    save.add_argument("project_root", type=Path)
    save.add_argument("flow_root", type=Path)
    save.add_argument("name")
    save.add_argument("next_action_index", type=int)
    save.add_argument("scope")
    save.add_argument("--source-identity")
    save.add_argument("--loop-count", action="append", default=[])
    save.add_argument("-l", "--local", action="store_true")
    save.add_argument("--experimental-structured", action="store_true")

    resume = commands.add_parser("checkpoint-resume")
    resume.add_argument("project_root", type=Path)
    resume.add_argument("flow_root", type=Path)
    resume.add_argument("name")
    resume.add_argument("--source-identity")
    resume.add_argument("-l", "--local", action="store_true")
    resume.add_argument("--experimental-structured", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "resolve":
            invocation = prepare_markdown_run(
                args.project_root,
                args.shared_root,
                args.name,
                args.task,
                origin=args.origin,
            )
            _print_json(
                {
                    "name": invocation.flow.name,
                    "origin": invocation.flow.origin,
                    "identity": invocation.flow.identity,
                    "path": str(invocation.flow.path),
                    "task": invocation.task,
                }
            )
            return 0
        if not args.experimental_structured:
            raise CustomFlowError(
                "experimental_opt_in_required",
                "strict v1/v2 runtime requires --experimental-structured",
            )
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
                    "version": flow.version,
                    "origin": flow.origin,
                    "identity": flow.identity,
                    "write_authority": (
                        None if flow.artifact_roles is None else sorted(flow.artifact_roles)
                    ),
                    "branches": [list(branch) for branch in flow.branches],
                    "steps": [
                        _step_report(step, index)
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
                FlowState(
                    args.next_action_index,
                    args.scope,
                    False,
                    _cli_loop_counts(args.loop_count),
                ),
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
                "loop_counts": dict(state.loop_counts),
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
