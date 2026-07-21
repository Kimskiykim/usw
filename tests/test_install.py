import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
INSTALL = ROOT / "install.sh"


class InstallTests(unittest.TestCase):
    SKILL_NAMES = (
        "usw-initialize-project",
        "usw-manage-handoff",
        "usw-brainstorm-solutions",
        "usw-refine-task",
        "usw-plan-small-steps",
        "usw-explain-me",
        "usw-create-flow",
        "usw-run-flow",
        "usw-manage-artifacts",
        "usw-execute-task",
        "usw-verify-task",
    )
    COMMAND_NAMES = ("usw-init.md", "usw-handoff.md", "usw-resume.md")

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

    def test_installs_all_components_for_both_agents_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)

            result = self.run_install(home)

            self.assertEqual(0, result.returncode, result.stderr)
            for skills_dir in (home / ".qwen/skills", home / ".agents/skills"):
                for skill_name in self.SKILL_NAMES:
                    self.assertTrue((skills_dir / skill_name / "SKILL.md").is_file())
                self.assertTrue(
                    (
                        skills_dir
                        / "usw-initialize-project/templates/openspec/AGENTS.md"
                    ).is_file()
                )
                self.assertTrue(
                    (
                        skills_dir
                        / "usw-initialize-project/templates/task/task.md"
                    ).is_file()
                )
            for commands_dir in (home / ".qwen/commands", home / ".codex/prompts"):
                for command_name in self.COMMAND_NAMES:
                    self.assertTrue((commands_dir / command_name).is_file())

    def test_refuses_to_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(0, self.run_install(home).returncode)
            installed_skill = home / ".qwen/skills/usw-initialize-project/SKILL.md"
            installed_skill.write_text("local change\n", encoding="utf-8")

            result = self.run_install(home)

            self.assertEqual(1, result.returncode)
            self.assertEqual("local change\n", installed_skill.read_text(encoding="utf-8"))

    def test_force_replaces_existing_components(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(0, self.run_install(home).returncode)
            installed_skills = []
            for skills_dir in (home / ".qwen/skills", home / ".agents/skills"):
                for skill_name in self.SKILL_NAMES:
                    path = skills_dir / skill_name / "SKILL.md"
                    path.write_text("stale\n", encoding="utf-8")
                    installed_skills.append((skill_name, path))
            installed_commands = []
            for commands_dir in (home / ".qwen/commands", home / ".codex/prompts"):
                for command_name in self.COMMAND_NAMES:
                    path = commands_dir / command_name
                    path.write_text("stale\n", encoding="utf-8")
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
