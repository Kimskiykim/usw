#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import repo_sync  # noqa: E402
import sync_workflow  # noqa: E402

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
    def test_whitespace_tool_failure_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(repo_sync.RepoSyncError, "repository"):
                sync_workflow.whitespace_findings(Path(temp), [])

    def test_whitespace_warning_with_findings_is_nonblocking(self) -> None:
        result = subprocess.CompletedProcess(
            args=["git", "diff", "--check"],
            returncode=2,
            stdout=b"f.txt:1: trailing whitespace.\n",
            stderr=b"warning: advisory message\n",
        )
        with mock.patch.object(repo_sync, "run_git", return_value=result):
            findings = sync_workflow.whitespace_findings(Path("."), [])
        self.assertEqual(findings, ["f.txt:1: trailing whitespace."])

    def test_index_inventory_batch_reads_blobs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            run("git", "init", "-q", str(repo))
            for index in range(75):
                (repo / f"file-{index:03}.txt").write_bytes(b"shared\n")
            run("git", "add", ".", cwd=repo)
            real_popen = subprocess.Popen
            commands: list[list[str]] = []
            batch_inputs: list[bytes] = []

            class RecordingProcess:
                def __init__(self, *args, **kwargs):
                    self.command = args[0]
                    commands.append(self.command)
                    self.process = real_popen(*args, **kwargs)

                def __getattr__(self, name):
                    return getattr(self.process, name)

                def communicate(self, input=None, timeout=None):
                    if "--batch" in self.command:
                        batch_inputs.append(input)
                    return self.process.communicate(input=input, timeout=timeout)

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return self.process.__exit__(*args)

            with mock.patch.object(repo_sync.subprocess, "Popen", RecordingProcess):
                files, blobs = repo_sync.index_inventory(repo)

            cat_commands = [command for command in commands if "cat-file" in command]
            self.assertEqual(len(files), 75)
            self.assertEqual(len(blobs), 75)
            self.assertEqual(len(cat_commands), 1)
            self.assertIn("--batch", cat_commands[0])
            self.assertEqual(batch_inputs[0].count(b"\n"), 1)

    def test_patch_export_rejects_text_crlf_postimage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            run("git", "init", "-q", str(source))
            run("git", "config", "user.email", "test@example.invalid", cwd=source)
            run("git", "config", "user.name", "Sync Test", cwd=source)
            (source / ".gitattributes").write_text("*.txt text\n", encoding="utf-8")
            run("git", "add", ".gitattributes", cwd=source)
            run("git", "commit", "-qm", "base", cwd=source)
            base = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            (source / "bad.txt").write_bytes(b"bad\r\n")
            oid = run("git", "hash-object", "-w", "--no-filters", "bad.txt", cwd=source).stdout.strip()
            run("git", "update-index", "--add", "--cacheinfo", f"100644,{oid},bad.txt", cwd=source)
            run("git", "commit", "-qm", "raw CRLF postimage", cwd=source)
            head = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            (source / ".gitattributes").write_text("bad.txt -text\n", encoding="utf-8")
            run("git", "add", ".gitattributes", cwd=source)
            run("git", "commit", "-qm", "make checkout clean", cwd=source)
            run("git", "reset", "--hard", "-q", "HEAD", cwd=source)
            target = root / "target"
            clone_at(source, target, base)
            report = root / "export.json"

            result = run(
                sys.executable,
                str(WORKFLOW),
                "export",
                str(source),
                "--base",
                base,
                "--head",
                head,
                "--path",
                "bad.txt",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--output",
                str(root / "bad.sync"),
                "--report",
                str(report),
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["classification"], "TEXT_EOL_NOT_LF")
            self.assertEqual(data["paths"], ["bad.txt"])
            self.assertFalse((root / "bad.sync").exists())

    def test_patch_transport_accepts_utf8_bom_and_explains_utf16(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, base, head = make_repo(root)
            target = root / "target"
            clone_at(source, target, base)
            original = root / "original.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(source),
                "--base",
                base,
                "--head",
                head,
                "--path",
                "service.txt",
                "--path",
                "new.txt",
                "--no-update-state",
                "--output",
                str(original),
            )
            raw = original.read_bytes()
            bundle = root / "bom.sync"
            bundle.write_bytes(b"\xef\xbb\xbf" + raw)

            inspected = run(sys.executable, str(REPO_SYNC), "inspect", str(bundle), check=False)
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            report = root / "validation.json"
            validated = run(
                sys.executable,
                str(VALIDATE),
                "--bundle",
                str(bundle),
                "--source-repo",
                str(source),
                "--internal-target",
                "pd-internal",
                "--internal-baseline",
                "baseline",
                "--validation-repo",
                str(target),
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
                str(report),
                check=False,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(
                json.loads(report.read_text(encoding="utf-8"))["bundle_sha256"],
                hashlib.sha256(bundle.read_bytes()).hexdigest(),
            )

            bundle.write_bytes(raw.decode("ascii").encode("utf-16"))
            refused = run(sys.executable, str(REPO_SYNC), "inspect", str(bundle), check=False)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("UTF-16", refused.stderr)
            self.assertIn("UTF-8/ASCII", refused.stderr)

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
            manifest, patch = repo_sync.read_bundle(bundle)
            self.assertEqual(manifest["target"], {"id": "pd-internal", "expected_head": target_head})
            self.assertEqual(len(manifest["changes"]), 2)
            text_postimages = [
                change["new"]
                for change in manifest["changes"]
                if isinstance(change.get("new"), dict) and change["new"].get("text") is True
            ]
            self.assertTrue(text_postimages)
            self.assertTrue(all("content_b85" in item for item in text_postimages))
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

            mismatched = json.loads(json.dumps(manifest))
            embedded = next(
                change["new"]
                for change in mismatched["changes"]
                if isinstance(change.get("new"), dict) and change["new"].get("text") is True
            )
            embedded["content_b85"] = base64.b85encode(b"safe but mismatched\n").decode("ascii")
            bundle.write_text(
                repo_sync.encode_payload(repo_sync.build_payload(mismatched, patch)),
                encoding="ascii",
            )
            inspected = run(sys.executable, str(REPO_SYNC), "inspect", str(bundle), check=False)
            self.assertNotEqual(inspected.returncode, 0)
            self.assertIn("checksum mismatch", inspected.stderr)

            tampered = json.loads(json.dumps(manifest))
            postimage = next(
                change["new"]
                for change in tampered["changes"]
                if isinstance(change.get("new"), dict) and change["new"].get("text") is True
            )
            crlf = b"tampered\r\n"
            postimage.update(
                {
                    "bytes": len(crlf),
                    "sha256": hashlib.sha256(crlf).hexdigest(),
                    "content_b85": base64.b85encode(crlf).decode("ascii"),
                }
            )
            bundle.write_text(
                repo_sync.encode_payload(repo_sync.build_payload(tampered, patch)),
                encoding="ascii",
            )
            inspected = run(sys.executable, str(REPO_SYNC), "inspect", str(bundle), check=False)
            self.assertNotEqual(inspected.returncode, 0)
            self.assertIn("Text files must use LF", inspected.stderr)

    def test_whitespace_findings_are_reported_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "source"
            repo.mkdir()
            run("git", "init", "-q", str(repo))
            run("git", "config", "user.email", "test@example.invalid", cwd=repo)
            run("git", "config", "user.name", "Sync Test", cwd=repo)
            (repo / "service.txt").write_text("before\n", encoding="utf-8")
            run("git", "add", "service.txt", cwd=repo)
            run("git", "commit", "-qm", "baseline", cwd=repo)
            base = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            (repo / "service.txt").write_text(
                "<<<<<<< HEAD\nafter \n=======\nother\n>>>>>>> branch\n",
                encoding="utf-8",
            )
            run("git", "add", "service.txt", cwd=repo)
            run("git", "commit", "-qm", "trailing whitespace change", cwd=repo)
            head = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            target = root / "target"
            clone_at(repo, target, base)

            export_report = root / "export-report.json"
            result = run(
                sys.executable,
                str(WORKFLOW),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--path",
                "service.txt",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--output",
                    str(root / "exported.sync"),
                "--report",
                str(export_report),
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(export_report.read_text(encoding="utf-8"))
            self.assertEqual(data["classification"], "CLEAN_APPLY")
            self.assertTrue(any("trailing whitespace" in item for item in data["whitespace_findings"]))
            self.assertTrue(any("conflict marker" in item for item in data["whitespace_findings"]))

            bundle = root / "whitespace.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--path",
                "service.txt",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--no-update-state",
                "--output",
                str(bundle),
            )
            receive_report = root / "receive-report.json"
            result = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(receive_report),
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(receive_report.read_text(encoding="utf-8"))
            self.assertEqual(data["classification"], "CLEAN_APPLY")
            self.assertTrue(any("trailing whitespace" in item for item in data["whitespace_findings"]))
            self.assertTrue(any("conflict marker" in item for item in data["whitespace_findings"]))
            self.assertEqual(run("git", "status", "--porcelain", cwd=target).stdout, "")

            validator_report = root / "validator.json"
            validated = run(
                sys.executable,
                str(VALIDATE),
                "--bundle",
                str(bundle),
                "--source-repo",
                str(repo),
                "--internal-target",
                "pd-internal",
                "--internal-baseline",
                "baseline",
                "--validation-repo",
                str(target),
                "--validation-baseline",
                base,
                "--base",
                base,
                "--head",
                head,
                "--mode",
                "full",
                "--excluded",
                "none",
                "--report",
                str(validator_report),
                check=False,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            validated_data = json.loads(validator_report.read_text(encoding="utf-8"))
            self.assertTrue(any("trailing whitespace" in item for item in validated_data["whitespace_findings"]))
            self.assertTrue(any("conflict marker" in item for item in validated_data["whitespace_findings"]))

    def test_cached_patch_contract_is_not_reported_as_worktree_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            run("git", "init", "-q", str(source))
            run("git", "config", "user.email", "test@example.invalid", cwd=source)
            run("git", "config", "user.name", "Sync Test", cwd=source)
            run("git", "commit", "-qm", "base", "--allow-empty", cwd=source)
            base = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            (source / "new.txt").write_bytes(b"canonical\n")
            run("git", "add", "new.txt", cwd=source)
            run("git", "commit", "-qm", "add LF file", cwd=source)
            head = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            target = root / "target"
            clone_at(source, target, base)
            info_attributes = Path(run("git", "rev-parse", "--git-path", "info/attributes", cwd=target).stdout.strip())
            if not info_attributes.is_absolute():
                info_attributes = target / info_attributes
            info_attributes.parent.mkdir(parents=True, exist_ok=True)
            info_attributes.write_text("new.txt text eol=crlf\n", encoding="utf-8")
            bundle = root / "change.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(source),
                "--base",
                base,
                "--head",
                head,
                "--path",
                "new.txt",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--no-update-state",
                "--output",
                str(bundle),
            )
            report = root / "receive.json"

            result = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(report),
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual((data["outcome"], data["classification"]), ("UNSAFE_STOP", "INDEX_CONTRACT_ONLY"))
            self.assertEqual(data["validation"]["index_contract"], "passed")
            self.assertEqual(data["validation"]["worktree_applicability"], "failed")
            self.assertFalse((target / "new.txt").exists())
            self.assertEqual(run("git", "status", "--porcelain", cwd=target).stdout, "")

    def test_patch_attributes_change_checks_unchanged_tracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            run("git", "init", "-q", str(source))
            run("git", "config", "user.email", "test@example.invalid", cwd=source)
            run("git", "config", "user.name", "Sync Test", cwd=source)
            (source / ".gitattributes").write_text("* -text\n", encoding="utf-8")
            (source / "unchanged.txt").write_bytes(b"same\n")
            run("git", "add", ".", cwd=source)
            run("git", "commit", "-qm", "base", cwd=source)
            base = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            (source / ".gitattributes").write_text("*.txt text eol=crlf\n", encoding="utf-8")
            run("git", "add", ".gitattributes", cwd=source)
            run("git", "commit", "-qm", "force CRLF checkout", cwd=source)
            head = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            target = root / "target"
            clone_at(source, target, base)
            # clone_at first checks out source HEAD, whose attributes request
            # CRLF, before detaching at base. Recreate the base checkout under
            # its own attributes so receive tests only the candidate change.
            (target / "unchanged.txt").unlink()
            run("git", "reset", "--hard", "-q", "HEAD", cwd=target)
            self.assertEqual(run("git", "status", "--porcelain", cwd=target).stdout, "")
            bundle = root / "attributes.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(source),
                "--base",
                base,
                "--head",
                head,
                "--path",
                ".gitattributes",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--no-update-state",
                "--output",
                str(bundle),
            )
            report = root / "receive.json"

            result = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(report),
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["classification"], "INDEX_CONTRACT_ONLY")
            self.assertIn("unchanged.txt", data["validation"]["worktree_mismatches"])
            self.assertEqual((target / ".gitattributes").read_text(), "* -text\n")

    def test_index_inventory_rejects_cr_in_text_blob(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            run("git", "init", "-q", str(repo))
            (repo / ".gitattributes").write_text("*.txt text\n", encoding="utf-8")
            run("git", "add", ".gitattributes", cwd=repo)
            stored = subprocess.run(
                ["git", "-C", str(repo), "hash-object", "-w", "--no-filters", "--stdin"],
                input=b"legacy\r\n",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout.decode().strip()
            run("git", "update-index", "--add", "--cacheinfo", f"100644,{stored},legacy.txt", cwd=repo)

            with self.assertRaises(repo_sync.TextEolError) as raised:
                repo_sync.index_inventory(repo)

            self.assertEqual(raised.exception.paths, ["legacy.txt"])

    def test_target_binary_attribute_cannot_override_canonical_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            run("git", "init", "-q", str(source))
            run("git", "config", "user.email", "test@example.invalid", cwd=source)
            run("git", "config", "user.name", "Sync Test", cwd=source)
            (source / ".gitattributes").write_text("*.txt text\n", encoding="utf-8")
            run("git", "add", ".gitattributes", cwd=source)
            run("git", "commit", "-qm", "base", cwd=source)
            base = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            stored = subprocess.run(
                ["git", "-C", str(source), "hash-object", "-w", "--no-filters", "--stdin"],
                input=b"bad\r\n",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout.decode().strip()
            run("git", "update-index", "--add", "--cacheinfo", f"100644,{stored},bad.txt", cwd=source)
            run("git", "commit", "-qm", "raw CRLF text", cwd=source)
            head = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            target = root / "target"
            run("git", "clone", "--quiet", "--no-hardlinks", "--no-checkout", str(source), str(target))
            run("git", "checkout", "--quiet", "--detach", base, cwd=target)
            info_attributes = Path(run("git", "rev-parse", "--git-path", "info/attributes", cwd=target).stdout.strip())
            if not info_attributes.is_absolute():
                info_attributes = target / info_attributes
            info_attributes.parent.mkdir(parents=True, exist_ok=True)
            info_attributes.write_text("bad.txt -text\n", encoding="utf-8")
            patch = repo_sync.make_patch(source, base, head, ["bad.txt"])
            new = repo_sync.blob_descriptor(source, head, "bad.txt")
            self.assertTrue(new["text"])
            new.pop("text")
            manifest = {
                "format": repo_sync.FORMAT,
                "version": repo_sync.VERSION,
                "base": base,
                "head": head,
                "patch_sha256": hashlib.sha256(patch).hexdigest(),
                "changes": [{"status": "A", "old": None, "new": new}],
                "target": {"id": "pd-internal", "expected_head": base},
            }
            bundle = root / "crlf.sync"
            bundle.write_text(
                repo_sync.encode_payload(repo_sync.build_payload(manifest, patch)),
                encoding="ascii",
            )
            report = root / "receive.json"

            received = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(report),
                check=False,
            )

            self.assertNotEqual(received.returncode, 0)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["classification"], "TEXT_EOL_NOT_LF")
            self.assertEqual(data["paths"], ["bad.txt"])

    def test_patch_preflight_uses_actual_unchanged_filtered_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            run("git", "init", "-q", str(source))
            run("git", "config", "user.email", "test@example.invalid", cwd=source)
            run("git", "config", "user.name", "Sync Test", cwd=source)
            (source / "f.txt").write_text("clean\n", encoding="utf-8")
            run("git", "add", "f.txt", cwd=source)
            run("git", "commit", "-qm", "base", cwd=source)
            base = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            (source / "new.txt").write_text("new\n", encoding="utf-8")
            run("git", "add", "new.txt", cwd=source)
            run("git", "commit", "-qm", "change", cwd=source)
            head = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            target = root / "target"
            clone_at(source, target, base)
            run("git", "config", "filter.demo.clean", "sed 's/^SMUDGED://'", cwd=target)
            run("git", "config", "filter.demo.smudge", "sed 's/^/SMUDGED:/'", cwd=target)
            info_attributes = Path(run("git", "rev-parse", "--git-path", "info/attributes", cwd=target).stdout.strip())
            if not info_attributes.is_absolute():
                info_attributes = target / info_attributes
            info_attributes.parent.mkdir(parents=True, exist_ok=True)
            info_attributes.write_text("f.txt filter=demo\n", encoding="utf-8")
            (target / "f.txt").unlink()
            run("git", "checkout", "--", "f.txt", cwd=target)
            self.assertEqual((target / "f.txt").read_text(), "SMUDGED:clean\n")
            self.assertEqual(run("git", "status", "--porcelain", cwd=target).stdout, "")
            bundle = root / "filtered.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(source),
                "--base",
                base,
                "--head",
                head,
                "--path",
                "new.txt",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--no-update-state",
                "--output",
                str(bundle),
            )
            report = root / "receive.json"

            received = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(report),
                check=False,
            )

            self.assertNotEqual(received.returncode, 0)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["classification"], "INDEX_CONTRACT_ONLY")
            self.assertIn("f.txt", data["validation"]["worktree_mismatches"])

    def test_core_eol_does_not_affect_unspecified_paths_when_autocrlf_is_false(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            run("git", "init", "-q", str(repo))
            (repo / "f.txt").write_text("lf\n", encoding="utf-8")
            run("git", "add", "f.txt", cwd=repo)
            run("git", "config", "core.autocrlf", "false", cwd=repo)
            run("git", "config", "core.eol", "crlf", cwd=repo)
            files, _ = repo_sync.index_inventory(repo)

            self.assertEqual(repo_sync.lf_worktree_violations(repo, files), [])

    def test_patch_preflight_uses_actual_changed_filtered_preimage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            run("git", "init", "-q", str(source))
            run("git", "config", "user.email", "test@example.invalid", cwd=source)
            run("git", "config", "user.name", "Sync Test", cwd=source)
            (source / "f.txt").write_text("clean\n", encoding="utf-8")
            run("git", "add", "f.txt", cwd=source)
            run("git", "commit", "-qm", "base", cwd=source)
            base = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            (source / "f.txt").write_text("changed\n", encoding="utf-8")
            run("git", "add", "f.txt", cwd=source)
            run("git", "commit", "-qm", "change", cwd=source)
            head = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            target = root / "target"
            clone_at(source, target, base)
            run("git", "config", "filter.demo.clean", "sed 's/^SMUDGED://'", cwd=target)
            run("git", "config", "filter.demo.smudge", "sed 's/^/SMUDGED:/'", cwd=target)
            info_attributes = Path(run("git", "rev-parse", "--git-path", "info/attributes", cwd=target).stdout.strip())
            if not info_attributes.is_absolute():
                info_attributes = target / info_attributes
            info_attributes.parent.mkdir(parents=True, exist_ok=True)
            info_attributes.write_text("f.txt filter=demo\n", encoding="utf-8")
            (target / "f.txt").unlink()
            run("git", "checkout", "--", "f.txt", cwd=target)
            self.assertEqual((target / "f.txt").read_text(), "SMUDGED:clean\n")
            self.assertEqual(run("git", "status", "--porcelain", cwd=target).stdout, "")

            validation, error = sync_workflow.validate_patch_in_disposable_clone(
                target,
                base,
                repo_sync.make_patch(source, base, head, ["f.txt"]),
                repo_sync.describe_changes(source, base, head, ["f.txt"]),
            )

            self.assertIsNotNone(error)
            self.assertEqual(validation["index_contract"], "passed")
            self.assertEqual(validation["worktree_applicability"], "failed")
            self.assertEqual(validation["failed_stage"], "worktree-apply-check")

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

    def test_receive_accepts_legacy_patch_without_text_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, base, head = make_repo(root)
            target = root / "target"
            clone_at(source, target, base)
            bundle = root / "legacy.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(source),
                "--base",
                base,
                "--head",
                head,
                "--path",
                "service.txt",
                "--path",
                "new.txt",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--no-update-state",
                "--output",
                str(bundle),
            )
            manifest, patch = repo_sync.read_bundle(bundle)
            for change in manifest["changes"]:
                for side in ("old", "new"):
                    descriptor = change.get(side)
                    if isinstance(descriptor, dict):
                        descriptor.pop("text", None)
            bundle.write_text(
                repo_sync.encode_payload(repo_sync.build_payload(manifest, patch)),
                encoding="ascii",
            )
            report = root / "receive.json"

            received = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(report),
                check=False,
            )

            self.assertEqual(received.returncode, 0, received.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual((data["outcome"], data["classification"]), ("READY", "CLEAN_APPLY"))
            self.assertEqual(manifest["format"], "repo-sync-text-v1")
            self.assertEqual(manifest["version"], 1)

    def test_unrelated_legacy_crlf_target_file_does_not_block_lf_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            run("git", "init", "-q", str(source))
            run("git", "config", "user.email", "test@example.invalid", cwd=source)
            run("git", "config", "user.name", "Sync Test", cwd=source)
            run("git", "config", "core.autocrlf", "false", cwd=source)
            (source / "tool.bat").write_bytes(b"echo legacy\r\n")
            (source / "service.txt").write_bytes(b"before\n")
            run("git", "add", ".", cwd=source)
            run("git", "commit", "-qm", "base", cwd=source)
            base = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            (source / "service.txt").write_bytes(b"after\n")
            run("git", "add", "service.txt", cwd=source)
            run("git", "commit", "-qm", "change", cwd=source)
            head = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            target = root / "target"
            clone_at(source, target, base)
            run("git", "config", "core.autocrlf", "false", cwd=target)
            bundle = root / "change.sync"
            export_report = root / "export.json"
            exported = run(
                sys.executable,
                str(WORKFLOW),
                "export",
                str(source),
                "--base",
                base,
                "--head",
                head,
                "--path",
                "service.txt",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--output",
                str(bundle),
                "--report",
                str(export_report),
                check=False,
            )
            self.assertEqual(exported.returncode, 0, exported.stderr)
            self.assertEqual(json.loads(export_report.read_text())["classification"], "CLEAN_APPLY")
            report = root / "receive.json"

            received = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(report),
                check=False,
            )

            self.assertEqual(received.returncode, 0, received.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["classification"], "CLEAN_APPLY")
            self.assertNotIn("tool.bat", data.get("paths", []))

    def test_binary_crlf_requires_explicit_target_attribute_in_patch_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            run("git", "init", "-q", str(source))
            run("git", "config", "user.email", "test@example.invalid", cwd=source)
            run("git", "config", "user.name", "Sync Test", cwd=source)
            run("git", "commit", "-qm", "base", "--allow-empty", cwd=source)
            base = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            (source / ".gitattributes").write_text("data.bin -text\n", encoding="utf-8")
            (source / "data.bin").write_bytes(b"opaque\r\nbytes")
            run("git", "add", ".gitattributes", "data.bin", cwd=source)
            run("git", "commit", "-qm", "binary", cwd=source)
            head = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            target = root / "target"
            clone_at(source, target, base)
            bundle = root / "binary.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(source),
                "--base",
                base,
                "--head",
                head,
                "--path",
                "data.bin",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--no-update-state",
                "--output",
                str(bundle),
            )
            report = root / "receive.json"

            received = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(report),
                check=False,
            )

            self.assertNotEqual(received.returncode, 0)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["classification"], "ATTRIBUTE_SCOPE_MISMATCH")
            self.assertEqual(data["paths"], ["data.bin"])

            complete_bundle = root / "binary-with-attributes.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(source),
                "--base",
                base,
                "--head",
                head,
                "--path",
                ".gitattributes",
                "--path",
                "data.bin",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--no-update-state",
                "--output",
                str(complete_bundle),
            )
            complete_report = root / "complete-receive.json"
            accepted = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(complete_bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(complete_report),
                check=False,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertEqual(json.loads(complete_report.read_text())["classification"], "CLEAN_APPLY")

    def test_legacy_patch_can_normalize_crlf_preimage_to_lf(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            run("git", "init", "-q", str(source))
            run("git", "config", "user.email", "test@example.invalid", cwd=source)
            run("git", "config", "user.name", "Sync Test", cwd=source)
            run("git", "config", "core.autocrlf", "false", cwd=source)
            (source / "notes.txt").write_bytes(b"line1\r\n")
            run("git", "add", "notes.txt", cwd=source)
            run("git", "commit", "-qm", "CRLF base", cwd=source)
            base = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            (source / "notes.txt").write_bytes(b"line1\n")
            run("git", "add", "notes.txt", cwd=source)
            run("git", "commit", "-qm", "normalize", cwd=source)
            head = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            target = root / "target"
            clone_at(source, target, base)
            run("git", "config", "core.autocrlf", "false", cwd=target)
            bundle = root / "legacy-normalize.sync"
            run(
                sys.executable,
                str(REPO_SYNC),
                "export",
                str(source),
                "--base",
                base,
                "--head",
                head,
                "--path",
                "notes.txt",
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--no-update-state",
                "--output",
                str(bundle),
            )
            manifest, patch = repo_sync.read_bundle(bundle)
            for change in manifest["changes"]:
                for side in ("old", "new"):
                    item = change.get(side)
                    if isinstance(item, dict):
                        item.pop("text", None)
                        item.pop("content_b85", None)
            bundle.write_text(
                repo_sync.encode_payload(repo_sync.build_payload(manifest, patch)),
                encoding="ascii",
            )
            report = root / "receive.json"

            received = run(
                sys.executable,
                str(WORKFLOW),
                "receive",
                str(bundle),
                "--target-repo",
                str(target),
                "--target-id",
                "pd-internal",
                "--report",
                str(report),
                check=False,
            )

            self.assertEqual(received.returncode, 0, received.stderr)
            self.assertEqual(json.loads(report.read_text())["classification"], "CLEAN_APPLY")

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
