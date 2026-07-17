import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "skills"
    / "usw-initialize-project"
    / "scripts"
    / "init_usw.py"
)
SPEC = importlib.util.spec_from_file_location("init_usw", SCRIPT_PATH)
INIT_USW = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(INIT_USW)


class InitializeUswTests(unittest.TestCase):
    def test_creates_project_files(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)

            results = INIT_USW.initialize_usw(project)
            (sync_file, sync_created), (hello_file, hello_created) = results

            self.assertTrue(sync_created)
            self.assertEqual(project.resolve() / "usw" / "SYNC.md", sync_file)
            self.assertEqual("# SYNC\n", sync_file.read_text(encoding="utf-8"))
            self.assertTrue(hello_created)
            self.assertEqual(project.resolve() / "hello_world.py", hello_file)
            self.assertEqual(
                'print("Hello, World!")\n',
                hello_file.read_text(encoding="utf-8"),
            )

    def test_uses_nearest_git_root(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".git").mkdir()
            nested = project / "src" / "feature"
            nested.mkdir(parents=True)

            results = INIT_USW.initialize_usw(nested)
            (sync_file, _), (hello_file, _) = results

            self.assertEqual(project.resolve() / "usw" / "SYNC.md", sync_file)
            self.assertEqual(project.resolve() / "hello_world.py", hello_file)

    def test_does_not_overwrite_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            sync_file = project / "usw" / "SYNC.md"
            sync_file.parent.mkdir()
            sync_file.write_text("existing content\n", encoding="utf-8")
            hello_file = project / "hello_world.py"
            hello_file.write_text("existing hello\n", encoding="utf-8")

            results = INIT_USW.initialize_usw(project)
            (returned_sync, sync_created), (returned_hello, hello_created) = results

            self.assertFalse(sync_created)
            self.assertEqual(sync_file.resolve(), returned_sync)
            self.assertEqual("existing content\n", sync_file.read_text(encoding="utf-8"))
            self.assertFalse(hello_created)
            self.assertEqual(hello_file.resolve(), returned_hello)
            self.assertEqual("existing hello\n", hello_file.read_text(encoding="utf-8"))

    def test_fails_when_usw_path_is_a_file(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "usw").write_text("not a directory", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                INIT_USW.initialize_usw(project)


if __name__ == "__main__":
    unittest.main()
