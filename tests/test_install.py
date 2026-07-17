import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
INSTALL = ROOT / "install.sh"


class InstallTests(unittest.TestCase):
    def run_install(self, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env.pop("QWEN_HOME", None)
        env.pop("CODEX_HOME", None)
        return subprocess.run(
            [str(INSTALL), *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_installs_both_skills_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)

            result = self.run_install(home)

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(
                (home / ".qwen/skills/usw-initialize-project/SKILL.md").is_file()
            )
            self.assertTrue((home / ".qwen/commands/usw-init.md").is_file())
            self.assertTrue(
                (home / ".agents/skills/usw-initialize-project/SKILL.md").is_file()
            )
            self.assertTrue((home / ".codex/prompts/usw-init.md").is_file())

    def test_refuses_to_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(0, self.run_install(home).returncode)
            installed_skill = home / ".qwen/skills/usw-initialize-project/SKILL.md"
            installed_skill.write_text("local change\n", encoding="utf-8")

            result = self.run_install(home)

            self.assertEqual(1, result.returncode)
            self.assertEqual("local change\n", installed_skill.read_text(encoding="utf-8"))

    def test_force_replaces_existing_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(0, self.run_install(home).returncode)
            qwen_skill = home / ".qwen/skills/usw-initialize-project/SKILL.md"
            codex_skill = home / ".agents/skills/usw-initialize-project/SKILL.md"
            qwen_command = home / ".qwen/commands/usw-init.md"
            codex_command = home / ".codex/prompts/usw-init.md"
            qwen_skill.write_text("stale\n", encoding="utf-8")
            codex_skill.write_text("stale\n", encoding="utf-8")
            qwen_command.write_text("stale\n", encoding="utf-8")
            codex_command.write_text("stale\n", encoding="utf-8")

            result = self.run_install(home, "--force")

            self.assertEqual(0, result.returncode, result.stderr)
            source_skill = (
                ROOT / "skills/usw-initialize-project/SKILL.md"
            ).read_text(encoding="utf-8")
            source_command = (ROOT / "commands/usw-init.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(source_skill, qwen_skill.read_text(encoding="utf-8"))
            self.assertEqual(source_skill, codex_skill.read_text(encoding="utf-8"))
            self.assertEqual(source_command, qwen_command.read_text(encoding="utf-8"))
            self.assertEqual(source_command, codex_command.read_text(encoding="utf-8"))

    def test_force_removes_legacy_skill_name(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            legacy_qwen = home / ".qwen/skills/usw-init"
            legacy_codex = home / ".agents/skills/usw-init"
            legacy_qwen.mkdir(parents=True)
            legacy_codex.mkdir(parents=True)
            (legacy_qwen / "SKILL.md").write_text("legacy\n", encoding="utf-8")
            (legacy_codex / "SKILL.md").write_text("legacy\n", encoding="utf-8")

            result = self.run_install(home, "--force")

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse(legacy_qwen.exists())
            self.assertFalse(legacy_codex.exists())


if __name__ == "__main__":
    unittest.main()
