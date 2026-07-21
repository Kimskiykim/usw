import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
VERSION_FILE = ROOT / "tests/openspec-version.txt"


class OpenSpecCompatibilityTests(unittest.TestCase):
    def test_pinned_source_is_single_plain_version_value(self):
        content = VERSION_FILE.read_text(encoding="utf-8")
        self.assertEqual("1.6.0\n", content)


if __name__ == "__main__":
    unittest.main()
