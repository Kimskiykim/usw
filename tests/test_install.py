import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
INSTALL = ROOT / "install.sh"


@unittest.skipIf(
    os.name == "nt",
    "install.sh is a POSIX shell script; Windows installs through the agent's "
    "own extension or plugin manager instead",
)
class InstallTests(unittest.TestCase):
    SKILL_NAMES = (
        "usw-initialize-project",
        "usw-manage-handoff",
        "usw-create-flow",
        "usw-run-flow",
        "usw-find-flow",
        "usw-assess-flow",
    )
    COMMAND_NAMES = (
        "usw-init.md",
        "usw-handoff.md",
        "usw-resume.md",
        "usw-reviewer-llm-critic.md",
        "usw-find-flow.md",
        "usw-assess-flow.md",
        "usw-scout.md",
        "usw-hypothesis-checker.md",
        "usw-bounded-implementer.md",
        "usw-coverage-checker.md",
    )

    def run_install(self, home: Path, *args: str, install=INSTALL, env_extra=None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env.pop("QWEN_HOME", None)
        env.pop("CODEX_HOME", None)
        env.pop("CLAUDE_HOME", None)
        env.update(env_extra or {})
        return subprocess.run(
            [str(install), *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def fixture(self, directory: Path) -> Path:
        source = directory / "source"
        source.mkdir()
        shutil.copy2(INSTALL, source / "install.sh")
        shutil.copytree(ROOT / "skills", source / "skills", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
        shutil.copytree(ROOT / "commands", source / "commands")
        return source

    def tree(self, path):
        def entry(p):
            if p.is_symlink():
                return ("link", os.readlink(p))
            if p.is_dir():
                return ("directory", None)
            return ("file", p.read_bytes())
        return {p.relative_to(path).as_posix(): entry(p) for p in (path, *path.rglob("*"))}

    def test_partial_skill_copy_preserves_previous_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = self.fixture(base)
            home = base / "home"
            target = home / ".agents/skills/usw-initialize-project"
            target.mkdir(parents=True)
            (target / "old").write_bytes(b"previous")
            before = self.tree(target)
            wrappers = base / "bin"
            wrappers.mkdir()
            cp = wrappers / "cp"
            cp.write_text('#!/bin/sh\ncase "$*" in *usw-initialize-project*) mkdir -p "$3"; printf partial > "$3/partial"; exit 1;; esac\nexec /bin/cp "$@"\n')
            cp.chmod(0o755)
            result = self.run_install(home, "codex", "--force", install=source / "install.sh", env_extra={"PATH": f"{wrappers}:{os.environ['PATH']}"})
            self.assertNotEqual(0, result.returncode)
            self.assertEqual(before, self.tree(target))

    def test_missing_late_source_preserves_early_and_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = self.fixture(base)
            (source / "commands" / self.COMMAND_NAMES[-1]).unlink()
            home = base / "home"
            early = home / ".agents/skills/usw-initialize-project/old"
            legacy = home / ".agents/skills/usw-init/old"
            for path in (early, legacy):
                path.parent.mkdir(parents=True)
                path.write_bytes(b"previous")
            result = self.run_install(home, "codex", "--force", install=source / "install.sh")
            self.assertNotEqual(0, result.returncode)
            for path in (early, legacy):
                self.assertTrue(path.is_file(), str(path))
                self.assertEqual(b"previous", path.read_bytes())

    def fault_env(self, base, fault, component):
        wrappers = base / "bin"
        wrappers.mkdir(exist_ok=True)
        bodies = {
            "cp": '''case "$FAULT:$*" in
              copy:*"$COMPONENT"*|copycleanup:*"$COMPONENT"*)
                case "$1" in -R) mkdir -p "$3"; printf partial > "$3/partial";; *) printf partial > "$2";; esac
                exit 1;; esac''',
            "find": '''case "$FAULT:$*" in find:*"$COMPONENT"*) exit 1;; esac''',
            "mv": '''case "$FAULT:$1:$2" in
              backup:*:*"$COMPONENT"*/backup|activate:*"$COMPONENT"*/new:*|rollback:*"$COMPONENT"*/new:*|rollback:*"$COMPONENT"*/backup:*) exit 1;; esac''',
            "rm": '''case "$FAULT:$*" in cleanup:*"$COMPONENT"*|copycleanup:*"$COMPONENT"*) exit 1;; esac''',
        }
        for name, body in bodies.items():
            real = shutil.which(name)
            wrapper = wrappers / name
            wrapper.write_text(f'#!/bin/sh\n{body}\nexec "{real}" "$@"\n')
            wrapper.chmod(0o755)
        return {"PATH": f"{wrappers}:{os.environ['PATH']}", "FAULT": fault, "COMPONENT": component}

    def test_faults_preserve_component_or_report_retained_backup(self):
        skill = "usw-initialize-project"
        command = self.COMMAND_NAMES[0]
        for fault, component, existed in (
            ("copy", skill, True), ("copy", command, True), ("copy", skill, False),
            ("find", skill, True), ("backup", skill, True), ("activate", skill, True),
            ("activate", command, True), ("activate", skill, False),
            ("rollback", skill, True), ("cleanup", skill, True), ("copycleanup", skill, True),
        ):
            with self.subTest(fault=fault, component=component, existed=existed), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                source = self.fixture(base)
                home = base / "home"
                is_skill = component == skill
                target = home / (".agents/skills" if is_skill else ".codex/prompts") / component
                target.parent.mkdir(parents=True)
                if existed:
                    if is_skill:
                        (target / "nested").mkdir(parents=True)
                        (target / "nested/old").write_bytes(b"old skill")
                        (target / "nested/empty").mkdir()
                        (target / "link").symlink_to("nested/old")
                    else:
                        target.write_bytes(b"old command")
                before = self.tree(target) if existed else None
                result = self.run_install(home, "codex", "--force", install=source / "install.sh", env_extra=self.fault_env(base, fault, component))
                self.assertNotEqual(0, result.returncode, result.stdout)
                self.assertIn(str(target), result.stderr)
                self.assertNotIn(str(target), result.stdout)
                staging = list(target.parent.glob(".usw-install.*"))
                if fault == "rollback":
                    self.assertFalse(target.exists())
                    self.assertEqual(1, len(staging))
                    backup = staging[0] / "backup"
                    self.assertEqual(before, self.tree(backup))
                    self.assertIn(str(backup), result.stderr)
                elif fault == "cleanup":
                    self.assertEqual(self.tree(source / "skills" / skill), self.tree(target))
                    self.assertEqual(1, len(staging))
                    self.assertEqual(before, self.tree(staging[0] / "backup"))
                    self.assertIn(str(staging[0]), result.stderr)
                elif fault == "copycleanup":
                    self.assertEqual(before, self.tree(target))
                    self.assertEqual(1, len(staging))
                    self.assertIn(str(staging[0]), result.stderr)
                else:
                    self.assertEqual([], staging)
                    if not existed:
                        self.assertFalse(target.exists())
                    else:
                        self.assertEqual(before, self.tree(target))

    def test_leaf_symlinks_are_conflicts_or_replaced_without_following(self):
        for component, is_skill in ((self.SKILL_NAMES[0], True), (self.COMMAND_NAMES[0], False)):
            for dangling in (False, True):
                for force in (False, True):
                    with self.subTest(component=component, dangling=dangling, force=force), tempfile.TemporaryDirectory() as directory:
                        base = Path(directory)
                        source = self.fixture(base)
                        home = base / "home"
                        target = home / (".agents/skills" if is_skill else ".codex/prompts") / component
                        target.parent.mkdir(parents=True)
                        external = base / "external"
                        if not dangling:
                            external.write_bytes(b"external")
                        target.symlink_to(external)
                        before = self.tree(target)
                        result = self.run_install(home, "codex", *(('--force',) if force else ()), install=source / "install.sh")
                        self.assertEqual(0 if force else 1, result.returncode, result.stderr)
                        self.assertEqual(not force, target.is_symlink())
                        if force:
                            expected = source / ("skills" if is_skill else "commands") / component
                            self.assertEqual(self.tree(expected), self.tree(target))
                        if not force:
                            self.assertEqual(before, self.tree(target))
                        self.assertEqual(not dangling, external.exists())
                        if not dangling:
                            self.assertEqual(b"external", external.read_bytes())

    def test_late_conflict_and_late_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = self.fixture(base)
            home = base / "home"
            late = home / ".claude/commands" / self.COMMAND_NAMES[-1]
            late.parent.mkdir(parents=True)
            late.write_bytes(b"conflict")
            result = self.run_install(home, install=source / "install.sh")
            self.assertNotEqual(0, result.returncode)
            self.assertEqual(b"conflict", late.read_bytes())
            self.assertFalse((home / ".qwen").exists())
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = self.fixture(base)
            home = base / "home"
            early = home / ".agents/skills" / self.SKILL_NAMES[0]
            late = home / ".agents/skills" / self.SKILL_NAMES[1]
            for target in (early, late):
                target.mkdir(parents=True)
                (target / "old").write_bytes(b"old")
            before = self.tree(late)
            result = self.run_install(home, "codex", "--force", install=source / "install.sh", env_extra=self.fault_env(base, "copy", self.SKILL_NAMES[1]))
            self.assertNotEqual(0, result.returncode)
            self.assertEqual(self.tree(source / "skills" / self.SKILL_NAMES[0]), self.tree(early))
            self.assertEqual(before, self.tree(late))
            self.assertIn(str(late), result.stderr)
            self.assertRegex(result.stderr.lower(), r"mixed|смешан")

    def test_parent_symlink_and_staged_bytecode_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = self.fixture(base)
            cache = source / "skills" / self.SKILL_NAMES[0] / "__pycache__"
            cache.mkdir()
            (cache / "test.pyc").write_bytes(b"cache")
            (source / "skills" / self.SKILL_NAMES[0] / "test.pyo").write_bytes(b"cache")
            home = base / "home"
            (home / ".agents").mkdir(parents=True)
            real_skills = base / "real-skills"
            real_skills.mkdir()
            (home / ".agents/skills").symlink_to(real_skills, target_is_directory=True)
            result = self.run_install(home, "codex", install=source / "install.sh")
            self.assertEqual(0, result.returncode, result.stderr)
            installed = real_skills / self.SKILL_NAMES[0]
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertFalse((installed / "__pycache__").exists())
            self.assertFalse((installed / "test.pyo").exists())
            self.assertTrue((cache / "test.pyc").is_file())

    def test_missing_skill_source_and_skill_entrypoint_preflight(self):
        for missing in ("directory", "entrypoint"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                source = self.fixture(base)
                skill = source / "skills" / self.SKILL_NAMES[-1]
                if missing == "directory":
                    shutil.rmtree(skill)
                else:
                    (skill / "SKILL.md").unlink()
                home = base / "home"
                previous = home / ".agents/skills/usw-init/old"
                previous.parent.mkdir(parents=True)
                previous.write_bytes(b"previous")
                result = self.run_install(home, "codex", "--force", install=source / "install.sh")
                self.assertNotEqual(0, result.returncode)
                self.assertEqual(b"previous", previous.read_bytes())
                self.assertIn(str(skill), result.stderr)

    def test_installs_all_components_for_both_agents_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)

            result = self.run_install(home)

            self.assertEqual(0, result.returncode, result.stderr)
            for skills_dir in (home / ".qwen/skills", home / ".agents/skills", home / ".claude/skills"):
                for skill_name in self.SKILL_NAMES:
                    self.assertTrue((skills_dir / skill_name / "SKILL.md").is_file())
                self.assertEqual(
                    [],
                    [
                        path
                        for path in skills_dir.rglob("*")
                        if path.name == "__pycache__"
                        or path.suffix in {".pyc", ".pyo"}
                    ],
                )
                self.assertTrue(
                    (
                        skills_dir
                        / "usw-initialize-project/templates/task/task.md"
                    ).is_file()
                )
                self.assertTrue(
                    (
                        skills_dir
                        / "usw-initialize-project/references/llm-fallback.md"
                    ).is_file()
                )
                for example in (
                    "chat-review.md",
                    "dev-test.md",
                ):
                    self.assertTrue(
                        (
                            skills_dir
                            / "usw-initialize-project/templates/flows/examples"
                            / example
                        ).is_file()
                    )
            for commands_dir in (home / ".qwen/commands", home / ".codex/prompts", home / ".claude/commands"):
                for command_name in self.COMMAND_NAMES:
                    self.assertTrue((commands_dir / command_name).is_file())

    def test_refuses_to_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(0, self.run_install(home).returncode)
            installed_skill = home / ".qwen/skills/usw-initialize-project/SKILL.md"
            installed_skill.write_text("local change\n", encoding="utf-8", newline="\n")

            result = self.run_install(home)

            self.assertEqual(1, result.returncode)
            self.assertEqual("local change\n", installed_skill.read_text(encoding="utf-8"))

    def test_force_replaces_existing_components(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(0, self.run_install(home).returncode)
            installed_skills = []
            for skills_dir in (home / ".qwen/skills", home / ".agents/skills", home / ".claude/skills"):
                for skill_name in self.SKILL_NAMES:
                    path = skills_dir / skill_name / "SKILL.md"
                    path.write_text("stale\n", encoding="utf-8", newline="\n")
                    installed_skills.append((skill_name, path))
            installed_commands = []
            for commands_dir in (home / ".qwen/commands", home / ".codex/prompts", home / ".claude/commands"):
                for command_name in self.COMMAND_NAMES:
                    path = commands_dir / command_name
                    path.write_text("stale\n", encoding="utf-8", newline="\n")
                    installed_commands.append((command_name, path))

            result = self.run_install(home, "--force")

            self.assertEqual(0, result.returncode, result.stderr)
            for skill_name, installed_path in installed_skills:
                source = (ROOT / "skills" / skill_name / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                self.assertEqual(source, installed_path.read_text(encoding="utf-8"))
            for command_name, installed_path in installed_commands:
                source = (ROOT / "commands" / command_name).read_text(
                    encoding="utf-8"
                )
                self.assertEqual(source, installed_path.read_text(encoding="utf-8"))

    def test_force_removes_legacy_names(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            legacy_skills = [
                base / name
                for base in (home / ".qwen/skills", home / ".agents/skills", home / ".claude/skills")
                for name in (
                    "usw-init",
                    "usw-refine-task",
                    "usw-execute-task",
                    "usw-verify-task",
                    "usw-route-task",
                    "usw-refine-intent",
                    "usw-plan-small-steps",
                    "usw-explain-me",
                    "usw-structured-review",
                )
            ]
            for path in legacy_skills:
                path.mkdir(parents=True)
                (path / "SKILL.md").write_text("legacy\n", encoding="utf-8", newline="\n")
            legacy_commands = [
                base / name
                for base in (home / ".qwen/commands", home / ".codex/prompts", home / ".claude/commands")
                for name in (
                    "usw-route-task.md",
                    "usw-refine-intent.md",
                    "usw-plan-small-steps.md",
                    "usw-explain-me.md",
                )
            ]
            for path in legacy_commands:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("legacy\n", encoding="utf-8", newline="\n")

            result = self.run_install(home, "--force")

            self.assertEqual(0, result.returncode, result.stderr)
            for path in (*legacy_skills, *legacy_commands):
                self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
