import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class PackageLayoutTests(unittest.TestCase):
    def test_public_command_delegates_to_internal_skill(self):
        command = (ROOT / "plugins/usw/commands/usw-init.md").read_text(
            encoding="utf-8"
        )

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

    def test_codex_marketplace_points_to_plugin(self):
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        plugin = marketplace["plugins"][0]
        plugin_dir = ROOT / plugin["source"]["path"]

        self.assertEqual("usw", marketplace["name"])
        self.assertTrue((plugin_dir / ".codex-plugin" / "plugin.json").is_file())
        self.assertTrue((plugin_dir / "commands" / "usw-init.md").is_file())
        self.assertTrue(
            (plugin_dir / "skills" / "usw-initialize-project" / "SKILL.md").is_file()
        )

    def test_only_qwen_and_codex_are_packaged(self):
        self.assertFalse((ROOT / ".claude-plugin").exists())
        self.assertFalse((ROOT / "plugins" / "usw" / ".claude-plugin").exists())


if __name__ == "__main__":
    unittest.main()
