import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class PackageLayoutTests(unittest.TestCase):
    def test_public_command_delegates_to_internal_skill(self):
        command = (ROOT / "commands/usw-init.md").read_text(encoding="utf-8")

        self.assertIn("usw-initialize-project", command)

    def test_qwen_extension_points_to_shared_skills(self):
        manifest = json.loads((ROOT / "qwen-extension.json").read_text(encoding="utf-8"))

        skills_dir = ROOT / manifest["skills"]
        commands_dir = ROOT / manifest["commands"]

        self.assertEqual("usw", manifest["name"])
        self.assertTrue(
            (skills_dir / "usw-initialize-project" / "SKILL.md").is_file()
        )
        self.assertTrue((commands_dir / "usw-init.md").is_file())

    def test_gigacode_extension_points_to_shared_skills(self):
        manifest = json.loads(
            (ROOT / "gigacode-extension.json").read_text(encoding="utf-8")
        )

        skills_dir = ROOT / manifest["skills"]
        commands_dir = ROOT / manifest["commands"]

        self.assertEqual("usw", manifest["name"])
        self.assertTrue(
            (skills_dir / "usw-initialize-project" / "SKILL.md").is_file()
        )
        self.assertTrue((commands_dir / "usw-init.md").is_file())

    def test_codex_marketplace_points_to_plugin(self):
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        plugin = marketplace["plugins"][0]

        self.assertEqual("usw", marketplace["name"])
        self.assertEqual("url", plugin["source"]["source"])
        self.assertEqual(
            "https://github.com/Kimskiykim/usw.git", plugin["source"]["url"]
        )
        self.assertTrue((ROOT / ".codex-plugin" / "plugin.json").is_file())
        self.assertTrue((ROOT / "commands" / "usw-init.md").is_file())
        self.assertTrue(
            (ROOT / "skills" / "usw-initialize-project" / "SKILL.md").is_file()
        )

    def test_claude_plugin_is_not_packaged(self):
        self.assertFalse((ROOT / ".claude-plugin").exists())
        self.assertFalse((ROOT / "plugins").exists())


if __name__ == "__main__":
    unittest.main()
