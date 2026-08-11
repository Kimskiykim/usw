#!/usr/bin/env python3
"""Validate one .sync bundle against explicit source and target baselines."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import repo_sync


def git(repo: Path, *args: str, input_data: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_text(repo: Path, *args: str, label: str = "git command") -> str:
    result = git(repo, *args)
    if result.returncode:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise repo_sync.RepoSyncError(f"{label} failed: {message}")
    return result.stdout.decode("utf-8", "replace").strip()


def resolve_commit(repo: Path, ref: str, label: str) -> str:
    result = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if result.returncode:
        raise repo_sync.RepoSyncError(f"{label} is unknown in {repo}: {ref}")
    return result.stdout.decode().strip()


def clone_at(repo: Path, baseline: str, destination: Path) -> None:
    result = subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", str(repo), str(destination)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise repo_sync.RepoSyncError(result.stderr.decode("utf-8", "replace").strip() or "temp clone failed")
    git_text(destination, "checkout", "--quiet", "--detach", baseline, label="validation baseline checkout")


def validate(args: argparse.Namespace) -> dict[str, object]:
    source = repo_sync.require_git_repo(args.source_repo.resolve())
    validation_repo = repo_sync.require_git_repo(args.validation_repo.resolve())
    base = resolve_commit(source, args.base, "source base")
    head = resolve_commit(source, args.head, "source head")
    validation_baseline = resolve_commit(validation_repo, args.validation_baseline, "validation baseline")
    manifest, patch = repo_sync.read_bundle(args.bundle.resolve())
    manifest_base = resolve_commit(source, str(manifest.get("base", "")), "bundle base")
    manifest_head = resolve_commit(source, str(manifest.get("head", "")), "bundle head")
    if manifest_base != base or manifest_head != head:
        raise repo_sync.RepoSyncError("Bundle base/head do not match the explicit source range")
    manifest_source = Path(str(manifest.get("source_repo", ""))).resolve()
    if manifest_source != source:
        raise repo_sync.RepoSyncError("Bundle source repository does not match --source-repo")
    paths = list(manifest.get("paths", []))
    repo_sync.require_complete_rename_paths(source, base, head, paths)
    source_patch = repo_sync.make_patch(source, base, head, paths)
    if source_patch != patch:
        raise repo_sync.RepoSyncError("Embedded patch does not match the explicit source range and paths")

    checks = ["payload-inspection", "source-patch-match", "import-check"]
    details = {name: "passed" for name in checks}
    with tempfile.TemporaryDirectory(prefix="sync-validation-") as temp:
        target = Path(temp) / "target"
        clone_at(validation_repo, validation_baseline, target)
        repo_sync.apply_patch(target, patch, check=True)
        if args.mode == "full":
            repo_sync.apply_patch(target, patch, check=False)
            git_text(target, "add", "-A", "--", *paths, label="stage validation diff")
            git_text(target, "diff", "--cached", "--check", label="diff check")
            applied_patch = git(
                target,
                "diff",
                "--cached",
                "--binary",
                "--full-index",
                "--find-renames",
                "HEAD",
                "--",
                *paths,
            ).stdout
            if applied_patch != patch:
                raise repo_sync.RepoSyncError("Applied temp-clone diff does not match the embedded patch")
            checks.extend(["temp-clone-apply", "diff-check"])
            details.update({"temp-clone-apply": "passed", "diff-check": "passed"})

    changed_files = git_text(source, "diff", "--name-only", base, head, "--", *manifest.get("paths", [])).splitlines()
    bundle = args.bundle.resolve()
    return {
        "status": "passed",
        "mode": args.mode,
        "bundle": str(bundle),
        "bundle_bytes": bundle.stat().st_size,
        "bundle_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "embedded_patch_sha256": manifest["patch_sha256"],
        "direction": manifest.get("channel"),
        "source_repo": str(source),
        "base": base,
        "head": head,
        "internal_target": args.internal_target,
        "internal_baseline": args.internal_baseline,
        "validation_repo": str(validation_repo),
        "validation_baseline": validation_baseline,
        "changed_files": changed_files,
        "excluded_changes": args.excluded,
        "checks": checks,
        "check_results": details,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--source-repo", required=True, type=Path)
    parser.add_argument("--internal-target", required=True)
    parser.add_argument("--internal-baseline", required=True)
    parser.add_argument("--validation-repo", required=True, type=Path)
    parser.add_argument("--validation-baseline", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--mode", required=True, choices=("check", "full"))
    parser.add_argument("--excluded", required=True, action="append")
    parser.add_argument("--report", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = validate(args)
    except repo_sync.RepoSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Validated {args.bundle} against {args.internal_target} baseline {args.internal_baseline}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
