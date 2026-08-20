#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
SNAPSHOT = SCRIPTS / "repo_snapshot_sync.py"
SKILL = SCRIPTS.parent / "SKILL.md"
SNAPSHOT_GUIDE = SCRIPTS.parent / "references" / "snapshot-converge.md"
sys.path.insert(0, str(SCRIPTS))
import repo_snapshot_sync as snapshot_sync  # noqa: E402
import repo_sync  # noqa: E402


def run(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def tracked(repo: Path) -> list[str]:
    result = run("git", "ls-files", "-z", cwd=repo)
    return sorted(path for path in result.stdout.split("\0") if path)


def make_canonical(root: Path) -> tuple[Path, str, str]:
    repo = root / "canonical"
    repo.mkdir()
    run("git", "init", "-q", str(repo))
    run("git", "config", "user.email", "test@example.invalid", cwd=repo)
    run("git", "config", "user.name", "Snapshot Test", cwd=repo)
    (repo / ".gitignore").write_text(".env\n.usw/\ncache/\ngenerated/\n", encoding="utf-8")
    (repo / "unchanged.txt").write_text("same\n", encoding="utf-8")
    (repo / "replace.txt").write_text("old\n", encoding="utf-8")
    (repo / "delete.txt").write_text("remove me\n", encoding="utf-8")
    (repo / "old-name.txt").write_text("renamed bytes\n", encoding="utf-8")
    scripts = repo / "bin"
    scripts.mkdir()
    runner = scripts / "run.sh"
    runner.write_text("#!/bin/sh\necho old\n", encoding="utf-8")
    runner.chmod(0o755)
    run("git", "add", ".", cwd=repo)
    run("git", "commit", "-qm", "canonical base", cwd=repo)
    base = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()

    (repo / "replace.txt").write_text("canonical replacement\n", encoding="utf-8")
    (repo / "delete.txt").unlink()
    run("git", "mv", "old-name.txt", "new-name.txt", cwd=repo)
    (repo / "add.txt").write_text("canonical addition\n", encoding="utf-8")
    runner.write_text("#!/bin/sh\necho canonical\n", encoding="utf-8")
    (repo / ".env").write_text("SOURCE_SECRET=never-package\n", encoding="utf-8")
    (repo / ".usw").mkdir()
    (repo / ".usw" / "HANDOFF.md").write_text("local source state\n", encoding="utf-8")
    (repo / "cache").mkdir()
    (repo / "cache" / "run.log").write_text("cache\n", encoding="utf-8")
    run("git", "add", "-A", cwd=repo)
    run("git", "commit", "-qm", "canonical head", cwd=repo)
    head = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
    return repo, base, head


def clone_at(source: Path, target: Path, revision: str) -> None:
    run("git", "clone", "--quiet", "--no-hardlinks", str(source), str(target))
    run("git", "checkout", "--quiet", "--detach", revision, cwd=target)
    run("git", "config", "user.email", "test@example.invalid", cwd=target)
    run("git", "config", "user.name", "Snapshot Test", cwd=target)


def export_snapshot(
    source: Path,
    head: str,
    bundle: Path,
    report: Path,
    *extra: str,
) -> subprocess.CompletedProcess[str]:
    return run(
        sys.executable,
        str(SNAPSHOT),
        "export",
        str(source),
        "--direction",
        "internal-to-external",
        "--head",
        head,
        "--output",
        str(bundle),
        "--report",
        str(report),
        "--acknowledge-full-snapshot",
        *extra,
        check=False,
    )


class SnapshotSyncTest(unittest.TestCase):
    def test_export_batch_reads_unique_blob_oids_with_one_process(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "canonical"
            repo.mkdir()
            run("git", "init", "-q", str(repo))
            run("git", "config", "user.email", "test@example.invalid", cwd=repo)
            run("git", "config", "user.name", "Snapshot Test", cwd=repo)
            for index in range(75):
                (repo / f"file-{index:03}.txt").write_bytes(b"shared blob bytes\n")
            run("git", "add", ".", cwd=repo)
            run("git", "commit", "-qm", "many files", cwd=repo)

            real_popen = subprocess.Popen
            commands: list[list[str]] = []
            batch_inputs: list[bytes] = []

            class RecordingProcess:
                def __init__(self, *args, **kwargs):
                    self.command = args[0]
                    commands.append(self.command)
                    self.process = real_popen(*args, **kwargs)

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return self.process.__exit__(*args)

                def __getattr__(self, name):
                    return getattr(self.process, name)

                def communicate(self, input=None, timeout=None):
                    if "--batch" in self.command:
                        batch_inputs.append(input)
                    return self.process.communicate(input=input, timeout=timeout)

            with mock.patch.object(snapshot_sync.subprocess, "Popen", RecordingProcess):
                files, blobs, excluded = snapshot_sync.canonical_files(repo, "HEAD", [], [])

            cat_file_commands = [command for command in commands if "cat-file" in command]
            self.assertEqual(len(files), 75)
            self.assertEqual(len(blobs), 1)
            self.assertEqual(excluded, [])
            self.assertEqual(len(cat_file_commands), 1)
            self.assertIn("--batch", cat_file_commands[0])
            self.assertNotIn("blob", cat_file_commands[0])
            self.assertEqual(batch_inputs[0].count(b"\n"), 1)

    def test_export_is_self_contained_and_contains_exact_tracked_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, _, head = make_canonical(root)
            bundle = root / "canonical.sync"
            report = root / "export.json"
            result = export_snapshot(source, head, bundle, report)
            self.assertEqual(result.returncode, 0, result.stderr)
            exported = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual((exported["outcome"], exported["classification"]), ("READY", "SNAPSHOT_EXPORTED"))
            self.assertEqual(exported["bundle_sha256"], hashlib.sha256(bundle.read_bytes()).hexdigest())

            inspected = run(sys.executable, str(SNAPSHOT), "inspect", str(bundle))
            manifest = json.loads(inspected.stdout)
            self.assertEqual(manifest["format"], "repo-sync-snapshot-v1")
            self.assertEqual(manifest["kind"], "git-tracked-snapshot")
            self.assertEqual(manifest["direction"], "internal-to-external")
            self.assertEqual(manifest["canonical"]["commit"], head)
            self.assertEqual(
                manifest["canonical"]["tree"],
                run("git", "rev-parse", f"{head}^{{tree}}", cwd=source).stdout.strip(),
            )
            paths = [entry["path"] for entry in manifest["files"]]
            self.assertEqual(paths, sorted(tracked(source)))
            self.assertIn(".gitignore", paths)
            self.assertNotIn(".env", paths)
            self.assertFalse(any(path == ".git" or path.startswith(".git/") for path in paths))
            self.assertFalse(any("content_b85" in entry for entry in manifest["files"]))
            self.assertEqual(manifest["scope"]["untracked_included"], False)
            self.assertEqual(manifest["authorization"]["apply_flag"], "--confirm-converge")
            self.assertIn("security_warning", manifest["handoff"])
            self.assertIn("receipt_template", manifest["handoff"])
            self.assertFalse(exported["transport_security"]["encrypted"])
            self.assertIn("not encryption", exported["transport_security"]["warning"].lower())
            self.assertEqual(exported["transport_security"]["encoding"], "base85+gzip+tar")
            self.assertIn("repo_snapshot_sync.py", exported["usage"]["inspect"])
            self.assertIn(" plan ", exported["usage"]["plan"])
            self.assertIn("--confirm-converge", manifest["handoff"]["command_templates"]["apply"])

    def test_plan_is_deterministic_and_classifies_add_replace_delete_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, base, head = make_canonical(root)
            target = root / "mirror"
            clone_at(source, target, base)
            target_head = run("git", "rev-parse", "HEAD", cwd=target).stdout.strip()
            bundle = root / "canonical.sync"
            self.assertEqual(export_snapshot(source, head, bundle, root / "export.json").returncode, 0)

            reports: list[dict[str, object]] = []
            for name in ("first", "second"):
                report = root / f"plan-{name}.json"
                result = run(
                    sys.executable,
                    str(SNAPSHOT),
                    "plan",
                    str(bundle),
                    str(target),
                    "--report",
                    str(report),
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                reports.append(json.loads(report.read_text(encoding="utf-8")))
            first, second = reports
            self.assertEqual(first["plan"], second["plan"])
            self.assertEqual((first["outcome"], first["classification"]), ("READY", "CANONICAL_CHANGES_REQUIRED"))
            self.assertEqual(first["target"]["head"], target_head)
            self.assertEqual(first["plan"]["add"], ["add.txt", "new-name.txt"])
            self.assertEqual(first["plan"]["replace"], ["bin/run.sh", "replace.txt"])
            self.assertEqual(first["plan"]["delete"], ["delete.txt", "old-name.txt"])
            self.assertEqual(first["plan"]["unchanged"], [".gitignore", "unchanged.txt"])
            self.assertEqual(first["disposable_validation"]["tracked_tree_match"], True)
            self.assertIn("--confirm-converge", first["usage"]["apply"])
            self.assertEqual(run("git", "rev-parse", "HEAD", cwd=target).stdout.strip(), target_head)
            self.assertEqual(run("git", "status", "--porcelain", cwd=target).stdout, "")

    def test_apply_requires_confirmation_and_preserves_untracked_local_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, base, head = make_canonical(root)
            target = root / "mirror"
            clone_at(source, target, base)
            target_head = run("git", "rev-parse", "HEAD", cwd=target).stdout.strip()
            (target / ".env").write_text("TARGET_SECRET=preserve\n", encoding="utf-8")
            (target / ".usw").mkdir()
            (target / ".usw" / "HANDOFF.md").write_text("target local state\n", encoding="utf-8")
            (target / "cache").mkdir()
            (target / "cache" / "run.log").write_text("target cache\n", encoding="utf-8")
            bundle = root / "canonical.sync"
            self.assertEqual(export_snapshot(source, head, bundle, root / "export.json").returncode, 0)

            denied_report = root / "denied.json"
            denied = run(
                sys.executable,
                str(SNAPSHOT),
                "apply",
                str(bundle),
                str(target),
                "--report",
                str(denied_report),
                check=False,
            )
            self.assertNotEqual(denied.returncode, 0)
            self.assertEqual(json.loads(denied_report.read_text())["classification"], "CONFIRMATION_REQUIRED")
            self.assertEqual((target / "replace.txt").read_text(), "old\n")

            receipt = root / "apply.json"
            applied = run(
                sys.executable,
                str(SNAPSHOT),
                "apply",
                str(bundle),
                str(target),
                "--confirm-converge",
                "--report",
                str(receipt),
                check=False,
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            data = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual((data["outcome"], data["classification"]), ("READY", "CONVERGED_STAGED"))
            self.assertEqual(data["verification"]["tracked_tree_match"], True)
            self.assertTrue(data["transaction"]["rollback_available"])
            self.assertIn("git restore", data["transaction"]["rollback_command"])
            self.assertEqual(run("git", "rev-parse", "HEAD", cwd=target).stdout.strip(), target_head)
            self.assertEqual(tracked(target), sorted(tracked(source)))
            self.assertEqual((target / "replace.txt").read_text(), "canonical replacement\n")
            self.assertFalse((target / "old-name.txt").exists())
            self.assertEqual((target / "new-name.txt").read_text(), "renamed bytes\n")
            self.assertEqual((target / ".env").read_text(), "TARGET_SECRET=preserve\n")
            self.assertEqual((target / ".usw" / "HANDOFF.md").read_text(), "target local state\n")
            self.assertEqual((target / "cache" / "run.log").read_text(), "target cache\n")
            self.assertFalse(data["commit_performed"])
            self.assertFalse(data["push_performed"])

    def test_apply_stops_on_dirty_tracked_file_and_untracked_or_ignored_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, base, head = make_canonical(root)
            bundle = root / "canonical.sync"
            self.assertEqual(export_snapshot(source, head, bundle, root / "export.json").returncode, 0)

            dirty = root / "dirty"
            clone_at(source, dirty, base)
            (dirty / "replace.txt").write_text("local dirty edit\n", encoding="utf-8")
            dirty_report = root / "dirty.json"
            dirty_result = run(
                sys.executable,
                str(SNAPSHOT),
                "plan",
                str(bundle),
                str(dirty),
                "--report",
                str(dirty_report),
                check=False,
            )
            self.assertNotEqual(dirty_result.returncode, 0)
            self.assertEqual(json.loads(dirty_report.read_text())["classification"], "TARGET_TRACKED_DIRTY")

            collision = root / "collision"
            clone_at(source, collision, base)
            (collision / "add.txt").write_text("user local file\n", encoding="utf-8")
            collision_report = root / "collision.json"
            collision_result = run(
                sys.executable,
                str(SNAPSHOT),
                "apply",
                str(bundle),
                str(collision),
                "--confirm-converge",
                "--report",
                str(collision_report),
                check=False,
            )
            self.assertNotEqual(collision_result.returncode, 0)
            collision_data = json.loads(collision_report.read_text())
            self.assertEqual(collision_data["classification"], "UNTRACKED_PATH_COLLISION")
            self.assertEqual((collision / "add.txt").read_text(), "user local file\n")

    def test_allow_and_deny_paths_are_explicit_manifest_deviations(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, _, head = make_canonical(root)
            bundle = root / "scoped.sync"
            result = export_snapshot(
                source,
                head,
                bundle,
                root / "scoped.json",
                "--allow-path",
                "bin",
                "--allow-path",
                ".gitignore",
                "--deny-path",
                ".gitignore",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            inspected = run(sys.executable, str(SNAPSHOT), "inspect", str(bundle))
            manifest = json.loads(inspected.stdout)
            self.assertEqual([entry["path"] for entry in manifest["files"]], ["bin/run.sh"])
            self.assertEqual(manifest["scope"]["allow_paths"], [".gitignore", "bin"])
            self.assertEqual(manifest["scope"]["deny_paths"], [".gitignore"])
            self.assertEqual(manifest["scope"]["default_inclusion"], "all tracked files at canonical head")

    def test_cli_has_only_plain_transport_export_inspect_plan_apply(self) -> None:
        result = run(sys.executable, str(SNAPSHOT), "--help")
        for command in ("export", "inspect", "plan", "apply"):
            self.assertIn(command, result.stdout)
        self.assertNotIn("--encrypt", result.stdout)
        self.assertNotIn("decrypt", result.stdout)

    def test_export_requires_explicit_immutable_direction(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, _, head = make_canonical(root)
            output = root / "missing-direction.sync"
            result = run(
                sys.executable,
                str(SNAPSHOT),
                "export",
                str(source),
                "--head",
                head,
                "--output",
                str(output),
                "--report",
                str(root / "missing-direction.json"),
                "--acknowledge-full-snapshot",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--direction", result.stderr)
            self.assertFalse(output.exists())

            bundle = root / "canonical.sync"
            self.assertEqual(export_snapshot(source, head, bundle, root / "export.json").returncode, 0)
            manifest, blobs = snapshot_sync.read_snapshot(bundle)
            manifest["direction"] = "external-to-internal"
            bundle.write_text(
                repo_sync.encode_payload(snapshot_sync.build_payload(manifest, blobs)),
                encoding="ascii",
            )
            inspected = run(sys.executable, str(SNAPSHOT), "inspect", str(bundle), check=False)
            self.assertNotEqual(inspected.returncode, 0)
            self.assertIn("direction", json.loads(inspected.stdout)["error"].lower())

    def test_docs_forbid_dlp_evasion_and_plaintext_encoding_claims(self) -> None:
        text = (SKILL.read_text(encoding="utf-8") + SNAPSHOT_GUIDE.read_text(encoding="utf-8")).lower()
        for phrase in (
            "not encryption",
            "no stealth",
            "dlp",
            "does not mean approval",
            "corporate-approved channel",
            "no automatic network",
            "--confirm-converge",
            "--direction internal-to-external",
            "canonical commit",
            "canonical tree",
            "tracked .gitignore",
        ):
            self.assertIn(phrase, text)

    def test_inspect_rejects_tampered_snapshot_blob(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, _, head = make_canonical(root)
            bundle = root / "canonical.sync"
            self.assertEqual(export_snapshot(source, head, bundle, root / "export.json").returncode, 0)
            manifest, blobs = snapshot_sync.read_snapshot(bundle)
            digest = manifest["files"][0]["sha256"]
            tampered = dict(blobs)
            tampered[digest] = b"tampered bytes\n"
            bundle.write_text(
                repo_sync.encode_payload(snapshot_sync.build_payload(manifest, tampered)),
                encoding="ascii",
            )
            inspected = run(sys.executable, str(SNAPSHOT), "inspect", str(bundle), check=False)
            self.assertNotEqual(inspected.returncode, 0)
            data = json.loads(inspected.stdout)
            self.assertEqual((data["outcome"], data["classification"]), ("UNSAFE_STOP", "UNSAFE_ERROR"))
            self.assertIn("checksum mismatch", data["error"].lower())

    def test_failed_apply_transaction_restores_original_index_and_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, base, head = make_canonical(root)
            target = root / "mirror"
            clone_at(source, target, base)
            bundle = root / "canonical.sync"
            self.assertEqual(export_snapshot(source, head, bundle, root / "export.json").returncode, 0)
            manifest, blobs = snapshot_sync.read_snapshot(bundle)
            plan = snapshot_sync.make_plan(manifest["files"], snapshot_sync.index_files(target))
            original_write = snapshot_sync.write_file
            calls = 0
            failed = False

            def fail_once(repo: Path, item: dict[str, object], content: bytes) -> None:
                nonlocal calls, failed
                calls += 1
                if calls == 2 and not failed:
                    failed = True
                    raise snapshot_sync.SnapshotError("injected transaction failure")
                original_write(repo, item, content)

            with mock.patch.object(snapshot_sync, "write_file", side_effect=fail_once):
                with self.assertRaisesRegex(snapshot_sync.SnapshotError, "injected transaction failure"):
                    snapshot_sync.apply_to_repo(target, manifest["files"], blobs, plan)
            self.assertEqual(run("git", "status", "--porcelain", cwd=target).stdout, "")
            self.assertEqual((target / "replace.txt").read_text(), "old\n")
            self.assertTrue((target / "delete.txt").exists())
            self.assertTrue((target / "old-name.txt").exists())
            self.assertFalse((target / "add.txt").exists())

    def test_export_rejects_symlink_targeting_git_or_outside_repository(self) -> None:
        for target_value in (".git/config", "../../outside", "/tmp/outside", "C:outside"):
            with self.subTest(target=target_value), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                source = root / "canonical"
                source.mkdir()
                run("git", "init", "-q", str(source))
                run("git", "config", "user.email", "test@example.invalid", cwd=source)
                run("git", "config", "user.name", "Snapshot Test", cwd=source)
                (source / "unsafe-link").symlink_to(target_value)
                run("git", "add", "unsafe-link", cwd=source)
                run("git", "commit", "-qm", "unsafe symlink", cwd=source)
                head = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
                result = export_snapshot(source, head, root / "unsafe.sync", root / "unsafe.json")
                self.assertNotEqual(result.returncode, 0)
                data = json.loads((root / "unsafe.json").read_text())
                self.assertEqual(data["outcome"], "UNSAFE_STOP")
                self.assertIn("symlink", data["error"].lower())

    def test_snapshot_paths_reject_git_traversal_and_cross_platform_drive_forms(self) -> None:
        for path in (".git/config", "../outside", "dir\\outside", "C:outside"):
            with self.subTest(path=path), self.assertRaises(snapshot_sync.SnapshotError):
                snapshot_sync.safe_path(path)

    def test_empty_untracked_directory_blocks_canonical_file_add(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, base, head = make_canonical(root)
            target = root / "mirror"
            clone_at(source, target, base)
            (target / "add.txt").mkdir()
            bundle = root / "canonical.sync"
            self.assertEqual(export_snapshot(source, head, bundle, root / "export.json").returncode, 0)
            result = run(
                sys.executable,
                str(SNAPSHOT),
                "plan",
                str(bundle),
                str(target),
                "--report",
                str(root / "plan.json"),
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            data = json.loads((root / "plan.json").read_text())
            self.assertEqual(data["classification"], "UNTRACKED_PATH_COLLISION")
            self.assertTrue((target / "add.txt").is_dir())

    def test_apply_rechecks_late_untracked_collision_after_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, base, head = make_canonical(root)
            target = root / "mirror"
            clone_at(source, target, base)
            bundle = root / "canonical.sync"
            self.assertEqual(export_snapshot(source, head, bundle, root / "export.json").returncode, 0)
            manifest, blobs = snapshot_sync.read_snapshot(bundle)
            plan = snapshot_sync.make_plan(manifest["files"], snapshot_sync.index_files(target))
            (target / "add.txt").write_text("appeared after plan\n", encoding="utf-8")
            with self.assertRaisesRegex(snapshot_sync.SnapshotError, "untracked path collision"):
                snapshot_sync.apply_to_repo(target, manifest["files"], blobs, plan)
            self.assertEqual((target / "add.txt").read_text(), "appeared after plan\n")
            self.assertEqual(run("git", "diff", "--cached", "--name-only", cwd=target).stdout, "")


if __name__ == "__main__":
    unittest.main()
