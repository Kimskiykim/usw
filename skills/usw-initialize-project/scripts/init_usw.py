#!/usr/bin/env python3
"""Initialize the USW OpenSpec workspace without overwriting project files."""

from __future__ import annotations

import argparse
import os
import re
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import NamedTuple


LOCAL_STATE_IGNORE_CONTENT = "*\n"
TEMPLATE_ROOT = Path(__file__).parents[1] / "templates"
CONFIG_FILE_NAME = "usw.yaml"
SUPPORTED_SCHEMA_VERSION = 1
SUPPORTED_PROVIDERS = frozenset({"standalone", "openspec"})
DEFAULT_SPECIALIZED_ROOTS = {
    "flows": "usw/flows",
    "reviews": "usw/reviews",
}
STANDARD_SCENARIOS = ("analysis", "development", "testing")
ARTIFACT_TEMPLATE_PATHS = (
    "change/proposal.md",
    "change/design.md",
    "change/spec.md",
    "change/tasks.md",
    "task/task.md",
    "task/development-evidence.md",
    "task/testing-evidence.md",
    "review/receipt.md",
)


class ConfigError(OSError):
    """A configuration error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class WorkspaceConfig(NamedTuple):
    """Resolved v1 workspace configuration."""

    schema_version: int
    provider: str
    artifact_root: str
    legacy_refinement_root: str | None
    flow_root: str
    review_root: str
    raw_content: str | None = None

    @property
    def managed_roots(self) -> dict[str, str]:
        return {
            "artifacts": self.artifact_root,
            "flows": self.flow_root,
            "reviews": self.review_root,
        }


def default_config(provider: str = "standalone") -> WorkspaceConfig:
    """Return deterministic v1 defaults for an explicitly selected provider."""
    if provider not in SUPPORTED_PROVIDERS:
        raise ConfigError("unsupported_provider", f"unsupported provider: {provider}")
    artifact_root = "usw" if provider == "standalone" else "openspec"
    return WorkspaceConfig(
        schema_version=SUPPORTED_SCHEMA_VERSION,
        provider=provider,
        artifact_root=artifact_root,
        legacy_refinement_root=None,
        flow_root=DEFAULT_SPECIALIZED_ROOTS["flows"],
        review_root=DEFAULT_SPECIALIZED_ROOTS["reviews"],
    )


def render_default_config() -> str:
    """Render the canonical standalone v1 configuration."""
    return read_template("usw.yaml")


def _parse_yaml_mapping(content: str) -> dict[str, object]:
    """Parse the small mapping-only YAML subset used by usw.yaml v1."""
    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, root)]
    for line_number, source_line in enumerate(content.splitlines(), start=1):
        stripped = source_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "\t" in source_line[: len(source_line) - len(source_line.lstrip())]:
            raise ConfigError("invalid_config", f"tabs are not allowed at line {line_number}")
        indent = len(source_line) - len(source_line.lstrip(" "))
        if ":" not in stripped:
            raise ConfigError("invalid_config", f"expected mapping at line {line_number}")
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise ConfigError("invalid_config", f"empty key at line {line_number}")
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if key in parent:
            raise ConfigError("invalid_config", f"duplicate key {key!r} at line {line_number}")
        value = raw_value.strip()
        if not value:
            child: dict[str, object] = {}
            parent[key] = child
            stack.append((indent, child))
            continue
        if value.startswith(("'", '"')) and value.endswith(value[0]):
            value = value[1:-1]
        scalar: object = int(value) if value.isdecimal() else value
        parent[key] = scalar
    return root


def parse_config(content: str) -> WorkspaceConfig:
    """Parse supported fields while retaining the original bytes for consumers."""
    data = _parse_yaml_mapping(content)
    schema_version = data.get("schema_version")
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ConfigError(
            "unsupported_schema_version",
            f"expected {SUPPORTED_SCHEMA_VERSION}, got {schema_version!r}",
        )
    artifacts = data.get("artifacts", {})
    refinement = data.get("refinement", {})
    flows = data.get("flows", {})
    reviews = data.get("reviews", {})
    for name, section in (
        ("artifacts", artifacts),
        ("refinement", refinement),
        ("flows", flows),
        ("reviews", reviews),
    ):
        if not isinstance(section, dict):
            raise ConfigError("invalid_config", f"{name} must be a mapping")
    provider = artifacts.get("provider", "standalone")
    if not isinstance(provider, str) or provider not in SUPPORTED_PROVIDERS:
        raise ConfigError("unsupported_provider", f"unsupported provider: {provider!r}")
    defaults = default_config(provider)

    def root_value(section: dict[str, object], default: str, name: str) -> str:
        value = section.get("root", default)
        if not isinstance(value, str):
            raise ConfigError("invalid_root", f"{name}.root must be a string")
        return value

    legacy_refinement_root = refinement.get("root")
    if legacy_refinement_root is not None and not isinstance(
        legacy_refinement_root, str
    ):
        raise ConfigError("invalid_root", "refinement.root must be a string")

    return WorkspaceConfig(
        schema_version=SUPPORTED_SCHEMA_VERSION,
        provider=provider,
        artifact_root=root_value(artifacts, defaults.artifact_root, "artifacts"),
        legacy_refinement_root=legacy_refinement_root,
        flow_root=root_value(flows, defaults.flow_root, "flows"),
        review_root=root_value(reviews, defaults.review_root, "reviews"),
        raw_content=content,
    )


def _root_parts(value: str, name: str) -> tuple[str, ...]:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not value or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ConfigError("invalid_root", f"{name}.root must be a safe project-relative path: {value!r}")
    return path.parts


def _paths_overlap(first: tuple[str, ...], second: tuple[str, ...]) -> bool:
    shortest = min(len(first), len(second))
    return first[:shortest] == second[:shortest]


def _validate_no_symlink_components(project_root: Path, parts: tuple[str, ...], name: str) -> None:
    current = project_root
    for part in parts:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ConfigError("symlinked_root", f"{name}.root traverses symbolic link: {current}")
        if not stat.S_ISDIR(mode):
            raise ConfigError("invalid_root", f"{name}.root traverses non-directory: {current}")


def validate_config(project_root: Path, config: WorkspaceConfig) -> WorkspaceConfig:
    """Validate all managed roots without mutating the project."""
    project_root = project_root.resolve()
    parsed = {
        name: _root_parts(value, name)
        for name, value in config.managed_roots.items()
    }
    if config.legacy_refinement_root is not None:
        _root_parts(config.legacy_refinement_root, "refinement")
    reserved = {"git": (".git",), "local": (".usw",)}
    for name, parts in parsed.items():
        _validate_no_symlink_components(project_root, parts, name)
        for reserved_name, reserved_parts in reserved.items():
            if _paths_overlap(parts, reserved_parts):
                raise ConfigError(
                    "conflicting_roots",
                    f"{name}.root overlaps reserved {reserved_name} area",
                )

    specialized_names = ("flows", "reviews")
    for index, first_name in enumerate(specialized_names):
        for second_name in specialized_names[index + 1 :]:
            if _paths_overlap(parsed[first_name], parsed[second_name]):
                raise ConfigError(
                    "conflicting_roots",
                    f"{first_name}.root overlaps {second_name}.root",
                )

    for specialized_name in specialized_names:
        if not _paths_overlap(parsed["artifacts"], parsed[specialized_name]):
            continue
        allowed = (
            config.provider == "standalone"
            and len(parsed[specialized_name]) > len(parsed["artifacts"])
            and parsed[specialized_name][: len(parsed["artifacts"])]
            == parsed["artifacts"]
        )
        if not allowed:
            raise ConfigError(
                "conflicting_roots",
                f"artifacts.root overlaps {specialized_name}.root",
            )
    return config


def load_config(project_root: Path) -> WorkspaceConfig:
    """Load and validate usw.yaml, or resolve standalone defaults when absent."""
    config_path = project_root / CONFIG_FILE_NAME
    if _existing_path_kind(config_path) is None:
        config = default_config()
    else:
        config = parse_config(config_path.read_text(encoding="utf-8"))
    return validate_config(project_root, config)


def render_handoff(updated_at: datetime | None = None) -> str:
    """Return the initial developer-local handoff state."""
    timestamp = updated_at or datetime.now(timezone.utc)
    values = {
        "status": "idle",
        "updated_at": timestamp.isoformat(timespec="seconds"),
        "fact_or_none": "no active work",
        "one_next_action_or_none": "None.",
        "reference_or_none": "None.",
        "fresh_stale_or_unknown": "unknown",
    }
    return re.sub(
        r"{{([^}]+)}}",
        lambda match: values.get(match.group(1), "none"),
        read_template("local/HANDOFF.md"),
    )


def find_project_root(start: Path) -> Path:
    """Return the nearest Git root, or the supplied directory if none exists."""
    start = start.expanduser().resolve()
    if not start.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {start}")

    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def _relative_to_project(project_root: Path, path: Path) -> tuple[str, ...]:
    """Return a project-local path, rejecting paths that escape the project."""
    try:
        relative = path.relative_to(project_root)
    except ValueError as error:
        raise OSError(f"USW path escapes the project root: {path}") from error
    if not relative.parts:
        raise OSError("USW path must not be the project root")
    return relative.parts


def _require_real_directory(path: Path) -> None:
    """Reject symlinks and non-directory path components."""
    try:
        path_stat = os.lstat(path)
    except FileNotFoundError:
        raise
    if stat.S_ISLNK(path_stat.st_mode):
        raise OSError(f"USW refuses symbolic links inside the project: {path}")
    if not stat.S_ISDIR(path_stat.st_mode):
        raise NotADirectoryError(f"Project path is not a directory: {path}")


def _ensure_real_parent_directories(project_root: Path, path: Path) -> None:
    """Create missing parents while refusing to traverse symbolic links."""
    current = project_root
    for component in _relative_to_project(project_root, path)[:-1]:
        current = current / component
        try:
            _require_real_directory(current)
        except FileNotFoundError:
            try:
                current.mkdir()
            except FileExistsError:
                pass
            _require_real_directory(current)


def _existing_path_kind(path: Path) -> str | None:
    """Classify an existing path without following a symbolic link."""
    try:
        path_stat = os.lstat(path)
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(path_stat.st_mode):
        raise OSError(f"USW refuses symbolic links inside the project: {path}")
    if stat.S_ISDIR(path_stat.st_mode):
        return "directory"
    if stat.S_ISREG(path_stat.st_mode):
        return "file"
    raise OSError(f"Unsupported project filesystem object: {path}")


def create_file(project_root: Path, path: Path, content: str) -> bool:
    """Safely create a project-local file without following symbolic links."""
    _ensure_real_parent_directories(project_root, path)
    existing_kind = _existing_path_kind(path)
    if existing_kind == "file":
        return False
    if existing_kind == "directory":
        raise IsADirectoryError(f"Project path is a directory, not a file: {path}")

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        existing_kind = _existing_path_kind(path)
        if existing_kind == "file":
            return False
        if existing_kind == "directory":
            raise IsADirectoryError(f"Project path is a directory, not a file: {path}")
        raise
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return True


def create_directory(project_root: Path, path: Path) -> bool:
    """Safely create a project-local directory without following symbolic links."""
    _ensure_real_parent_directories(project_root, path)
    existing_kind = _existing_path_kind(path)
    if existing_kind == "directory":
        return False
    if existing_kind == "file":
        raise NotADirectoryError(f"Project path is not a directory: {path}")
    try:
        path.mkdir()
    except FileExistsError:
        existing_kind = _existing_path_kind(path)
        if existing_kind == "directory":
            return False
        if existing_kind == "file":
            raise NotADirectoryError(f"Project path is not a directory: {path}")
        raise
    return True


def read_template(relative_path: str) -> str:
    """Read a template distributed with the initialization skill."""
    return (TEMPLATE_ROOT / relative_path).read_text(encoding="utf-8")


def _git_is_worktree(project_root: Path) -> bool:
    """Return whether project_root is a usable Git worktree."""
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def _git_path_is_ignored(project_root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "check-ignore",
            "--quiet",
            "--no-index",
            "--",
            relative_path,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _git_path_is_tracked(project_root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "ls-files",
            "--error-unmatch",
            "--",
            relative_path,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def validate_workspace_paths(project_root: Path, config: WorkspaceConfig) -> None:
    """Reject existing managed paths that are symlinks or have the wrong type."""
    expected_paths = [
        (CONFIG_FILE_NAME, "file"),
        (config.flow_root, "directory"),
        (config.review_root, "directory"),
        (".usw", "directory"),
        (".usw/.gitignore", "file"),
        (".usw/HANDOFF.md", "file"),
    ]
    expected_paths.extend(
        (
            f"{config.flow_root}/flow-scenario-{scenario}.md",
            "file",
        )
        for scenario in STANDARD_SCENARIOS
    )
    if config.provider == "standalone":
        expected_paths.extend(
            [
                (config.artifact_root, "directory"),
                (f"{config.artifact_root}/changes", "directory"),
                (f"{config.artifact_root}/templates", "directory"),
            ]
        )
        expected_paths.extend(
            (f"{config.artifact_root}/templates/{path}", "file")
            for path in ARTIFACT_TEMPLATE_PATHS
        )
    for rendered_path, expected_kind in expected_paths:
        parts = Path(rendered_path).parts
        current = project_root
        for index, component in enumerate(parts):
            current = current / component
            current_kind = _existing_path_kind(current)
            if current_kind is None:
                break
            is_leaf = index == len(parts) - 1
            required_kind = expected_kind if is_leaf else "directory"
            if current_kind != required_kind:
                if required_kind == "directory":
                    raise NotADirectoryError(f"Project path is not a directory: {current}")
                raise IsADirectoryError(f"Project path is a directory, not a file: {current}")


def validate_local_state_git_policy(project_root: Path) -> None:
    """Ensure existing local USW state will remain local in a Git worktree."""
    local_ignore_file = project_root / ".usw" / ".gitignore"
    if not _git_is_worktree(project_root):
        return

    local_paths = (
        ".usw/HANDOFF.md",
        ".usw/HANDOFF.next.md",
        ".usw/refinements/.privacy-check",
    )
    tracked = [
        relative_path
        for relative_path in local_paths
        if _git_path_is_tracked(project_root, relative_path)
    ]
    if tracked:
        rendered = ", ".join(tracked)
        raise OSError(
            f"USW local state is tracked by Git: {rendered}; run "
            "'git rm --cached <path>' before initializing"
        )
    if _existing_path_kind(local_ignore_file) is None:
        return
    unignored = [
        relative_path
        for relative_path in local_paths
        if not _git_path_is_ignored(project_root, relative_path)
    ]
    if unignored:
        rendered = ", ".join(unignored)
        raise OSError(
            f"Existing {local_ignore_file} does not ignore USW local state: {rendered}"
        )


def detect_openspec_workspace(project_root: Path) -> bool:
    """Return whether an OpenSpec workspace exists, without inspecting its content."""
    return _existing_path_kind(project_root / "openspec") == "directory"


def initialize_usw(project: Path) -> list[tuple[Path, bool]]:
    """Create configured USW workspace state without overwriting project files."""
    project_root = find_project_root(project)
    config_file = project_root / CONFIG_FILE_NAME
    config = load_config(project_root)
    artifact_directory = project_root / config.artifact_root
    changes_directory = artifact_directory / "changes"
    artifact_template_directory = artifact_directory / "templates"
    flow_directory = project_root / config.flow_root
    review_directory = project_root / config.review_root
    local_state_ignore_file = project_root / ".usw" / ".gitignore"
    handoff_file = project_root / ".usw" / "HANDOFF.md"

    validate_workspace_paths(project_root, config)
    validate_local_state_git_policy(project_root)

    results = [
        (
            config_file,
            create_file(project_root, config_file, render_default_config()),
        ),
    ]
    if config.provider == "standalone":
        results.extend(
            [
                (
                    artifact_directory,
                    create_directory(project_root, artifact_directory),
                ),
                (
                    changes_directory,
                    create_directory(project_root, changes_directory),
                ),
                (
                    artifact_template_directory,
                    create_directory(project_root, artifact_template_directory),
                ),
            ]
        )
        results.extend(
            (
                artifact_template_directory / relative_path,
                create_file(
                    project_root,
                    artifact_template_directory / relative_path,
                    read_template(relative_path),
                ),
            )
            for relative_path in ARTIFACT_TEMPLATE_PATHS
        )
    results.extend(
        [
            (flow_directory, create_directory(project_root, flow_directory)),
            (review_directory, create_directory(project_root, review_directory)),
        ]
    )
    results.extend(
        (
            flow_directory / f"flow-scenario-{scenario}.md",
            create_file(
                project_root,
                flow_directory / f"flow-scenario-{scenario}.md",
                read_template(f"flows/flow-scenario-{scenario}.md"),
            ),
        )
        for scenario in STANDARD_SCENARIOS
    )
    results.extend([
        (
            local_state_ignore_file,
            create_file(project_root, local_state_ignore_file, LOCAL_STATE_IGNORE_CONTENT),
        ),
        (handoff_file, create_file(project_root, handoff_file, render_handoff())),
    ])
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a standalone USW workspace, project-owned artifact templates, "
            "and developer-local .usw/HANDOFF.md without overwriting existing files."
        )
    )
    parser.add_argument(
        "project",
        nargs="?",
        default=".",
        type=Path,
        help="Project directory (defaults to the current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_root = find_project_root(args.project)
        openspec_detected = detect_openspec_workspace(project_root)
        config = load_config(project_root)
        results = initialize_usw(args.project)
    except OSError as error:
        print(f"USW initialization failed: {error}", file=sys.stderr)
        return 1

    for path, created in results:
        status = "Created" if created else "Already exists"
        print(f"{status}: {path}")
    if openspec_detected:
        print(
            "Detected existing OpenSpec workspace; it was left unchanged. "
            "Set artifacts.provider: openspec in usw.yaml to opt in explicitly."
        )
    if config.legacy_refinement_root is not None:
        print(
            "Legacy refinement.root detected at "
            f"{config.legacy_refinement_root}; left unchanged. New intent "
            "clarification sessions use .usw/refinements and require an "
            "explicit migration decision."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
