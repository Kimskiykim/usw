#!/usr/bin/env python3
"""Persistent one-case-at-a-time state transitions for usw-refine-task."""

from __future__ import annotations

import re
import runpy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, NamedTuple


INIT_SCRIPT = Path(__file__).parents[2] / "usw-initialize-project/scripts/init_usw.py"
CONFIG = SimpleNamespace(**runpy.run_path(str(INIT_SCRIPT)))
ASSET_ROOT = Path(__file__).parents[1] / "assets"
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class RefinementError(ValueError):
    pass


class DecisionCase(NamedTuple):
    case_id: str
    title: str
    problem: str
    impact: str
    options: tuple[str, ...]
    recommendation: str


class TurnResult(NamedTuple):
    status: str
    current_case: str | None
    paths: tuple[str, ...]


def refinement_root(project: Path) -> Path:
    root = CONFIG.find_project_root(project)
    config = CONFIG.load_config(root)
    return root / config.refinement_root


def _now(timestamp: datetime | None) -> str:
    return (timestamp or datetime.now(timezone.utc)).isoformat(timespec="seconds")


def _validate_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value):
        raise RefinementError(f"unsafe {label}: {value!r}")
    return value


def _render_asset(name: str, **values: str) -> str:
    template = (ASSET_ROOT / name).read_text(encoding="utf-8")
    return re.sub(
        r"{{([^}]+)}}", lambda match: values.get(match.group(1), "None."), template
    )


def start_or_resume(
    project: Path,
    *,
    refinement_id: str,
    title: str,
    goal: str,
    target: str,
    cases: Iterable[DecisionCase],
    timestamp: datetime | None = None,
) -> TurnResult:
    _validate_id(refinement_id, "refinement ID")
    case_list = tuple(cases)
    if not case_list:
        raise RefinementError("at least one decision case is required")
    for case in case_list:
        _validate_id(case.case_id, "case ID")
        if len(case.options) not in {2, 3}:
            raise RefinementError("each case requires two or three options")
    directory = refinement_root(project) / refinement_id
    session = directory / "session.md"
    decisions = directory / "decisions.md"
    if session.exists():
        content = session.read_text(encoding="utf-8")
        if f"- ID: `{refinement_id}`" not in content or f"\n{goal}\n" not in content:
            raise RefinementError("existing refinement ID has a different goal")
        current = re.search(r"^- Current case: `([^`]+)`", content, re.MULTILINE)
        return TurnResult("resumed", current.group(1) if current else None, (session.as_posix(), decisions.as_posix()))
    directory.mkdir(parents=True, exist_ok=False)
    current = case_list[0]
    case_rows = "\n".join(f"- [ ] `{case.case_id}` — {case.title}" for case in case_list)
    content = _render_asset(
        "session.md", title=title, refinement_id=refinement_id,
        updated_at=_now(timestamp), target_or_none=target,
        current_case_id=current.case_id, goal=goal, case_rows=case_rows,
        current_case_title=current.title, problem=current.problem,
        impact=current.impact, options_summary=" | ".join(current.options),
        recommendation=current.recommendation,
    )
    session.write_text(content, encoding="utf-8")
    decisions.write_text(_render_asset("decisions.md", title=title), encoding="utf-8")
    return TurnResult("started", current.case_id, (session.as_posix(), decisions.as_posix()))


def _decision_blocks(content: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^## `(D-[0-9]{3})`", content, re.MULTILINE))
    return [
        (match.group(1), content[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(content)])
        for index, match in enumerate(matches)
    ]


def decide_current_case(
    project: Path,
    *,
    refinement_id: str,
    case: DecisionCase,
    decision: str,
    basis: str,
    consequences: str,
    confirmed: bool,
    remaining_cases: Iterable[DecisionCase] = (),
    supersedes: str | None = None,
    next_flow: str = "Use the agreed outcome as input to a separately authorized planning flow.",
    timestamp: datetime | None = None,
) -> TurnResult:
    if not confirmed:
        return TurnResult("confirmation_required", case.case_id, ())
    directory = refinement_root(project) / _validate_id(refinement_id, "refinement ID")
    session = directory / "session.md"
    decisions_file = directory / "decisions.md"
    content = session.read_text(encoding="utf-8")
    if f"- Current case: `{case.case_id}`" not in content:
        prior = decisions_file.read_text(encoding="utf-8")
        revisiting = supersedes and re.search(
            rf"## `{re.escape(supersedes)}`.*?^- Case: `{re.escape(case.case_id)}`.*?^- Status: accepted$",
            prior,
            re.MULTILINE | re.DOTALL,
        )
        if not revisiting:
            raise RefinementError("decision does not match current case")
        content = re.sub(r"^- Status: ready$", "- Status: active", content, count=1, flags=re.MULTILINE)
        content = re.sub(r"^- Current case: none$", f"- Current case: `{case.case_id}`", content, count=1, flags=re.MULTILINE)
    decisions = decisions_file.read_text(encoding="utf-8")
    blocks = _decision_blocks(decisions)
    decision_id = f"D-{len(blocks) + 1:03d}"
    if supersedes:
        found = False
        for old_id, block in blocks:
            if old_id == supersedes and "- Status: accepted" in block:
                decisions = decisions.replace(block, block.replace("- Status: accepted", f"- Status: superseded\n- Replaced by: `{decision_id}`", 1))
                found = True
                break
        if not found:
            raise RefinementError("superseded decision is not currently accepted")
    entry = (
        f"\n## `{decision_id}` — {case.title}\n\n- Case: `{case.case_id}`\n"
        f"- Status: accepted\n- Decided: {_now(timestamp)}\n- Decision: {decision}\n"
        f"- Basis: {basis}\n- Consequences: {consequences}\n"
        f"- Supersedes: {f'`{supersedes}`' if supersedes else 'none'}\n"
    )
    decisions_file.write_text(decisions.rstrip() + "\n" + entry, encoding="utf-8")
    content = content.replace(f"- [ ] `{case.case_id}`", f"- [x] `{case.case_id}`", 1)
    remaining = tuple(remaining_cases)
    if remaining:
        next_case = remaining[0]
        content = re.sub(r"^- Current case: `[^`]+`", f"- Current case: `{next_case.case_id}`", content, count=1, flags=re.MULTILINE)
        content = content.split("\n## Current case\n", 1)[0] + (
            f"\n## Current case\n\n### `{next_case.case_id}` — {next_case.title}\n\n"
            f"- Problem: {next_case.problem}\n- Why it matters: {next_case.impact}\n"
            f"- Options: {' | '.join(next_case.options)}\n- Recommendation: {next_case.recommendation}\n"
            "- User decision: pending\n\n## Next action\n\n"
            f"Ask one question required to resolve `{next_case.case_id}`.\n"
        )
        session.write_text(content, encoding="utf-8")
        return TurnResult("active", next_case.case_id, (session.as_posix(), decisions_file.as_posix()))

    content = re.sub(r"^- Status: active$", "- Status: ready", content, count=1, flags=re.MULTILINE)
    content = re.sub(r"^- Current case: `[^`]+`$", "- Current case: none", content, count=1, flags=re.MULTILINE)
    session.write_text(content, encoding="utf-8")
    accepted = []
    references = []
    for current_id, block in _decision_blocks(decisions_file.read_text(encoding="utf-8")):
        if "- Status: accepted" not in block:
            continue
        decided = re.search(r"^- Decision: (.+)$", block, re.MULTILINE)
        if decided:
            accepted.append(decided.group(1))
            references.append(current_id)
    outcome = directory / "outcome.md"
    outcome.write_text(_render_asset(
        "outcome.md", title=refinement_id, refinement_id=refinement_id,
        updated_at=_now(timestamp), goal=re.search(
            r"## Goal\n\n(.+?)\n\n##", content, re.DOTALL
        ).group(1), agreed_model="\n".join(f"- {item}" for item in accepted),
        constraints="- Preserve the confirmed scope and decision consequences.",
        remaining_unknowns="- None within the refinement scope.",
        decision_references="\n".join(f"- `{item}`" for item in references),
        next_flow=next_flow,
    ), encoding="utf-8")
    return TurnResult("ready", None, (session.as_posix(), decisions_file.as_posix(), outcome.as_posix()))
