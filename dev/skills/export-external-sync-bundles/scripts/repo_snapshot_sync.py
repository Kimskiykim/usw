#!/usr/bin/env python3
"""Export, plan, and explicitly apply canonical tracked-file snapshots."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import stat
import subprocess
import sys
import tarfile
import tempfile
from typing import Any

import repo_sync


FORMAT = "repo-sync-snapshot-v1"
VERSION = 1
READY = "READY"
ALREADY = "ALREADY_OR_PARTIALLY_APPLIED"
UNSAFE = "UNSAFE_STOP"
PLAINTEXT_SECURITY = {
    "encrypted": False,
    "encoding": "base85+gzip+tar",
    "warning": (
        "Base85+gzip+tar is encoding/compression, not encryption. Treat this package as plaintext "
        "source content and use only a corporate-approved channel."
    ),
}
GIT_OBJECT_ID = re.compile(r"[0-9a-f]{40,64}")
WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


class SnapshotError(Exception):
    """Expected snapshot workflow failure."""


def output_text(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stdout.decode("utf-8", "replace").strip()


def error_text(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stderr.decode("utf-8", "replace").strip()


def report(outcome: str, classification: str, **values: Any) -> dict[str, Any]:
    return {
        "outcome": outcome,
        "classification": classification,
        "real_target_modified": False,
        "commit_performed": False,
        "push_performed": False,
        "transfer_performed": False,
        **values,
    }


def write_report(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_path(path: str) -> str:
    pure = PurePosixPath(path)
    if (
        not path
        or "\\" in path
        or "\0" in path
        or WINDOWS_DRIVE.match(path) is not None
        or pure.is_absolute()
        or str(pure) != path
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        raise SnapshotError(f"Unsafe snapshot path: {path!r}")
    if any(part.casefold() == ".git" for part in pure.parts):
        raise SnapshotError(f"Snapshot paths must never include .git: {path!r}")
    return path


def safe_symlink_target(path: str, content: bytes) -> str:
    try:
        target = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SnapshotError(f"Symlink target must be UTF-8 at {path}") from exc
    pure = PurePosixPath(target)
    if (
        not target
        or "\\" in target
        or "\0" in target
        or WINDOWS_DRIVE.match(target) is not None
        or pure.is_absolute()
    ):
        raise SnapshotError(f"Unsafe symlink target at {path}: {target!r}")
    resolved = list(PurePosixPath(path).parent.parts)
    for part in pure.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not resolved:
                raise SnapshotError(f"Symlink escapes repository at {path}: {target!r}")
            resolved.pop()
        else:
            resolved.append(part)
    if any(part.casefold() == ".git" for part in resolved):
        raise SnapshotError(f"Symlink targets .git at {path}: {target!r}")
    return target


def normalize_filters(values: list[str]) -> list[str]:
    return sorted({safe_path(value.rstrip("/")) for value in values})


def path_matches(path: str, pattern: str) -> bool:
    return path == pattern or path.startswith(f"{pattern}/")


def cat_blob(repo: Path, oid: str) -> bytes:
    result = repo_sync.run_git(repo, ["cat-file", "blob", oid])
    if result.returncode:
        raise SnapshotError(error_text(result) or f"Cannot read Git blob {oid}")
    return result.stdout


def descriptor(path: str, mode: str, oid: str, content: bytes) -> dict[str, Any]:
    return {
        "path": safe_path(path),
        "mode": mode,
        "oid": oid,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def tree_hash(files: list[dict[str, Any]]) -> str:
    inventory = [
        {key: item[key] for key in ("path", "mode", "bytes", "sha256")}
        for item in files
    ]
    encoded = json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_files(
    repo: Path,
    revision: str,
    allow: list[str],
    deny: list[str],
) -> tuple[list[dict[str, Any]], dict[str, bytes], list[str]]:
    result = repo_sync.run_git(repo, ["ls-tree", "-r", "-z", "--full-tree", revision])
    if result.returncode:
        raise SnapshotError(error_text(result) or "git ls-tree failed")
    files: list[dict[str, Any]] = []
    blobs: dict[str, bytes] = {}
    excluded: list[str] = []
    for record in result.stdout.rstrip(b"\0").split(b"\0") if result.stdout else []:
        header, separator, raw_path = record.partition(b"\t")
        if not separator:
            raise SnapshotError("Invalid git ls-tree record")
        try:
            mode, object_type, oid = header.decode("ascii").split()
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise SnapshotError("Snapshot requires UTF-8 Git paths") from exc
        safe_path(path)
        selected = (not allow or any(path_matches(path, item) for item in allow)) and not any(
            path_matches(path, item) for item in deny
        )
        if not selected:
            excluded.append(path)
            continue
        if object_type != "blob" or mode not in {"100644", "100755", "120000"}:
            raise SnapshotError(f"Unsupported tracked object {object_type}/{mode} at {path}; gitlinks are not snapshot files")
        content = cat_blob(repo, oid)
        if mode == "120000":
            safe_symlink_target(path, content)
        item = descriptor(path, mode, oid, content)
        files.append(item)
        blobs.setdefault(item["sha256"], content)
    files.sort(key=lambda item: item["path"])
    return files, blobs, sorted(excluded)


def build_payload(manifest: dict[str, Any], blobs: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        members = [("manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"))]
        members.extend((f"blobs/{digest}", blobs[digest]) for digest in sorted(blobs))
        for name, content in members:
            member = tarfile.TarInfo(name)
            member.size = len(content)
            member.mode = 0o600
            member.mtime = 0
            member.uid = member.gid = 0
            member.uname = member.gname = ""
            archive.addfile(member, io.BytesIO(content))
    return gzip.compress(buffer.getvalue(), compresslevel=9, mtime=0)


def parse_payload(payload: bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
    try:
        with tarfile.open(fileobj=io.BytesIO(gzip.decompress(payload)), mode="r") as archive:
            names = archive.getnames()
            if len(names) != len(set(names)) or "manifest.json" not in names:
                raise SnapshotError("Snapshot payload has duplicate or missing members")
            manifest_file = archive.extractfile("manifest.json")
            if manifest_file is None or not archive.getmember("manifest.json").isfile():
                raise SnapshotError("Snapshot manifest is missing")
            manifest = json.loads(manifest_file.read().decode("utf-8"))
            if manifest.get("format") != FORMAT or manifest.get("version") != VERSION:
                raise SnapshotError("Unsupported snapshot format/version")
            if manifest.get("kind") != "git-tracked-snapshot" or manifest.get("direction") != "internal-to-external":
                raise SnapshotError("Snapshot direction must be immutable internal-to-external")
            canonical = manifest.get("canonical")
            if (
                not isinstance(canonical, dict)
                or not isinstance(canonical.get("source_repo"), str)
                or GIT_OBJECT_ID.fullmatch(str(canonical.get("commit", ""))) is None
                or GIT_OBJECT_ID.fullmatch(str(canonical.get("tree", ""))) is None
            ):
                raise SnapshotError("Snapshot canonical commit/tree identity is invalid")
            files = manifest.get("files")
            if not isinstance(files, list) or files != sorted(files, key=lambda item: item.get("path", "")):
                raise SnapshotError("Snapshot file inventory must be a sorted list")
            blobs: dict[str, bytes] = {}
            expected_names = {"manifest.json"}
            seen_paths: set[str] = set()
            for item in files:
                path = safe_path(item["path"])
                if path in seen_paths:
                    raise SnapshotError(f"Duplicate snapshot path: {path}")
                seen_paths.add(path)
                digest = item["sha256"]
                member_name = f"blobs/{digest}"
                expected_names.add(member_name)
                if digest not in blobs:
                    member = archive.extractfile(member_name)
                    if member is None or not archive.getmember(member_name).isfile():
                        raise SnapshotError(f"Snapshot blob is missing: {digest}")
                    content = member.read()
                    if hashlib.sha256(content).hexdigest() != digest:
                        raise SnapshotError(f"Snapshot blob checksum mismatch: {digest}")
                    blobs[digest] = content
                if len(blobs[digest]) != item["bytes"] or item["mode"] not in {"100644", "100755", "120000"}:
                    raise SnapshotError(f"Snapshot descriptor mismatch at {path}")
                if item["mode"] == "120000":
                    safe_symlink_target(path, blobs[digest])
            if set(names) != expected_names:
                raise SnapshotError("Snapshot payload contains unreferenced members")
            if manifest.get("tree_sha256") != tree_hash(files):
                raise SnapshotError("Snapshot tracked-tree checksum mismatch")
            return manifest, blobs
    except (OSError, tarfile.TarError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        if isinstance(exc, SnapshotError):
            raise
        raise SnapshotError("Snapshot payload is invalid") from exc


def encode_snapshot(manifest: dict[str, Any], blobs: dict[str, bytes]) -> bytes:
    return repo_sync.encode_payload(build_payload(manifest, blobs)).encode("ascii")


def decode_snapshot(data: bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise SnapshotError("Snapshot transport must be base85 text") from exc
    return parse_payload(repo_sync.decode_payload(text))


def read_snapshot(path: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    try:
        return decode_snapshot(path.read_bytes())
    except OSError as exc:
        raise SnapshotError(f"Cannot read snapshot: {path}") from exc


def tracked_dirty(repo: Path) -> bool:
    result = repo_sync.run_git(repo, ["status", "--porcelain=v1", "-z", "--untracked-files=no"])
    if result.returncode:
        raise SnapshotError(error_text(result) or "git status failed")
    return bool(result.stdout)


def index_files(repo: Path) -> dict[str, dict[str, Any]]:
    result = repo_sync.run_git(repo, ["ls-files", "-s", "-z"])
    if result.returncode:
        raise SnapshotError(error_text(result) or "git ls-files failed")
    files: dict[str, dict[str, Any]] = {}
    for record in result.stdout.rstrip(b"\0").split(b"\0") if result.stdout else []:
        header, separator, raw_path = record.partition(b"\t")
        if not separator:
            raise SnapshotError("Invalid git index record")
        try:
            mode, oid, stage = header.decode("ascii").split()
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise SnapshotError("Snapshot requires UTF-8 target paths") from exc
        if stage != "0" or mode not in {"100644", "100755", "120000"}:
            raise SnapshotError(f"Unsupported target index entry at {path}")
        content = cat_blob(repo, oid)
        files[path] = descriptor(path, mode, oid, content)
    return files


def local_untracked(repo: Path) -> list[str]:
    paths: set[str] = set()
    for arguments in (
        ["ls-files", "--others", "--exclude-standard", "-z"],
        ["ls-files", "--others", "--ignored", "--exclude-standard", "-z"],
    ):
        result = repo_sync.run_git(repo, arguments)
        if result.returncode:
            raise SnapshotError(error_text(result) or "Cannot inspect untracked target paths")
        paths.update(raw.decode("utf-8") for raw in result.stdout.rstrip(b"\0").split(b"\0") if raw)
    return sorted(paths)


def collides(path: str, local_path: str) -> bool:
    return path == local_path or path.startswith(f"{local_path}/") or local_path.startswith(f"{path}/")


def untracked_collisions(repo: Path, add_paths: list[str]) -> list[str]:
    return sorted(
        {
            local
            for local in local_untracked(repo)
            if any(collides(path, local) for path in add_paths)
        }
        | {
            path
            for path in add_paths
            if (repo / path).exists() or (repo / path).is_symlink()
        }
    )


def make_plan(
    canonical: list[dict[str, Any]],
    current: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    expected = {item["path"]: item for item in canonical}
    add = sorted(expected.keys() - current.keys())
    delete = sorted(current.keys() - expected.keys())
    replace: list[str] = []
    unchanged: list[str] = []
    for path in sorted(expected.keys() & current.keys()):
        if (expected[path]["mode"], expected[path]["sha256"]) == (current[path]["mode"], current[path]["sha256"]):
            unchanged.append(path)
        else:
            replace.append(path)
    return {"add": add, "replace": replace, "delete": delete, "unchanged": unchanged}


def ensure_safe_parents(repo: Path, path: str) -> None:
    current = repo
    for part in PurePosixPath(path).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise SnapshotError(f"Refusing to traverse symlink parent for {path}")
        if current.exists() and not current.is_dir():
            raise SnapshotError(f"Non-directory parent blocks snapshot path: {path}")
        current.mkdir(exist_ok=True)


def remove_path(repo: Path, path: str) -> None:
    target = repo / path
    if target.is_symlink() or target.exists():
        if target.is_dir() and not target.is_symlink():
            raise SnapshotError(f"Refusing to remove directory as tracked file: {path}")
        target.unlink()
    parent = target.parent
    while parent != repo:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def write_file(repo: Path, item: dict[str, Any], content: bytes) -> None:
    path = item["path"]
    ensure_safe_parents(repo, path)
    target = repo / path
    temporary = target.with_name(f".{target.name}.sync-tmp-{os.getpid()}")
    if temporary.is_symlink() or temporary.exists():
        raise SnapshotError(f"Temporary path collision for {path}")
    try:
        if item["mode"] == "120000":
            os.symlink(safe_symlink_target(path, content), temporary)
        else:
            temporary.write_bytes(content)
            temporary.chmod(0o755 if item["mode"] == "100755" else 0o644)
        os.replace(temporary, target)
    finally:
        if temporary.is_symlink() or temporary.exists():
            temporary.unlink()


def worktree_backup(repo: Path, paths: list[str]) -> dict[str, tuple[str, bytes] | None]:
    backup: dict[str, tuple[str, bytes] | None] = {}
    for path in paths:
        target = repo / path
        if target.is_symlink():
            backup[path] = ("120000", os.readlink(os.fsencode(target)))
        elif target.is_file():
            mode = "100755" if target.stat().st_mode & stat.S_IXUSR else "100644"
            backup[path] = (mode, target.read_bytes())
        elif target.exists():
            raise SnapshotError(f"Unsupported worktree object at {path}")
        else:
            backup[path] = None
    return backup


def restore_backup(repo: Path, backup: dict[str, tuple[str, bytes] | None]) -> None:
    reset = repo_sync.run_git(repo, ["reset", "--quiet", "HEAD"])
    for path in sorted(backup, key=lambda value: (value.count("/"), value), reverse=True):
        remove_path(repo, path)
    for path, saved in sorted(backup.items()):
        if saved is not None:
            mode, content = saved
            write_file(repo, {"path": path, "mode": mode}, content)
    if reset.returncode:
        raise SnapshotError(error_text(reset) or "Automatic index rollback failed")


def verify_index(repo: Path, canonical: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {item["path"]: (item["mode"], item["sha256"]) for item in canonical}
    actual_files = index_files(repo)
    actual = {path: (item["mode"], item["sha256"]) for path, item in actual_files.items()}
    return {
        "tracked_tree_match": actual == expected,
        "expected_file_count": len(expected),
        "actual_file_count": len(actual),
        "tree_sha256": tree_hash(canonical),
    }


def apply_to_repo(
    repo: Path,
    canonical: list[dict[str, Any]],
    blobs: dict[str, bytes],
    plan: dict[str, list[str]],
) -> dict[str, Any]:
    if tracked_dirty(repo):
        raise SnapshotError("Target tracked/index state changed before apply")
    if make_plan(canonical, index_files(repo)) != plan:
        raise SnapshotError("Target tracked tree changed after plan")
    collisions = untracked_collisions(repo, plan["add"])
    if collisions:
        raise SnapshotError(f"Late untracked path collision: {', '.join(collisions)}")
    affected = sorted(plan["add"] + plan["replace"] + plan["delete"])
    expected = {item["path"]: item for item in canonical}
    backup = worktree_backup(repo, affected)
    try:
        for path in sorted(plan["delete"] + plan["replace"], reverse=True):
            remove_path(repo, path)
        for path in sorted(plan["add"] + plan["replace"]):
            item = expected[path]
            write_file(repo, item, blobs[item["sha256"]])
        if affected:
            staged = repo_sync.run_git(repo, ["add", "-A", "--", *affected])
            if staged.returncode:
                raise SnapshotError(error_text(staged) or "Failed to stage converged tracked paths")
        verification = verify_index(repo, canonical)
        if not verification["tracked_tree_match"]:
            raise SnapshotError("Final tracked tree does not match canonical snapshot")
        return verification
    except Exception as original:
        try:
            restore_backup(repo, backup)
        except Exception as rollback:
            raise SnapshotError(f"{original}; automatic rollback failed: {rollback}") from rollback
        raise


def clone_at(repo: Path, revision: str, destination: Path) -> None:
    result = subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", str(repo), str(destination)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise SnapshotError(error_text(result) or "Disposable target clone failed")
    checkout = repo_sync.run_git(destination, ["checkout", "--quiet", "--detach", revision])
    if checkout.returncode:
        raise SnapshotError(error_text(checkout) or "Disposable target checkout failed")


def analyze(
    bundle: Path,
    target_arg: Path,
    *,
    disposable: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, bytes], Path]:
    manifest, blobs = read_snapshot(bundle.resolve())
    target = repo_sync.require_git_repo(target_arg.resolve())
    target_head = repo_sync.git_output(target, ["rev-parse", "HEAD^{commit}"])
    target_info = {"repo": str(target), "head": target_head}
    common = {
        "bundle": str(bundle.resolve()),
        "bundle_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "target": target_info,
        "canonical": manifest["canonical"],
        "transport_security": PLAINTEXT_SECURITY,
    }
    if tracked_dirty(target):
        return report(UNSAFE, "TARGET_TRACKED_DIRTY", **common), manifest, blobs, target
    current = index_files(target)
    plan = make_plan(manifest["files"], current)
    collisions = untracked_collisions(target, plan["add"])
    if collisions:
        return (
            report(UNSAFE, "UNTRACKED_PATH_COLLISION", **common, plan=plan, collisions=collisions),
            manifest,
            blobs,
            target,
        )
    changed = bool(plan["add"] or plan["replace"] or plan["delete"])
    result = report(
        READY if changed else ALREADY,
        "CANONICAL_CHANGES_REQUIRED" if changed else "IN_SYNC",
        **common,
        divergence="DIVERGED" if changed else "IN_SYNC",
        plan=plan,
        deletion_review={"required": bool(plan["delete"]), "paths": plan["delete"]},
    )
    if disposable:
        if changed:
            with tempfile.TemporaryDirectory(prefix="sync-snapshot-check-") as temp:
                clone = Path(temp) / "target"
                clone_at(target, target_head, clone)
                clone_plan = make_plan(manifest["files"], index_files(clone))
                validation = apply_to_repo(clone, manifest["files"], blobs, clone_plan)
        else:
            validation = verify_index(target, manifest["files"])
        result["disposable_validation"] = validation
    return result, manifest, blobs, target


def snapshot_manifest(
    source: Path,
    direction: str,
    commit: str,
    tree: str,
    files: list[dict[str, Any]],
    excluded: list[str],
    allow: list[str],
    deny: list[str],
) -> dict[str, Any]:
    fingerprint = tree_hash(files)
    return {
        "format": FORMAT,
        "version": VERSION,
        "kind": "git-tracked-snapshot",
        "direction": direction,
        "canonical": {"source_repo": str(source), "commit": commit, "tree": tree},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "tree_sha256": fingerprint,
        "scope": {
            "default_inclusion": "all tracked files at canonical head",
            "untracked_included": False,
            "allow_paths": allow,
            "deny_paths": deny,
            "excluded_tracked_paths": excluded,
            "tracked_gitignore_included": any(item["path"] == ".gitignore" for item in files),
        },
        "authorization": {
            "export_acknowledgement_flag": "--acknowledge-full-snapshot",
            "apply_flag": "--confirm-converge",
            "automatic_apply": False,
        },
        "handoff": {
            "security_warning": PLAINTEXT_SECURITY["warning"],
            "command_templates": {
                "inspect": "python scripts/repo_snapshot_sync.py inspect PACKAGE.sync",
                "plan": "python scripts/repo_snapshot_sync.py plan PACKAGE.sync TARGET_REPO --report plan.json",
                "apply": (
                    "python scripts/repo_snapshot_sync.py apply PACKAGE.sync TARGET_REPO "
                    "--confirm-converge --report apply.json"
                ),
            },
            "required_receiver_sequence": [
                "inspect",
                "capture_actual_target_head",
                "plan_add_replace_delete_unchanged",
                "disposable_validation",
                "explicit_apply_confirmation",
                "verify_final_tracked_tree",
            ],
            "stop_conditions": [
                "invalid_hash_or_format",
                "tracked_target_dirty",
                "untracked_or_ignored_path_collision",
                "unsupported_gitlink_or_platform_path",
                "missing_explicit_confirmation",
            ],
            "receipt_template": {
                "outcome": None,
                "classification": None,
                "actual_target_head": None,
                "plan": {"add": [], "replace": [], "delete": [], "unchanged": []},
                "tracked_tree_match": None,
                "rollback_command": None,
                "commit_performed": False,
                "push_performed": False,
            },
        },
    }


def export_command(args: argparse.Namespace) -> dict[str, Any]:
    if not args.acknowledge_full_snapshot:
        return report(
            UNSAFE,
            "AUTHORIZATION_REQUIRED",
            error="Full tracked-repository transport requires --acknowledge-full-snapshot after security/scope review.",
        )
    source = repo_sync.require_git_repo(args.source_repo.resolve())
    if tracked_dirty(source):
        return report(UNSAFE, "CANONICAL_TRACKED_DIRTY", canonical={"repo": str(source)})
    output = args.output.resolve()
    if output.exists():
        return report(UNSAFE, "OUTPUT_COLLISION", error=f"Output already exists: {output}")
    if output.suffix != ".sync":
        return report(UNSAFE, "INVALID_OUTPUT", error="Snapshot output must use the stable .sync extension")
    allow = normalize_filters(args.allow_path)
    deny = normalize_filters(args.deny_path)
    commit = repo_sync.git_output(source, ["rev-parse", f"{args.head}^{{commit}}"])
    tree = repo_sync.git_output(source, ["rev-parse", f"{commit}^{{tree}}"])
    files, blobs, excluded = canonical_files(source, commit, allow, deny)
    if not files:
        return report(UNSAFE, "EMPTY_SCOPE", error="Snapshot scope contains no tracked files")
    manifest = snapshot_manifest(source, args.direction, commit, tree, files, excluded, allow, deny)
    plaintext = encode_snapshot(manifest, blobs)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(plaintext)
    script = str(Path(__file__).resolve())
    return report(
        READY,
        "SNAPSHOT_EXPORTED",
        bundle=str(output),
        bundle_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        canonical=manifest["canonical"],
        scope=manifest["scope"],
        tree_sha256=manifest["tree_sha256"],
        file_count=len(files),
        transport_security=PLAINTEXT_SECURITY,
        usage={
            "inspect": shlex.join([sys.executable, script, "inspect", str(output)]),
            "plan": shlex.join(
                [sys.executable, script, "plan", str(output), "TARGET_REPO", "--report", "plan.json"]
            ),
        },
    )


def inspect_command(args: argparse.Namespace) -> dict[str, Any]:
    manifest, _ = read_snapshot(args.bundle.resolve())
    return manifest


def plan_command(args: argparse.Namespace) -> dict[str, Any]:
    value, _, _, _ = analyze(args.bundle, args.target_repo, disposable=True)
    value["usage"] = {
        "apply": shlex.join(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "apply",
                str(args.bundle.resolve()),
                str(args.target_repo.resolve()),
                "--confirm-converge",
                "--report",
                str(args.report.with_name(f"{args.report.stem}-apply.json").resolve()),
            ]
        )
    }
    return value


def apply_command(args: argparse.Namespace) -> dict[str, Any]:
    if not args.confirm_converge:
        return report(
            UNSAFE,
            "CONFIRMATION_REQUIRED",
            error="Snapshot apply requires explicit --confirm-converge after reviewing the dry-run plan.",
        )
    value, manifest, blobs, target = analyze(args.bundle, args.target_repo, disposable=True)
    if value["outcome"] == UNSAFE:
        return value
    if value["classification"] == "IN_SYNC":
        return value
    plan = value["plan"]
    verification = apply_to_repo(target, manifest["files"], blobs, plan)
    affected = sorted(plan["add"] + plan["replace"] + plan["delete"])
    rollback = shlex.join(
        ["git", "restore", "--source=HEAD", "--staged", "--worktree", "--", *affected]
    )
    value.update(
        {
            "outcome": READY,
            "classification": "CONVERGED_STAGED",
            "real_target_modified": True,
            "verification": verification,
            "transaction": {
                "rollback_available": True,
                "rollback_command": rollback,
                "rollback_cwd": str(target),
                "failure_rollback": "automatic",
                "commit_performed": False,
            },
        }
    )
    return value


def add_export_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("source_repo", type=Path)
    parser.add_argument("--direction", required=True, choices=["internal-to-external"])
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--allow-path", action="append", default=[])
    parser.add_argument("--deny-path", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--acknowledge-full-snapshot", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canonical tracked-repository snapshot/converge workflow")
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="export canonical tracked files into a self-contained snapshot")
    add_export_arguments(export)
    export.set_defaults(func=export_command)
    inspect = commands.add_parser("inspect", help="inspect and verify snapshot metadata")
    inspect.add_argument("bundle", type=Path)
    inspect.set_defaults(func=inspect_command)
    plan = commands.add_parser("plan", help="deterministic dry-run plus disposable convergence validation")
    plan.add_argument("bundle", type=Path)
    plan.add_argument("target_repo", type=Path)
    plan.add_argument("--report", required=True, type=Path)
    plan.set_defaults(func=plan_command)
    apply = commands.add_parser("apply", help="explicitly stage canonical tracked-tree convergence")
    apply.add_argument("bundle", type=Path)
    apply.add_argument("target_repo", type=Path)
    apply.add_argument("--confirm-converge", action="store_true")
    apply.add_argument("--report", required=True, type=Path)
    apply.set_defaults(func=apply_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        value = args.func(args)
    except (OSError, SnapshotError, repo_sync.RepoSyncError) as exc:
        value = report(UNSAFE, "UNSAFE_ERROR", error=str(exc))
    if hasattr(args, "report"):
        write_report(args.report.resolve(), value)
    print(json.dumps(value, sort_keys=True))
    if args.command == "inspect":
        return 1 if value.get("outcome") == UNSAFE else 0
    return 0 if value.get("outcome") in {READY, ALREADY} else 1


if __name__ == "__main__":
    raise SystemExit(main())
