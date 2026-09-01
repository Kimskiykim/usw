#!/usr/bin/env python3
"""Target-aware export and receive checks for repo-sync-text-v1 bundles.

The target repository is always read-only. Patch application happens only in a
temporary local clone that is deleted before this process exits.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
from typing import Any

import repo_sync


READY = "READY"
NEEDS_BASELINE = "NEEDS_REBASE_OR_BASELINE"
CONFLICT = "CONFLICT_OR_PATH_MISMATCH"
ALREADY = "ALREADY_OR_PARTIALLY_APPLIED"
UNSAFE = "UNSAFE_STOP"


def text_output(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stdout.decode("utf-8", "replace").strip()


def error_output(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stderr.decode("utf-8", "replace").strip()


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def exit_code(report: dict[str, Any]) -> int:
    if report["outcome"] in {READY, ALREADY}:
        return 0
    return 1 if report["outcome"] == UNSAFE else 2


def result_report(outcome: str, classification: str, **values: Any) -> dict[str, Any]:
    return {
        "outcome": outcome,
        "classification": classification,
        "real_target_modified": False,
        "commit_performed": False,
        "push_performed": False,
        "transfer_performed": False,
        **values,
    }


def add_bundle_receipt(report: dict[str, Any], input_bundle: Path) -> None:
    if not input_bundle.is_file():
        return
    report["input_bundle_sha256"] = hashlib.sha256(input_bundle.read_bytes()).hexdigest()
    replacement = report.get("replacement")
    candidate = Path(replacement["bundle"]) if isinstance(replacement, dict) else input_bundle
    if candidate.is_file():
        report["candidate_bundle_sha256"] = hashlib.sha256(candidate.read_bytes()).hexdigest()


def copy_worktree_bytes(source: Path, destination: Path, paths: list[str]) -> None:
    for path in paths:
        source_path = source / path
        destination_path = destination / path
        if destination_path.is_symlink() or destination_path.exists():
            destination_path.unlink()
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.is_symlink():
            destination_path.symlink_to(source_path.readlink())
        elif source_path.is_file():
            destination_path.write_bytes(source_path.read_bytes())
            destination_path.chmod(stat.S_IMODE(source_path.stat().st_mode))
        else:
            raise repo_sync.RepoSyncError(f"Tracked target path is absent from worktree: {path}")


def tracked_paths(repo: Path) -> list[str]:
    listed = repo_sync.run_git(repo, ["ls-files", "-z"])
    if listed.returncode:
        raise repo_sync.RepoSyncError(error_output(listed) or "Cannot list tracked target paths")
    try:
        return [raw.decode("utf-8") for raw in listed.stdout.rstrip(b"\0").split(b"\0") if raw]
    except UnicodeDecodeError as exc:
        raise repo_sync.RepoSyncError("Tracked target paths must be valid UTF-8") from exc


def clone_at(
    repo: Path,
    revision: str,
    destination: Path,
    *,
    worktree_source: Path | None = None,
    unchanged_paths: list[str] | None = None,
) -> None:
    result = subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout", str(repo), str(destination)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise repo_sync.RepoSyncError(error_output(result) or "temporary clone failed")
    repo_sync.copy_checkout_environment(repo, destination)
    checkout = repo_sync.run_git(destination, ["checkout", "--quiet", "--detach", revision])
    if checkout.returncode:
        raise repo_sync.RepoSyncError(error_output(checkout) or "temporary checkout failed")
    if worktree_source is not None and unchanged_paths:
        copy_worktree_bytes(worktree_source, destination, unchanged_paths)


def descriptor_content(descriptor: dict[str, Any]) -> bytes | None:
    encoded = descriptor.get("content_b85")
    if not isinstance(encoded, str):
        return None
    try:
        content = base64.b85decode(encoded.encode("ascii"))
    except (UnicodeEncodeError, ValueError) as exc:
        raise repo_sync.RepoSyncError(f"Invalid embedded blob for {descriptor.get('path')}") from exc
    if len(content) != descriptor.get("bytes") or hashlib.sha256(content).hexdigest() != descriptor.get("sha256"):
        raise repo_sync.RepoSyncError(f"Embedded blob checksum mismatch for {descriptor.get('path')}")
    return content


def same_blob(actual: dict[str, Any] | None, expected: dict[str, Any] | None) -> bool:
    if actual is None or expected is None:
        return actual is expected
    return actual.get("mode") == expected.get("mode") and actual.get("sha256") == expected.get("sha256")


def index_descriptor(repo: Path, path: str) -> dict[str, Any] | None:
    result = repo_sync.run_git(repo, ["--literal-pathspecs", "ls-files", "-s", "-z", "--", path])
    if result.returncode:
        raise repo_sync.RepoSyncError(error_output(result) or "git ls-files failed")
    if not result.stdout:
        return None
    header, _, listed_path = result.stdout.rstrip(b"\0").partition(b"\t")
    mode, oid, stage = header.decode("ascii").split()
    if stage != "0" or listed_path.decode("utf-8") != path:
        raise repo_sync.RepoSyncError(f"Unexpected index state for {path}")
    content_result = repo_sync.run_git(repo, ["cat-file", "blob", oid])
    if content_result.returncode:
        raise repo_sync.RepoSyncError(error_output(content_result) or "git cat-file failed")
    content = content_result.stdout
    return {
        "path": path,
        "mode": mode,
        "oid": oid,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def paths_for_changes(changes: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            descriptor["path"]
            for change in changes
            for descriptor in (change.get("old"), change.get("new"))
            if isinstance(descriptor, dict)
        }
    )


def expected_post(changes: list[dict[str, Any]]) -> dict[str, dict[str, Any] | None]:
    post: dict[str, dict[str, Any] | None] = {}
    for change in changes:
        old = change.get("old")
        new = change.get("new")
        if isinstance(old, dict):
            post[old["path"]] = None if change["status"].startswith(("D", "R")) else old
        if isinstance(new, dict):
            post[new["path"]] = new
    return post


def stage_failure(
    details: dict[str, Any],
    stage: str,
    result: subprocess.CompletedProcess[bytes],
    fallback: str,
) -> tuple[dict[str, Any], str]:
    details.update(
        {
            "failed_stage": stage,
            "failed_stdout": text_output(result),
            "failed_stderr": error_output(result),
        }
    )
    return details, error_output(result) or text_output(result) or fallback


def whitespace_findings(repo: Path, args: list[str]) -> list[str]:
    checked = repo_sync.run_git(
        repo,
        ["-c", "core.whitespace=trailing-space,space-before-tab", "diff", "--check", *args],
    )
    stdout = text_output(checked)
    stderr = error_output(checked)
    if checked.returncode not in {0, 2} or (checked.returncode == 2 and not stdout):
        raise repo_sync.RepoSyncError(stderr or "git diff --check failed")
    return stdout.splitlines() if stdout else []


def validate_patch_in_disposable_clone(
    target_repo: Path,
    target_head: str,
    patch: bytes,
    changes: list[dict[str, Any]],
    *,
    use_actual_worktree: bool = True,
) -> tuple[dict[str, Any], str | None]:
    with tempfile.TemporaryDirectory(prefix="sync-receive-") as temp:
        index_clone = Path(temp) / "index-target"
        clone_at(target_repo, target_head, index_clone)
        summary = repo_sync.run_git(index_clone, ["apply", "--summary"], input_data=patch)
        cached_check = repo_sync.run_git(
            index_clone,
            ["apply", "--cached", "--binary", "--whitespace=nowarn", "--check"],
            input_data=patch,
        )
        details = {
            "summary": text_output(summary),
            "check_returncode": cached_check.returncode,
            "check_stderr": error_output(cached_check),
            "index_contract": "not-run",
            "worktree_applicability": "not-run",
            "disposable_apply": "not-run",
            "postimage_content": "not-run",
        }
        if cached_check.returncode:
            return stage_failure(details, "cached-apply-check", cached_check, "git apply --cached --check failed")
        cached_apply = repo_sync.run_git(
            index_clone,
            ["apply", "--cached", "--binary", "--whitespace=nowarn"],
            input_data=patch,
        )
        if cached_apply.returncode:
            return stage_failure(details, "cached-apply", cached_apply, "git apply --cached failed")
        for path, expected in expected_post(changes).items():
            if not same_blob(index_descriptor(index_clone, path), expected):
                details["failed_stage"] = "postimage-blob"
                return details, f"post-apply blob mismatch at {path}"
        try:
            final_files, final_contents = repo_sync.index_inventory(index_clone, enforce_lf=False)
        except repo_sync.TextEolError as exc:
            details.update(
                {
                    "failed_stage": "cached-text-eol",
                    "text_eol_paths": exc.paths,
                }
            )
            return details, str(exc)
        canonical_text_violations = sorted(
            path
            for path, expected in expected_post(changes).items()
            if isinstance(expected, dict)
            and expected.get("mode") != "120000"
            and (
                expected.get("text") is True
                or (expected.get("text") is None and b"\0" not in final_contents[path])
            )
            and b"\r" in final_contents[path]
        )
        if canonical_text_violations:
            details.update(
                {
                    "failed_stage": "cached-text-eol",
                    "text_eol_paths": canonical_text_violations,
                }
            )
            return details, str(repo_sync.TextEolError(canonical_text_violations))
        postimages = {
            path: expected
            for path, expected in expected_post(changes).items()
            if isinstance(expected, dict)
        }
        final_attributes = repo_sync.index_attributes(index_clone, list(postimages), ["text"])
        attribute_mismatches = sorted(
            path
            for path, expected in postimages.items()
            if expected.get("text") is False
            and expected.get("text_attribute") == "unset"
            and b"\r" in final_contents[path]
            and final_attributes[path]["text"] != "unset"
        )
        details.update(
            {
                "index_contract": "passed",
                "postimage_content": "passed",
                "whitespace_findings": whitespace_findings(index_clone, ["--cached"]),
            }
        )
        if attribute_mismatches:
            details.update(
                {
                    "failed_stage": "binary-attribute-scope",
                    "worktree_applicability": "failed",
                    "attribute_mismatch_paths": attribute_mismatches,
                }
            )
            return (
                details,
                "Canonical binary attributes are absent from target scope: "
                + ", ".join(attribute_mismatches),
            )
        lf_violations = repo_sync.lf_worktree_violations(index_clone, final_files)
        if lf_violations:
            details.update(
                {
                    "failed_stage": "lf-worktree-policy",
                    "worktree_applicability": "failed",
                    "worktree_mismatches": lf_violations,
                }
            )
            return details, f"Target cannot keep canonical text as LF: {', '.join(lf_violations)}"

        worktree_clone = Path(temp) / "worktree-target"
        if use_actual_worktree:
            clone_at(
                target_repo,
                target_head,
                worktree_clone,
                worktree_source=target_repo,
                unchanged_paths=tracked_paths(target_repo),
            )
        else:
            clone_at(target_repo, target_head, worktree_clone)
        worktree_check = repo_sync.run_git(
            worktree_clone,
            ["apply", "--binary", "--whitespace=nowarn", "--check"],
            input_data=patch,
        )
        if worktree_check.returncode:
            details["worktree_applicability"] = "failed"
            return stage_failure(details, "worktree-apply-check", worktree_check, "git apply --check failed")
        worktree_apply = repo_sync.run_git(
            worktree_clone,
            ["apply", "--binary", "--whitespace=nowarn"],
            input_data=patch,
        )
        if worktree_apply.returncode:
            details["worktree_applicability"] = "failed"
            return stage_failure(details, "worktree-apply", worktree_apply, "git apply failed")
        paths = paths_for_changes(changes)
        staged = repo_sync.run_git(worktree_clone, ["add", "-A", "--", *paths])
        if staged.returncode:
            details["worktree_applicability"] = "failed"
            return stage_failure(details, "worktree-stage", staged, "staging validation diff failed")
        for path, expected in expected_post(changes).items():
            if not same_blob(index_descriptor(worktree_clone, path), expected):
                details.update({"failed_stage": "worktree-postimage-blob", "worktree_applicability": "failed"})
                return details, f"worktree post-apply blob mismatch at {path}"
        try:
            worktree_files, _ = repo_sync.index_inventory(worktree_clone, enforce_lf=False)
        except repo_sync.TextEolError as exc:
            details.update(
                {
                    "failed_stage": "worktree-text-eol",
                    "worktree_applicability": "failed",
                    "text_eol_paths": exc.paths,
                }
            )
            return details, str(exc)
        worktree_policy = set(repo_sync.lf_worktree_violations(worktree_clone, worktree_files))
        physical_mismatches = {
            item["path"]
            for item in final_files
            if item["text"] is True
            and (
                not (worktree_clone / item["path"]).is_file()
                or (worktree_clone / item["path"]).read_bytes() != final_contents[item["path"]]
            )
        }
        worktree_mismatches = set(repo_sync.tracked_worktree_mismatches(worktree_clone))
        worktree_mismatches.update(worktree_policy)
        worktree_mismatches.update(physical_mismatches)
        if worktree_mismatches:
            paths = sorted(worktree_mismatches)
            details.update(
                {
                    "failed_stage": "worktree-postimage",
                    "worktree_applicability": "failed",
                    "worktree_mismatches": paths,
                }
            )
            return details, f"Target cannot keep canonical text as LF: {', '.join(paths)}"
        details.update({"worktree_applicability": "passed", "disposable_apply": "passed"})
        return details, None


def legacy_pure_renames(patch: bytes) -> list[tuple[str, str]]:
    try:
        text = patch.decode("utf-8")
    except UnicodeDecodeError:
        return []
    pairs: list[tuple[str, str]] = []
    for block in text.split("diff --git ")[1:]:
        lines = block.splitlines()
        old = next((line[12:] for line in lines if line.startswith("rename from ")), None)
        new = next((line[10:] for line in lines if line.startswith("rename to ")), None)
        if old is None or new is None or "similarity index 100%" not in lines:
            return []
        if any(line.startswith(("--- ", "+++ ", "@@", "GIT binary patch")) for line in lines):
            return []
        pairs.append((old, new))
    return pairs


def change_state(target_repo: Path, target_head: str, change: dict[str, Any]) -> str:
    status = str(change.get("status", ""))
    old = change.get("old")
    new = change.get("new")
    if status.startswith("R") and isinstance(old, dict) and isinstance(new, dict):
        old_actual = repo_sync.blob_descriptor(target_repo, target_head, old["path"])
        new_actual = repo_sync.blob_descriptor(target_repo, target_head, new["path"])
        old_matches = same_blob(old_actual, old)
        new_matches = same_blob(new_actual, new)
        if old_actual is None and new_actual is None:
            return "missing-preimage"
        if old_matches and new_actual is None:
            return "pre"
        if old_actual is None and new_matches:
            return "post"
        if old_matches and new_matches:
            return "partial"
        if old_actual is not None and not old_matches and new_actual is None:
            return "baseline-mismatch"
        return "conflict"
    path_descriptor = new if isinstance(new, dict) else old
    if not isinstance(path_descriptor, dict):
        return "conflict"
    actual = repo_sync.blob_descriptor(target_repo, target_head, path_descriptor["path"])
    if same_blob(actual, new):
        return "post"
    if same_blob(actual, old):
        return "pre"
    return "baseline-mismatch" if actual is not None else "conflict"


def build_add_patch(changes: list[dict[str, Any]]) -> bytes:
    with tempfile.TemporaryDirectory(prefix="sync-add-patch-") as temp:
        repo = Path(temp)
        init = subprocess.run(
            ["git", "init", "--quiet", str(repo)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if init.returncode:
            raise repo_sync.RepoSyncError(error_output(init) or "temporary git init failed")
        for change in changes:
            new = change["new"]
            content = descriptor_content(new)
            if content is None:
                raise repo_sync.RepoSyncError(f"Destination blob content is absent for {new['path']}")
            stored = repo_sync.run_git(repo, ["hash-object", "-w", "--stdin"], input_data=content)
            if stored.returncode:
                raise repo_sync.RepoSyncError(error_output(stored) or "git hash-object failed")
            oid = text_output(stored)
            indexed = repo_sync.run_git(
                repo,
                ["update-index", "--add", "--cacheinfo", new["mode"], oid, new["path"]],
            )
            if indexed.returncode:
                raise repo_sync.RepoSyncError(error_output(indexed) or "git update-index failed")
        empty = repo_sync.run_git(repo, ["mktree"], input_data=b"")
        if empty.returncode:
            raise repo_sync.RepoSyncError(error_output(empty) or "git mktree failed")
        paths = paths_for_changes(changes)
        patch = repo_sync.run_git(
            repo,
            ["diff", "--cached", "--binary", "--full-index", "--no-renames", text_output(empty), "--", *paths],
        )
        if patch.returncode or not patch.stdout:
            raise repo_sync.RepoSyncError(error_output(patch) or "target-aware patch generation failed")
        return patch.stdout


def three_way_probe(target_repo: Path, target_head: str, patch: bytes, requested: bool) -> dict[str, Any]:
    if not requested:
        return {"requested": False}
    with tempfile.TemporaryDirectory(prefix="sync-three-way-") as temp:
        clone = Path(temp) / "target"
        clone_at(target_repo, target_head, clone)
        result = repo_sync.run_git(
            clone,
            ["apply", "--binary", "--whitespace=nowarn", "--3way", "--check"],
            input_data=patch,
        )
        message = "\n".join(part for part in (text_output(result), error_output(result)) if part)
        return {
            "requested": True,
            "returncode": result.returncode,
            "message": message,
            "conflicts": "conflict" in message.lower(),
            "permission_to_apply": False,
        }


def handoff_for_missing_blob(
    bundle: Path,
    target_id: str,
    target_head: str,
    pairs: list[tuple[str, str]],
    *,
    content_available: bool = False,
) -> dict[str, str]:
    paths = ", ".join(f"{old} -> {new}" for old, new in pairs)
    next_step = (
        "Verified destination blob content is available; generate a target-aware candidate with the exact command below."
        if content_available
        else "The bundle does not contain verified destination blob content; re-export from the source with "
        "sync_workflow.py export against a clean local checkout of this target HEAD."
    )
    return {"prompt": (
        f"Target {target_id} HEAD {target_head}: pure rename preimage is missing for {paths}. "
        f"Bundle {bundle.name}: {next_step} "
        "Do not create an empty placeholder or edit the patch."
    )}


def create_replacement(
    manifest: dict[str, Any],
    original_patch: bytes,
    target_repo: Path,
    target_id: str,
    target_head: str,
    output: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if output.exists():
        raise repo_sync.RepoSyncError(f"Replacement output already exists: {output}")
    rename_changes = list(manifest["changes"])
    add_changes: list[dict[str, Any]] = []
    destination_hashes: list[str] = []
    for change in rename_changes:
        new = dict(change["new"])
        if descriptor_content(new) is None:
            raise repo_sync.RepoSyncError(f"Destination blob content is absent for {new['path']}")
        destination_hashes.append(new["sha256"])
        add_changes.append({"status": "A", "old": None, "new": new})
    patch = build_add_patch(add_changes)
    replacement = dict(manifest)
    replacement.update(
        {
            "kind": "target-aware-add",
            "target": {"id": target_id, "expected_head": target_head},
            "paths": [change["new"]["path"] for change in add_changes],
            "changes": add_changes,
            "patch_bytes": len(patch),
            "patch_sha256": hashlib.sha256(patch).hexdigest(),
            "replaces_patch_sha256": hashlib.sha256(original_patch).hexdigest(),
            "replacement_reason": "missing-pure-rename-preimage",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    replacement["handoff"] = repo_sync.build_handoff_contract(
        str(replacement.get("channel", "external-to-company")),
        str(replacement.get("base", "")),
        str(replacement.get("head", "")),
        replacement["target"],
        replacement["paths"],
        add_changes,
        replacement["patch_sha256"],
    )
    validation, error = validate_patch_in_disposable_clone(target_repo, target_head, patch, add_changes)
    if error:
        raise repo_sync.RepoSyncError(f"Target-aware replacement validation failed: {error}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(repo_sync.encode_payload(repo_sync.build_payload(replacement, patch)), encoding="utf-8")
    info: dict[str, Any] = {
        "bundle": str(output.resolve()),
        "bundle_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "patch_sha256": replacement["patch_sha256"],
        "validation": validation,
    }
    if len(destination_hashes) == 1:
        info["destination_sha256"] = destination_hashes[0]
    else:
        info["destination_sha256"] = destination_hashes
    return replacement, info


def analyze_bundle(
    bundle: Path,
    target_repo_arg: Path,
    target_id: str,
    *,
    replacement_output: Path | None,
    check_threeway: bool,
) -> dict[str, Any]:
    target_repo = repo_sync.require_git_repo(target_repo_arg.resolve())
    target_head = repo_sync.git_output(target_repo, ["rev-parse", "HEAD^{commit}"])
    target_info = {"id": target_id, "repo": str(target_repo), "head": target_head}
    if repo_sync.is_dirty(target_repo):
        return result_report(UNSAFE, "DIRTY_WORKTREE", bundle=str(bundle.resolve()), target=target_info)
    try:
        manifest, patch = repo_sync.read_bundle(bundle.resolve())
    except repo_sync.TextEolError as exc:
        return result_report(
            UNSAFE,
            "TEXT_EOL_NOT_LF",
            bundle=str(bundle.resolve()),
            target=target_info,
            error=str(exc),
            paths=exc.paths,
        )
    except (OSError, repo_sync.RepoSyncError) as exc:
        return result_report(UNSAFE, "INVALID_BUNDLE", bundle=str(bundle.resolve()), target=target_info, error=str(exc))
    bound_target = manifest.get("target")
    if isinstance(bound_target, dict) and bound_target.get("id") != target_id:
        return result_report(
            UNSAFE,
            "TARGET_CONTEXT_MISMATCH",
            bundle=str(bundle.resolve()),
            target=target_info,
            expected_target=bound_target,
        )
    summary = repo_sync.run_git(target_repo, ["apply", "--summary"], input_data=patch)
    patch_info = {
        "sha256": hashlib.sha256(patch).hexdigest(),
        "summary": text_output(summary),
        "summary_stderr": error_output(summary),
    }
    changes = manifest.get("changes")
    if not isinstance(changes, list) or not changes:
        pairs = legacy_pure_renames(patch)
        if pairs and any(repo_sync.blob_descriptor(target_repo, target_head, old) is None for old, _ in pairs):
            return result_report(
                NEEDS_BASELINE,
                "MISSING_PREIMAGE",
                bundle=str(bundle.resolve()),
                target=target_info,
                patch=patch_info,
                handoff=handoff_for_missing_blob(bundle, target_id, target_head, pairs),
            )
        return result_report(
            UNSAFE,
            "MISSING_CONTENT_BASELINE",
            bundle=str(bundle.resolve()),
            target=target_info,
            patch=patch_info,
            handoff={"prompt": "Re-export with sync_workflow.py export; this bundle lacks verifiable pre/post blob metadata."},
        )
    try:
        for change in changes:
            new = change.get("new")
            if str(change.get("status", "")).startswith("R") and isinstance(new, dict):
                descriptor_content(new)
    except repo_sync.RepoSyncError as exc:
        return result_report(UNSAFE, "INVALID_CONTENT_METADATA", bundle=str(bundle.resolve()), target=target_info, error=str(exc))
    ignore_case_result = repo_sync.run_git(target_repo, ["config", "--bool", "core.ignorecase"])
    ignore_case = ignore_case_result.returncode == 0 and text_output(ignore_case_result) == "true"
    if ignore_case and any(
        str(change.get("status", "")).startswith("R")
        and change["old"]["path"] != change["new"]["path"]
        and change["old"]["path"].casefold() == change["new"]["path"].casefold()
        for change in changes
    ):
        return result_report(UNSAFE, "UNSUPPORTED_PLATFORM", bundle=str(bundle.resolve()), target=target_info, patch=patch_info)
    states = [change_state(target_repo, target_head, change) for change in changes]
    if all(state == "post" for state in states):
        return result_report(ALREADY, "ALREADY_APPLIED", bundle=str(bundle.resolve()), target=target_info, patch=patch_info)
    if any(state == "partial" for state in states) or (
        any(state == "post" for state in states) and any(state != "post" for state in states)
    ):
        return result_report(ALREADY, "PARTIALLY_APPLIED", bundle=str(bundle.resolve()), target=target_info, patch=patch_info)
    if any(state == "conflict" for state in states):
        return result_report(CONFLICT, "NORMAL_CONFLICT", bundle=str(bundle.resolve()), target=target_info, patch=patch_info)
    if any(state == "baseline-mismatch" for state in states):
        return result_report(
            NEEDS_BASELINE,
            "BASELINE_MISMATCH",
            bundle=str(bundle.resolve()),
            target=target_info,
            patch=patch_info,
            expected_target=bound_target,
            three_way=three_way_probe(target_repo, target_head, patch, check_threeway),
        )
    if any(state == "missing-preimage" for state in states):
        pure_missing = all(
            state == "missing-preimage" and str(change.get("status", "")) == "R100"
            for state, change in zip(states, changes)
        )
        content_available = pure_missing and all(
            isinstance(change.get("new"), dict) and descriptor_content(change["new"]) is not None
            for change in changes
        )
        if replacement_output is not None and content_available:
            try:
                _, replacement = create_replacement(
                    manifest,
                    patch,
                    target_repo,
                    target_id,
                    target_head,
                    replacement_output.resolve(),
                )
            except repo_sync.RepoSyncError as exc:
                return result_report(UNSAFE, "REPLACEMENT_VALIDATION_FAILED", bundle=str(bundle.resolve()), target=target_info, error=str(exc))
            return result_report(
                READY,
                "TARGET_AWARE_REPLACEMENT",
                bundle=str(bundle.resolve()),
                target=target_info,
                patch=patch_info,
                replacement=replacement,
                validation=replacement["validation"],
            )
        pairs = [
            (change["old"]["path"], change["new"]["path"])
            for change in changes
            if str(change.get("status", "")).startswith("R")
        ]
        handoff = handoff_for_missing_blob(
            bundle,
            target_id,
            target_head,
            pairs,
            content_available=content_available,
        )
        if content_available:
            suggested = bundle.with_name(f"{bundle.stem}-for-{target_head[:12]}.sync")
            handoff["command"] = shlex.join(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "receive",
                    str(bundle.resolve()),
                    "--target-repo",
                    str(target_repo),
                    "--target-id",
                    target_id,
                    "--replacement-output",
                    str(suggested),
                    "--report",
                    str(suggested.with_suffix(".json")),
                ]
            )
        return result_report(
            NEEDS_BASELINE,
            "MISSING_PREIMAGE",
            bundle=str(bundle.resolve()),
            target=target_info,
            patch=patch_info,
            handoff=handoff,
        )
    if not all(state == "pre" for state in states):
        return result_report(CONFLICT, "NORMAL_CONFLICT", bundle=str(bundle.resolve()), target=target_info, patch=patch_info)
    if not isinstance(bound_target, dict) or bound_target.get("expected_head") != target_head:
        return result_report(
            NEEDS_BASELINE,
            "BASELINE_MISMATCH",
            bundle=str(bundle.resolve()),
            target=target_info,
            patch=patch_info,
            expected_target=bound_target,
            three_way=three_way_probe(target_repo, target_head, patch, check_threeway),
        )
    validation, error = validate_patch_in_disposable_clone(target_repo, target_head, patch, changes)
    if error:
        if validation.get("attribute_mismatch_paths"):
            return result_report(
                UNSAFE,
                "ATTRIBUTE_SCOPE_MISMATCH",
                bundle=str(bundle.resolve()),
                target=target_info,
                patch=patch_info,
                validation=validation,
                paths=validation["attribute_mismatch_paths"],
                whitespace_findings=validation.get("whitespace_findings", []),
                error=error,
            )
        if validation.get("text_eol_paths"):
            return result_report(
                UNSAFE,
                "TEXT_EOL_NOT_LF",
                bundle=str(bundle.resolve()),
                target=target_info,
                patch=patch_info,
                validation=validation,
                paths=validation["text_eol_paths"],
                whitespace_findings=validation.get("whitespace_findings", []),
                error=error,
            )
        if validation.get("index_contract") == "passed":
            return result_report(
                UNSAFE,
                "INDEX_CONTRACT_ONLY",
                bundle=str(bundle.resolve()),
                target=target_info,
                patch=patch_info,
                validation=validation,
                whitespace_findings=validation.get("whitespace_findings", []),
                error=error,
            )
        return result_report(
            CONFLICT,
            "NORMAL_CONFLICT",
            bundle=str(bundle.resolve()),
            target=target_info,
            patch=patch_info,
            validation=validation,
            whitespace_findings=validation.get("whitespace_findings", []),
            error=error,
        )
    return result_report(
        READY,
        "CLEAN_APPLY",
        bundle=str(bundle.resolve()),
        target=target_info,
        patch=patch_info,
        validation=validation,
        whitespace_findings=validation.get("whitespace_findings", []),
    )


def receive_command(args: argparse.Namespace) -> dict[str, Any]:
    report = analyze_bundle(
        args.bundle,
        args.target_repo,
        args.target_id,
        replacement_output=args.replacement_output,
        check_threeway=args.check_3way,
    )
    add_bundle_receipt(report, args.bundle.resolve())
    write_report(args.report.resolve(), report)
    return report


def export_command(args: argparse.Namespace) -> dict[str, Any]:
    source = repo_sync.require_git_repo(args.source_repo.resolve())
    target = repo_sync.require_git_repo(args.target_repo.resolve())
    if repo_sync.is_dirty(source):
        report = result_report(UNSAFE, "DIRTY_SOURCE_WORKTREE", source_repo=str(source), target={"repo": str(target)})
        write_report(args.report.resolve(), report)
        return report
    if repo_sync.is_dirty(target):
        report = result_report(UNSAFE, "DIRTY_WORKTREE", source_repo=str(source), target={"repo": str(target)})
        write_report(args.report.resolve(), report)
        return report
    base = repo_sync.git_output(source, ["rev-parse", f"{args.base}^{{commit}}"])
    head = repo_sync.git_output(source, ["rev-parse", f"{args.head}^{{commit}}"])
    try:
        repo_sync.describe_changes(source, base, head, args.path)
    except repo_sync.TextEolError as exc:
        report = result_report(
            UNSAFE,
            "TEXT_EOL_NOT_LF",
            source_repo=str(source),
            error=str(exc),
            paths=exc.paths,
        )
        write_report(args.report.resolve(), report)
        return report
    source_whitespace = whitespace_findings(source, [base, head, "--", *args.path])
    command = [
        sys.executable,
        str(Path(repo_sync.__file__).resolve()),
        "export",
        str(source),
        "--base",
        base,
        "--head",
        head,
        "--target-repo",
        str(target),
        "--target-id",
        args.target_id,
        "--channel",
        args.channel,
        "--no-update-state",
        "--output",
        str(args.output.resolve()),
    ]
    for path in args.path:
        command.extend(["--path", path])
    exported = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if exported.returncode:
        report = result_report(
            UNSAFE,
            "EXPORT_FAILED",
            source_repo=str(source),
            target={"repo": str(target)},
            error=error_output(exported),
        )
        write_report(args.report.resolve(), report)
        return report
    report = analyze_bundle(
        args.output,
        target,
        args.target_id,
        replacement_output=args.replacement_output,
        check_threeway=args.check_3way,
    )
    add_bundle_receipt(report, args.output.resolve())
    report["whitespace_findings"] = sorted(
        set(source_whitespace) | set(report.get("whitespace_findings", []))
    )
    report["source_preflight"] = {
        "repo": str(source),
        "base": base,
        "head": head,
        "paths": args.path,
        "diff_check": "completed",
        "export_stdout": text_output(exported),
        "state_updated": False,
    }
    write_report(args.report.resolve(), report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Target-aware .sync export and receive validation")
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="export and validate against the current target HEAD")
    export.add_argument("source_repo", type=Path)
    export.add_argument("--base", required=True)
    export.add_argument("--head", default="HEAD")
    export.add_argument("--path", action="append", required=True)
    export.add_argument("--target-repo", required=True, type=Path)
    export.add_argument("--target-id", required=True)
    export.add_argument("--output", required=True, type=Path)
    export.add_argument("--replacement-output", type=Path)
    export.add_argument("--report", required=True, type=Path)
    export.add_argument("--channel", default="external-to-company")
    export.add_argument("--check-3way", action="store_true")
    export.set_defaults(func=export_command)
    receive = commands.add_parser("receive", help="inspect and validate without changing the target")
    receive.add_argument("bundle", type=Path)
    receive.add_argument("--target-repo", required=True, type=Path)
    receive.add_argument("--target-id", required=True)
    receive.add_argument("--replacement-output", type=Path)
    receive.add_argument("--report", required=True, type=Path)
    receive.add_argument("--check-3way", action="store_true")
    receive.set_defaults(func=receive_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = args.func(args)
    except (OSError, repo_sync.RepoSyncError) as exc:
        report = result_report(UNSAFE, "UNSAFE_ERROR", error=str(exc))
        write_report(args.report.resolve(), report)
    print(json.dumps(report, sort_keys=True))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
