#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import repo_sync  # noqa: E402

REPO_SYNC = SCRIPTS / "repo_sync.py"
VALIDATE = SCRIPTS / "validate_sync_bundle.py"
RENDER = SCRIPTS / "render_sync_docs.py"
WORKFLOW = SCRIPTS / "sync_workflow.py"
SKILL_DOC = SCRIPTS.parent / "SKILL.md"
VALIDATION_GUIDE = SCRIPTS.parent / "references" / "validation-and-outputs.md"


def run(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def make_repo(root: Path) -> tuple[Path, str, str]:
    repo = root / "source"
    repo.mkdir()
    run("git", "init", "-q", str(repo))
    run("git", "config", "user.email", "test@example.invalid", cwd=repo)
    run("git", "config", "user.name", "Sync Test", cwd=repo)
    (repo / "service.txt").write_text("before\n", encoding="utf-8")
    run("git", "add", "service.txt", cwd=repo)
    run("git", "commit", "-qm", "baseline", cwd=repo)
    base = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
    (repo / "service.txt").write_text("after\n", encoding="utf-8")
    (repo / "new.txt").write_text("new file\n", encoding="utf-8")
    run("git", "add", "service.txt", "new.txt", cwd=repo)
    run("git", "commit", "-qm", "product change", cwd=repo)
    head = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
    return repo, base, head


def make_rename_repo(root: Path) -> tuple[Path, str, str]:
    repo = root / "rename-source"
    repo.mkdir()
    run("git", "init", "-q", str(repo))
    run("git", "config", "user.email", "test@example.invalid", cwd=repo)
    run("git", "config", "user.name", "Sync Test", cwd=repo)
    (repo / "old.txt").write_text("alpha\nbeta\ngamma\ndelta\n", encoding="utf-8")
    run("git", "add", "old.txt", cwd=repo)
    run("git", "commit", "-qm", "baseline", cwd=repo)
    base = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
    run("git", "mv", "old.txt", "new.txt", cwd=repo)
    (repo / "new.txt").write_text("alpha\nbeta changed\ngamma\ndelta\n", encoding="utf-8")
    run("git", "add", "new.txt", cwd=repo)
    run("git", "commit", "-qm", "rename product file", cwd=repo)
    head = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
    return repo, base, head


def make_pure_rename_repo(
    root: Path,
    *,
    old_path: str = "old.txt",
    new_path: str = "new.txt",
) -> tuple[Path, str, str, bytes]:
    repo = root / "pure-rename-source"
    repo.mkdir()
    run("git", "init", "-q", str(repo))
    run("git", "config", "user.email", "test@example.invalid", cwd=repo)
    run("git", "config", "user.name", "Sync Test", cwd=repo)
    content = b"expected production content\nsecond line\n"
    (repo / old_path).write_bytes(content)
    run("git", "add", old_path, cwd=repo)
    run("git", "commit", "-qm", "baseline", cwd=repo)
    base = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
    if old_path.casefold() == new_path.casefold():
        temporary = f"{old_path}.case-tmp"
        run("git", "mv", old_path, temporary, cwd=repo)
        run("git", "mv", temporary, new_path, cwd=repo)
    else:
        run("git", "mv", old_path, new_path, cwd=repo)
    run("git", "commit", "-qm", "pure rename", cwd=repo)
    head = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
    return repo, base, head, content


def clone_at(repo: Path, destination: Path, revision: str) -> None:
    run("git", "clone", "--quiet", "--no-hardlinks", str(repo), str(destination))
    run("git", "checkout", "--quiet", "--detach", revision, cwd=destination)


class SyncToolsTest(unittest.TestCase):
    def test_workflow_export_normal_text_is_ready_and_captures_target_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head = make_repo(root)
            target = root / "target"
            clone_at(repo, target, base)
            target_head = run("git", "rev-parse", "HEAD", cwd=target).stdout.strip()
            bundle = root / "normal.sync"
            report = root / "normal-report.json"
            result = run(
                sys.executable,
                str(WORKFLOW),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--path",
                "service.txt",
                "--path",
                "new.txt",
                "--output",
                str(bundle),
                "--report",
                str(report),
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["outcome"], "READY")
            self.assertEqual(data["classification"], "CLEAN_APPLY")
            self.assertEqual(data["target"]["head"], target_head)
            self.assertEqual(data["validation"]["disposable_apply"], "passed")
            self.assertEqual(data["candidate_bundle_sha256"], hashlib.sha256(bundle.read_bytes()).hexdigest())
            self.assertFalse(data["real_target_modified"])
            self.assertEqual(run("git", "rev-parse", "HEAD", cwd=target).stdout.strip(), target_head)
            self.assertEqual(run("git", "status", "--porcelain", cwd=target).stdout, "")
            manifest, _ = repo_sync.read_bundle(bundle)
            self.assertEqual(manifest["target"], {"id": "pd-internal", "expected_head": target_head})
            self.assertEqual(len(manifest["changes"]), 2)
            contract = manifest["handoff"]
            self.assertEqual(contract["contract_version"], 1)
            self.assertEqual(contract["direction"], "external-to-company")
            self.assertEqual(contract["source"], {"base": base, "head": head})
            self.assertEqual(contract["expected_target_checkpoint"], manifest["target"])
            self.assertEqual(contract["scope"]["paths"], ["service.txt", "new.txt"])
            self.assertEqual(contract["integrity"]["patch_sha256"], manifest["patch_sha256"])
            self.assertIn("dependency_manifest_policy", contract["scope"])
            self.assertIn("capture_actual_target_head", contract["allowed_automatic_operations"])
            self.assertEqual(
                contract["required_validation_sequence"][:3],
                ["inspect", "verify_hashes", "capture_actual_target_head"],
            )
            self.assertIn("missing_or_mismatched_preimage", contract["stop_conditions"])
            receipt = contract["receipt_template"]
            self.assertEqual(receipt["real_target_modified"], False)
            for field in ("apply_summary", "post_apply_diff_sha256", "tests", "commit"):
                self.assertIn(field, receipt)

    def test_workflow_generates_validated_replacement_for_missing_pure_rename_preimage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head, content = make_pure_rename_repo(root)
            target = root / "target"
            clone_at(repo, target, base)
            run("git", "rm", "-q", "old.txt", cwd=target)
            run("git", "config", "user.email", "test@example.invalid", cwd=target)
            run("git", "config", "user.name", "Sync Test", cwd=target)
            run("git", "commit", "-qm", "target removed preimage", cwd=target)
            original = root / "rename.sync"
            replacement = root / "rename-target-aware.sync"
            report = root / "rename-report.json"
            result = run(
                sys.executable,
                str(WORKFLOW),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--path",
                "old.txt",
                "--path",
                "new.txt",
                "--output",
                str(original),
                "--replacement-output",
                str(replacement),
                "--report",
                str(report),
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["outcome"], "READY")
            self.assertEqual(data["classification"], "TARGET_AWARE_REPLACEMENT")
            self.assertEqual(data["replacement"]["destination_sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(data["candidate_bundle_sha256"], hashlib.sha256(replacement.read_bytes()).hexdigest())
            replacement_manifest, replacement_patch = repo_sync.read_bundle(replacement)
            self.assertEqual(replacement_manifest["kind"], "target-aware-add")
            self.assertIn(b"new file mode", replacement_patch)
            self.assertIn(b"+expected production content", replacement_patch)
            inspected = run(sys.executable, str(REPO_SYNC), "inspect", str(original))
            inspect_manifest = json.loads(inspected.stdout)
            self.assertNotIn("content_b85", inspected.stdout)
            self.assertTrue(inspect_manifest["changes"][0]["new"]["content_embedded"])
            self.assertFalse((target / "old.txt").exists())
            self.assertFalse((target / "new.txt").exists())

            recommendation_report = root / "recommendation-report.json"
            recommendation = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(original),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(recommendation_report),
                check=False,
            )
            self.assertNotEqual(recommendation.returncode, 0)
            recommendation_data = json.loads(recommendation_report.read_text())
            self.assertEqual(recommendation_data["classification"], "MISSING_PREIMAGE")
            self.assertIn("verified destination blob content is available", recommendation_data["handoff"]["prompt"].lower())
            self.assertIn("--replacement-output", recommendation_data["handoff"]["command"])

            receive_report = root / "receive-report.json"
            receive = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(replacement),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(receive_report),
                check=False,
            )
            self.assertEqual(receive.returncode, 0, receive.stderr)
            self.assertEqual(json.loads(receive_report.read_text())["classification"], "CLEAN_APPLY")

    def test_raw_pure_rename_rejects_missing_but_accepts_unverified_placeholder_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head, _ = make_pure_rename_repo(root)
            patch = repo_sync.make_patch(repo, base, head, ["old.txt", "new.txt"])
            self.assertIn(b"similarity index 100%", patch)
            self.assertNotIn(b"\nindex ", patch)

            for name, preimage, expected_destination in (
                ("missing", None, None),
                ("empty", b"", b""),
                ("wrong", b"wrong target content\n", b"wrong target content\n"),
            ):
                target = root / f"raw-{name}"
                clone_at(repo, target, base)
                run("git", "rm", "-q", "old.txt", cwd=target)
                if preimage is not None:
                    (target / "old.txt").write_bytes(preimage)
                run("git", "add", "-A", cwd=target)
                run("git", "config", "user.email", "test@example.invalid", cwd=target)
                run("git", "config", "user.name", "Sync Test", cwd=target)
                run("git", "commit", "-qm", f"{name} preimage", cwd=target)
                checked = subprocess.run(
                    ["git", "apply", "--check"],
                    cwd=target,
                    input=patch,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                if preimage is None:
                    self.assertNotEqual(checked.returncode, 0)
                    self.assertIn("old.txt", checked.stderr.decode())
                    continue
                self.assertEqual(checked.returncode, 0, checked.stderr.decode())
                applied = subprocess.run(
                    ["git", "apply"],
                    cwd=target,
                    input=patch,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(applied.returncode, 0, applied.stderr.decode())
                self.assertFalse((target / "old.txt").exists())
                self.assertEqual((target / "new.txt").read_bytes(), expected_destination)

    def test_workflow_missing_legacy_preimage_emits_exact_handoff_without_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head, _ = make_pure_rename_repo(root)
            patch = repo_sync.make_patch(repo, base, head, ["old.txt", "new.txt"])
            manifest = {
                "format": repo_sync.FORMAT,
                "base": base,
                "head": head,
                "source_repo": str(repo.resolve()),
                "paths": ["old.txt", "new.txt"],
                "patch_sha256": hashlib.sha256(patch).hexdigest(),
            }
            bundle = root / "legacy.sync"
            bundle.write_text(repo_sync.encode_payload(repo_sync.build_payload(manifest, patch)), encoding="utf-8")
            target = root / "target"
            clone_at(repo, target, base)
            run("git", "rm", "-q", "old.txt", cwd=target)
            run("git", "config", "user.email", "test@example.invalid", cwd=target)
            run("git", "config", "user.name", "Sync Test", cwd=target)
            run("git", "commit", "-qm", "target removed preimage", cwd=target)
            target_head = run("git", "rev-parse", "HEAD", cwd=target).stdout.strip()
            report = root / "legacy-report.json"
            result = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--replacement-output",
                str(root / "must-not-exist.sync"),
                "--report",
                str(report),
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["outcome"], "NEEDS_REBASE_OR_BASELINE")
            self.assertEqual(data["classification"], "MISSING_PREIMAGE")
            self.assertIn(target_head, data["handoff"]["prompt"])
            self.assertIn("destination blob", data["handoff"]["prompt"].lower())
            self.assertFalse((root / "must-not-exist.sync").exists())

    def test_workflow_rejects_dirty_empty_placeholder_and_wrong_preimage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head, _ = make_pure_rename_repo(root)
            target = root / "target"
            clone_at(repo, target, base)
            bundle = root / "rename.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--no-update-state",
                "--path",
                "old.txt",
                "--path",
                "new.txt",
                "--output",
                str(bundle),
            )
            run("git", "rm", "-q", "old.txt", cwd=target)
            run("git", "config", "user.email", "test@example.invalid", cwd=target)
            run("git", "config", "user.name", "Sync Test", cwd=target)
            run("git", "commit", "-qm", "target removed preimage", cwd=target)
            (target / "old.txt").write_bytes(b"")
            dirty_report = root / "dirty.json"
            dirty = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(dirty_report),
                check=False,
            )
            self.assertNotEqual(dirty.returncode, 0)
            self.assertEqual(json.loads(dirty_report.read_text())["classification"], "DIRTY_WORKTREE")

            (target / "old.txt").write_text("wrong target content\n", encoding="utf-8")
            run("git", "add", "old.txt", cwd=target)
            run("git", "commit", "-qm", "wrong preimage placeholder", cwd=target)
            wrong_report = root / "wrong.json"
            wrong = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(wrong_report),
                check=False,
            )
            self.assertNotEqual(wrong.returncode, 0)
            wrong_data = json.loads(wrong_report.read_text())
            self.assertEqual(wrong_data["outcome"], "NEEDS_REBASE_OR_BASELINE")
            self.assertEqual(wrong_data["classification"], "BASELINE_MISMATCH")

    def test_workflow_classifies_conflict_duplicate_partial_and_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head, content = make_pure_rename_repo(root)
            for state in ("conflict", "duplicate", "partial"):
                target = root / f"target-{state}"
                clone_at(repo, target, base)
                run("git", "config", "user.email", "test@example.invalid", cwd=target)
                run("git", "config", "user.name", "Sync Test", cwd=target)
                if state == "conflict":
                    run("git", "rm", "-q", "old.txt", cwd=target)
                    (target / "new.txt").write_text("different destination\n", encoding="utf-8")
                elif state == "duplicate":
                    run("git", "mv", "old.txt", "new.txt", cwd=target)
                else:
                    (target / "new.txt").write_bytes(content)
                run("git", "add", "-A", cwd=target)
                run("git", "commit", "-qm", state, cwd=target)
                bundle = root / f"{state}.sync"
                report = root / f"{state}.json"
                result = run(
                    sys.executable,
                    str(WORKFLOW),
                    "export",
                    str(repo),
                    "--base",
                    base,
                    "--head",
                    head,
                    "--target-repo",
                    str(target),
                    "--target-id",
                    "pd-internal",
                    "--path",
                    "old.txt",
                    "--path",
                    "new.txt",
                    "--output",
                    str(bundle),
                    "--report",
                    str(report),
                    check=False,
                )
                data = json.loads(report.read_text())
                expected = {
                    "conflict": ("CONFLICT_OR_PATH_MISMATCH", "NORMAL_CONFLICT"),
                    "duplicate": ("ALREADY_OR_PARTIALLY_APPLIED", "ALREADY_APPLIED"),
                    "partial": ("ALREADY_OR_PARTIALLY_APPLIED", "PARTIALLY_APPLIED"),
                }[state]
                self.assertEqual((data["outcome"], data["classification"]), expected)
                self.assertEqual(result.returncode == 0, state in {"duplicate", "partial"})

            target = root / "target-drift"
            clone_at(repo, target, base)
            bound_bundle = root / "bound.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--no-update-state",
                "--path",
                "old.txt",
                "--path",
                "new.txt",
                "--output",
                str(bound_bundle),
            )
            run("git", "config", "user.email", "test@example.invalid", cwd=target)
            run("git", "config", "user.name", "Sync Test", cwd=target)
            (target / "unrelated.txt").write_text("drift\n", encoding="utf-8")
            run("git", "add", "unrelated.txt", cwd=target)
            run("git", "commit", "-qm", "unrelated drift", cwd=target)
            drift_report = root / "drift.json"
            drift = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bound_bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--check-3way",
                "--report",
                str(drift_report),
                check=False,
            )
            self.assertNotEqual(drift.returncode, 0)
            drift_data = json.loads(drift_report.read_text())
            self.assertEqual(drift_data["outcome"], "NEEDS_REBASE_OR_BASELINE")
            self.assertEqual(drift_data["classification"], "BASELINE_MISMATCH")
            self.assertTrue(drift_data["three_way"]["requested"])

    def test_workflow_case_only_rename_respects_platform_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head, _ = make_pure_rename_repo(root, old_path="case.txt", new_path="Case.txt")
            target = root / "target"
            clone_at(repo, target, base)
            ignore_case = run("git", "config", "--bool", "core.ignorecase", cwd=target, check=False).stdout.strip() == "true"
            report = root / "case.json"
            result = run(
                sys.executable,
                str(WORKFLOW),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--path",
                "case.txt",
                "--path",
                "Case.txt",
                "--output",
                str(root / "case.sync"),
                "--report",
                str(report),
                check=False,
            )
            data = json.loads(report.read_text())
            if ignore_case:
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((data["outcome"], data["classification"]), ("UNSAFE_STOP", "UNSUPPORTED_PLATFORM"))
            else:
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(data["outcome"], "READY")

    def test_rename_guidance_has_ordered_diagnostics_and_no_force_rules(self) -> None:
        guidance = VALIDATION_GUIDE.read_text(encoding="utf-8")
        required_sequence = [
            "repo_sync.py inspect",
            "--patch-out",
            "git apply --summary",
            "git apply --check",
            "git apply --3way --check",
        ]
        for item in required_sequence:
            self.assertIn(item, guidance)
        positions = [guidance.index(item) for item in required_sequence]
        self.assertEqual(positions, sorted(positions))
        for category in ("baseline drift", "path-filter defect", "patch defect"):
            self.assertIn(category, guidance.lower())
        self.assertIn("--reject", guidance)
        self.assertIn("hand-edit", guidance.lower())
        for required in (
            "sync_workflow.py export",
            "sync_workflow.py receive",
            "READY",
            "NEEDS_REBASE_OR_BASELINE",
            "CONFLICT_OR_PATH_MISMATCH",
            "ALREADY_OR_PARTIALLY_APPLIED",
            "UNSAFE_STOP",
            "missing preimage",
            "empty placeholder",
            "expected target checkpoint",
            "actual target HEAD",
            "handoff",
            "receipt",
        ):
            self.assertIn(required.lower(), guidance.lower())
        self.assertIn("validation-and-outputs.md", SKILL_DOC.read_text(encoding="utf-8"))

    def test_rename_export_import_check_and_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head = make_rename_repo(root)
            bundle = root / "rename.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--no-update-state",
                "--path",
                "old.txt",
                "--path",
                "new.txt",
                "-o",
                str(bundle),
            )
            _, patch = repo_sync.read_bundle(bundle)
            self.assertIn(b"rename from old.txt", patch)
            self.assertIn(b"rename to new.txt", patch)

            target = root / "target"
            clone_at(repo, target, base)
            checked = run(sys.executable, str(REPO_SYNC), "import", str(bundle), str(target))
            self.assertIn("Checked patch", checked.stdout)
            run(sys.executable, str(REPO_SYNC), "import", str(bundle), str(target), "--apply")
            self.assertFalse((target / "old.txt").exists())
            self.assertEqual((target / "new.txt").read_text(encoding="utf-8"), "alpha\nbeta changed\ngamma\ndelta\n")

    def test_export_rejects_path_filter_that_splits_rename(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head = make_rename_repo(root)
            for selected_path in ("old.txt", "new.txt"):
                with self.subTest(selected_path=selected_path):
                    result = run(
                        sys.executable,
                        str(REPO_SYNC),
                        "export",
                        str(repo),
                        "--base",
                        base,
                        "--head",
                        head,
                        "--no-update-state",
                        "--path",
                        selected_path,
                        "-o",
                        str(root / f"split-{selected_path}.sync"),
                        check=False,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("rename", result.stderr.lower())
                    self.assertIn("old.txt", result.stderr)
                    self.assertIn("new.txt", result.stderr)

    def test_validator_rejects_bundle_with_split_rename_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head = make_rename_repo(root)
            patch = repo_sync.make_patch(repo, base, head, ["new.txt"])
            manifest = {
                "format": repo_sync.FORMAT,
                "base": base,
                "head": head,
                "source_repo": str(repo.resolve()),
                "paths": ["new.txt"],
                "patch_sha256": hashlib.sha256(patch).hexdigest(),
            }
            bundle = root / "legacy-split-rename.sync"
            bundle.write_text(
                repo_sync.encode_payload(repo_sync.build_payload(manifest, patch)),
                encoding="utf-8",
            )
            result = run(
                sys.executable,
                str(VALIDATE),
                "--bundle",
                str(bundle),
                "--source-repo",
                str(repo),
                "--internal-target",
                "pd-internal",
                "--internal-baseline",
                "internal-pd-rename",
                "--validation-repo",
                str(repo),
                "--validation-baseline",
                base,
                "--base",
                base,
                "--head",
                head,
                "--mode",
                "check",
                "--excluded",
                "none",
                "--report",
                str(root / "report.json"),
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("splits rename", result.stderr.lower())

    def test_export_validate_and_render(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head = make_repo(root)
            bundle = root / "aef-change.sync"
            state = root / "exporter-state.json"

            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--channel",
                "external-to-company",
                "--state-file",
                str(state),
                "--path",
                "service.txt",
                "--path",
                "new.txt",
                "-o",
                str(bundle),
            )
            self.assertTrue(bundle.is_file())
            self.assertEqual(json.loads(state.read_text())["channels"]["external-to-company"]["last_export_head"], head)

            report = root / "validation.json"
            run(
                sys.executable,
                str(VALIDATE),
                "--bundle",
                str(bundle),
                "--source-repo",
                str(repo),
                "--internal-target",
                "aef-internal",
                "--internal-baseline",
                "internal-baseline-42",
                "--validation-repo",
                str(repo),
                "--validation-baseline",
                base,
                "--base",
                base,
                "--head",
                head,
                "--mode",
                "full",
                "--excluded",
                "USW and live coordination housekeeping",
                "--report",
                str(report),
            )
            data = json.loads(report.read_text())
            self.assertEqual(data["status"], "passed")
            self.assertEqual(data["internal_target"], "aef-internal")
            self.assertEqual(data["checks"], [
                "payload-inspection",
                "source-patch-match",
                "import-check",
                "temp-clone-apply",
                "diff-check",
            ])

            docs = root / "docs"
            run(
                sys.executable,
                str(RENDER),
                "--report",
                str(report),
                "--included-scope",
                "one product change",
                "--output-dir",
                str(docs),
            )
            note = (docs / "aef-change-transfer-note.md").read_text()
            validation = (docs / "aef-change-validation-report.md").read_text()
            self.assertIn("No transfer or target-side apply was performed", note)
            self.assertIn("USW and live coordination housekeeping", note)
            self.assertIn("temp-clone-apply: passed", validation)

    def test_validator_accepts_resolvable_abbreviated_manifest_base(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head = make_repo(root)
            bundle = root / "short-base.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--no-update-state",
                "--path",
                "service.txt",
                "-o",
                str(bundle),
            )
            manifest, patch = repo_sync.read_bundle(bundle)
            manifest["base"] = base[:7]
            bundle.write_text(repo_sync.encode_payload(repo_sync.build_payload(manifest, patch)), encoding="utf-8")

            run(
                sys.executable,
                str(VALIDATE),
                "--bundle",
                str(bundle),
                "--source-repo",
                str(repo),
                "--internal-target",
                "pd-internal",
                "--internal-baseline",
                "internal-pd-1",
                "--validation-repo",
                str(repo),
                "--validation-baseline",
                base,
                "--base",
                base,
                "--head",
                head,
                "--mode",
                "check",
                "--excluded",
                "none",
                "--report",
                str(root / "report.json"),
            )

    def test_validator_stops_on_unknown_validation_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, head = make_repo(root)
            bundle = root / "change.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--no-update-state",
                "--path",
                "service.txt",
                "-o",
                str(bundle),
            )
            result = run(
                sys.executable,
                str(VALIDATE),
                "--bundle",
                str(bundle),
                "--source-repo",
                str(repo),
                "--internal-target",
                "pd-internal",
                "--internal-baseline",
                "unknown",
                "--validation-repo",
                str(repo),
                "--validation-baseline",
                "not-a-commit",
                "--base",
                base,
                "--head",
                head,
                "--mode",
                "check",
                "--excluded",
                "none",
                "--report",
                str(root / "report.json"),
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("validation baseline is unknown", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
