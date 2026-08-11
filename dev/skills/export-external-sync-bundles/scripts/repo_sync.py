#!/usr/bin/env python3
"""Create and inspect repo-sync-text-v1 patch bundles.

The export path is the packaged form of the AEF/PD repository helper. The
import path exists only to support checks and disposable-clone validation.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from typing import Any


FORMAT = "repo-sync-text-v1"
VERSION = 1
DEFAULT_STATE_FILE = ".repo_sync_state.json"
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


class RepoSyncError(Exception):
    """Expected user-facing error."""


def run_git(repo: Path, args: list[str], *, input_data: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_output(repo: Path, args: list[str]) -> str:
    result = run_git(repo, args)
    if result.returncode:
        raise RepoSyncError(result.stderr.decode("utf-8", "replace").strip() or "git command failed")
    return result.stdout.decode("utf-8", "replace").strip()


def require_git_repo(repo: Path) -> Path:
    if not repo.exists():
        raise RepoSyncError(f"Repository path does not exist: {repo}")
    return Path(git_output(repo, ["rev-parse", "--show-toplevel"])).resolve()


def is_dirty(repo: Path) -> bool:
    return bool(git_output(repo, ["status", "--porcelain"]))


def read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"format": FORMAT, "channels": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RepoSyncError(f"State file is not valid JSON: {path}") from exc
    if not isinstance(state, dict):
        raise RepoSyncError(f"State file root must be an object: {path}")
    state.setdefault("format", FORMAT)
    state.setdefault("channels", {})
    return state


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_patch(repo: Path, base: str, head: str, paths: list[str]) -> bytes:
    args = ["diff", "--binary", "--full-index", "--find-renames", base, head]
    if paths:
        args.extend(["--", *paths])
    result = run_git(repo, args)
    if result.returncode:
        raise RepoSyncError(result.stderr.decode("utf-8", "replace").strip() or "git diff failed")
    if not result.stdout:
        raise RepoSyncError("No changes found for the selected base/head/path range")
    return result.stdout


def diff_entries(repo: Path, base: str, head: str, paths: list[str]) -> list[tuple[str, tuple[str, ...]]]:
    args = ["diff", "--name-status", "-z", "--find-renames", base, head]
    if paths:
        args.extend(["--", *paths])
    result = run_git(repo, args)
    if result.returncode:
        raise RepoSyncError(result.stderr.decode("utf-8", "replace").strip() or "git diff failed")
    fields = result.stdout.rstrip(b"\0").split(b"\0") if result.stdout else []
    entries: list[tuple[str, tuple[str, ...]]] = []
    index = 0
    try:
        while index < len(fields):
            status = fields[index].decode("ascii")
            index += 1
            path_count = 2 if status.startswith(("R", "C")) else 1
            names = tuple(field.decode("utf-8") for field in fields[index : index + path_count])
            if len(names) != path_count:
                raise ValueError
            entries.append((status, names))
            index += path_count
    except (UnicodeDecodeError, ValueError) as exc:
        raise RepoSyncError("Git paths in the selected range must be valid UTF-8") from exc
    return entries


def require_complete_rename_paths(repo: Path, base: str, head: str, paths: list[str]) -> None:
    if not paths:
        return
    full_renames = {
        names for status, names in diff_entries(repo, base, head, []) if status.startswith("R")
    }
    selected_entries = diff_entries(repo, base, head, paths)
    selected_names = {name for _, names in selected_entries for name in names}
    selected_renames = {
        names for status, names in selected_entries if status.startswith("R")
    }
    for old_path, new_path in sorted(full_renames - selected_renames):
        if old_path in selected_names or new_path in selected_names:
            raise RepoSyncError(
                "Path filter splits rename "
                f"{old_path!r} -> {new_path!r}; include both paths or exclude both"
            )


def blob_descriptor(repo: Path, revision: str, path: str, *, include_content: bool = False) -> dict[str, Any] | None:
    result = run_git(repo, ["--literal-pathspecs", "ls-tree", "-z", revision, "--", path])
    if result.returncode:
        raise RepoSyncError(result.stderr.decode("utf-8", "replace").strip() or "git ls-tree failed")
    if not result.stdout:
        return None
    record = result.stdout.rstrip(b"\0")
    header, _, listed_path = record.partition(b"\t")
    try:
        mode, object_type, oid = header.decode("ascii").split()
        decoded_path = listed_path.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        raise RepoSyncError(f"Cannot describe Git path: {path}") from exc
    if decoded_path != path or object_type != "blob":
        raise RepoSyncError(f"Unsupported non-blob change at path: {path}")
    content_result = run_git(repo, ["cat-file", "blob", oid])
    if content_result.returncode:
        raise RepoSyncError(content_result.stderr.decode("utf-8", "replace").strip() or "git cat-file failed")
    content = content_result.stdout
    descriptor: dict[str, Any] = {
        "path": path,
        "mode": mode,
        "oid": oid,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    if include_content:
        descriptor["content_b85"] = base64.b85encode(content).decode("ascii")
    return descriptor


def describe_changes(repo: Path, base: str, head: str, paths: list[str]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for status, names in diff_entries(repo, base, head, paths):
        kind = status[0]
        old_path = names[0]
        new_path = names[-1]
        old = None if kind == "A" else blob_descriptor(repo, base, old_path)
        new = None if kind == "D" else blob_descriptor(repo, head, new_path, include_content=kind == "R")
        changes.append({"status": status, "old": old, "new": new})
    return changes


def build_handoff_contract(
    channel: str,
    base: str,
    head: str,
    target: dict[str, str] | None,
    paths: list[str],
    changes: list[dict[str, Any]],
    patch_sha256: str,
) -> dict[str, Any]:
    rename_requirements = [
        {
            "old_path": change["old"]["path"],
            "new_path": change["new"]["path"],
            "preimage_required": True,
            "preimage_sha256": change["old"]["sha256"],
            "destination_sha256": change["new"]["sha256"],
        }
        for change in changes
        if str(change.get("status", "")).startswith("R")
    ]
    return {
        "contract_version": 1,
        "direction": channel,
        "source": {"base": base, "head": head},
        "expected_target_checkpoint": target,
        "scope": {
            "paths": paths,
            "change_count": len(changes),
            "dependency_manifest_policy": "only explicitly listed paths; dependency or manifest changes require inclusion and validation",
        },
        "integrity": {
            "patch_sha256": patch_sha256,
            "blob_inventory": "manifest.changes",
            "rename_requirements": rename_requirements,
        },
        "allowed_automatic_operations": [
            "inspect",
            "verify_hashes",
            "capture_actual_target_head",
            "apply_check",
            "disposable_apply_validation",
            "verified_pure_rename_add_replacement",
        ],
        "required_validation_sequence": [
            "inspect",
            "verify_hashes",
            "capture_actual_target_head",
            "compare_expected_checkpoint_and_content",
            "apply_summary",
            "apply_check",
            "disposable_apply_validation",
            "verify_postimage_hashes",
        ],
        "stop_conditions": [
            "dirty_worktree",
            "target_context_mismatch",
            "expected_checkpoint_mismatch",
            "missing_or_mismatched_preimage",
            "destination_conflict",
            "invalid_patch_or_blob_hash",
            "unsupported_platform_path",
        ],
        "receipt_template": {
            "outcome": None,
            "classification": None,
            "actual_target_head": None,
            "candidate_bundle_sha256": None,
            "validation": None,
            "apply_summary": None,
            "post_apply_diff_sha256": None,
            "tests": [],
            "commit": None,
            "real_target_modified": False,
        },
    }


def build_payload(manifest: dict[str, Any], patch: bytes) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode()
        for name, content in (("manifest.json", manifest_bytes), ("changes.patch", patch)):
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    return gzip.compress(buffer.getvalue(), compresslevel=9, mtime=0)


def parse_payload(payload: bytes) -> tuple[dict[str, Any], bytes]:
    try:
        tar_bytes = gzip.decompress(payload)
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r") as archive:
            names = set(archive.getnames())
            if names != {"manifest.json", "changes.patch"}:
                raise RepoSyncError("Sync payload must contain only manifest.json and changes.patch")
            manifest_file = archive.extractfile("manifest.json")
            patch_file = archive.extractfile("changes.patch")
            if manifest_file is None or patch_file is None:
                raise RepoSyncError("Sync payload is missing manifest or patch data")
            manifest = json.loads(manifest_file.read().decode())
            patch = patch_file.read()
    except (OSError, tarfile.TarError, KeyError, json.JSONDecodeError) as exc:
        raise RepoSyncError("Sync text is not a valid repo-sync payload") from exc
    if manifest.get("format") != FORMAT:
        raise RepoSyncError("Unsupported sync payload format")
    if manifest.get("patch_sha256") != hashlib.sha256(patch).hexdigest():
        raise RepoSyncError("Patch checksum does not match manifest")
    return manifest, patch


def encode_payload(payload: bytes) -> str:
    encoded = base64.b85encode(payload).decode("ascii")
    return "\n".join(encoded[i : i + 80] for i in range(0, len(encoded), 80)) + "\n"


def decode_payload(text: str) -> bytes:
    compact = "".join(text.split())
    if not compact:
        raise RepoSyncError("Sync text is empty")
    try:
        return base64.b85decode(compact.encode("ascii"))
    except ValueError as exc:
        raise RepoSyncError("Sync text is not valid encoded text") from exc


def read_bundle(path: Path) -> tuple[dict[str, Any], bytes]:
    return parse_payload(decode_payload(path.read_text(encoding="utf-8")))


def export_command(args: argparse.Namespace) -> int:
    if args.all and args.path:
        raise RepoSyncError("--all and --path cannot be used together")
    if not args.full and not args.all and not args.path:
        raise RepoSyncError("Incremental export requires at least one --path; use --all only after full diff review")
    repo = require_git_repo(args.repo.resolve())
    output = args.output.resolve()
    if output.suffix != ".sync":
        raise RepoSyncError("Output file must use the .sync extension")
    if output.exists() and not args.overwrite:
        raise RepoSyncError(f"Output file already exists: {output}")
    base = EMPTY_TREE if args.full else args.base
    if not base:
        state_path = (repo / args.state_file).resolve()
        base = read_state(state_path).get("channels", {}).get(args.channel, {}).get("last_export_head")
        if not base:
            raise RepoSyncError("No base revision is known; pass --base explicitly")
    base = git_output(repo, ["rev-parse", f"{base}^{{commit}}"])
    head = git_output(repo, ["rev-parse", f"{args.head}^{{commit}}"])
    require_complete_rename_paths(repo, base, head, args.path)
    patch = make_patch(repo, base, head, args.path)
    changes = describe_changes(repo, base, head, args.path)
    if bool(args.target_repo) != bool(args.target_id):
        raise RepoSyncError("--target-repo and --target-id must be supplied together")
    target = None
    if args.target_repo:
        target_repo = require_git_repo(args.target_repo.resolve())
        if is_dirty(target_repo):
            raise RepoSyncError(f"Target worktree must be clean: {target_repo}")
        target = {"id": args.target_id, "expected_head": git_output(target_repo, ["rev-parse", "HEAD^{commit}"])}
    dirty = is_dirty(repo)
    generated_at = datetime.now(timezone.utc).isoformat()
    patch_sha256 = hashlib.sha256(patch).hexdigest()
    manifest = {
        "format": FORMAT,
        "version": VERSION,
        "kind": "git-patch",
        "channel": args.channel,
        "source_repo": str(repo),
        "base": base,
        "head": head,
        "head_ref": args.head,
        "paths": args.path,
        "changes": changes,
        "target": target,
        "dirty_worktree_at_export": dirty,
        "generated_at": generated_at,
        "patch_bytes": len(patch),
        "patch_sha256": patch_sha256,
        "handoff": build_handoff_contract(args.channel, base, head, target, args.path, changes, patch_sha256),
        "note": "Validate against the recorded internal baseline before human transfer.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encode_payload(build_payload(manifest, patch)), encoding="utf-8")
    if not args.no_update_state:
        state_path = (repo / args.state_file).resolve()
        state = read_state(state_path)
        state.setdefault("channels", {})[args.channel] = {
            "last_export_base": base,
            "last_export_head": head,
            "last_export_file": str(output),
            "updated_at": generated_at,
        }
        write_state(state_path, state)
    print(f"Exported {len(patch)} patch bytes from {base}..{head} into {output}")
    if dirty:
        print("warning: source worktree has uncommitted changes; they were not included", file=sys.stderr)
    return 0


def inspect_command(args: argparse.Namespace) -> int:
    manifest, patch = read_bundle(args.bundle)
    display = json.loads(json.dumps(manifest))
    for change in display.get("changes", []):
        for side in ("old", "new"):
            descriptor = change.get(side)
            if isinstance(descriptor, dict) and descriptor.pop("content_b85", None) is not None:
                descriptor["content_embedded"] = True
    print(json.dumps(display, indent=2, sort_keys=True))
    if args.patch_out:
        args.patch_out.write_bytes(patch)
    return 0


def apply_patch(repo: Path, patch: bytes, *, check: bool) -> None:
    git_args = ["apply", "--binary", "--whitespace=nowarn"]
    if check:
        git_args.append("--check")
    result = run_git(repo, git_args, input_data=patch)
    if result.returncode:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise RepoSyncError(message or "git apply failed")


def import_command(args: argparse.Namespace) -> int:
    repo = require_git_repo(args.repo.resolve())
    manifest, patch = read_bundle(args.bundle)
    apply_patch(repo, patch, check=not args.apply)
    action = "Applied in disposable validation clone" if args.apply else "Checked"
    print(f"{action} patch from {manifest['base']}..{manifest['head']} in {repo}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or validate repo-sync-text-v1 .sync files")
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("repo", type=Path)
    export.add_argument("-o", "--output", type=Path, required=True)
    export.add_argument("--base")
    export.add_argument("--head", default="HEAD")
    export.add_argument("--full", action="store_true")
    export.add_argument("--path", action="append", default=[])
    export.add_argument("--all", action="store_true")
    export.add_argument("--channel", default="external-to-company")
    export.add_argument("--state-file", default=DEFAULT_STATE_FILE)
    export.add_argument("--no-update-state", action="store_true")
    export.add_argument("--overwrite", action="store_true")
    export.add_argument("--target-repo", type=Path)
    export.add_argument("--target-id")
    export.set_defaults(func=export_command)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("bundle", type=Path)
    inspect.add_argument("--patch-out", type=Path)
    inspect.set_defaults(func=inspect_command)
    import_parser = commands.add_parser("import")
    import_parser.add_argument("bundle", type=Path)
    import_parser.add_argument("repo", type=Path)
    import_parser.add_argument("--apply", action="store_true", help="Use only in a disposable validation clone")
    import_parser.set_defaults(func=import_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except RepoSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
