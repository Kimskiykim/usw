import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "skills/usw-refine-intent/scripts/refinement_state.py"
SPEC = importlib.util.spec_from_file_location("refinement_state", SCRIPT)
REFINE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = REFINE
SPEC.loader.exec_module(REFINE)


class RefineTaskTests(unittest.TestCase):
    def case(self, case_id="scope", title="Scope"):
        return REFINE.DecisionCase(
            case_id,
            title,
            "Choose the boundary",
            "It changes delivery",
            ("small", "large"),
            "small",
        )

    def initialize(self, project: Path, legacy_root: str | None = None):
        local = project / ".usw"
        local.mkdir()
        (local / ".gitignore").write_text("*\n", encoding="utf-8")
        config = "schema_version: 1\nartifacts:\n  provider: standalone\n"
        if legacy_root:
            config += f"refinement:\n  root: {legacy_root}\n"
        (project / "usw.yaml").write_text(config, encoding="utf-8")

    def test_new_and_resumed_session_use_only_local_root(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize(project, "shared/refinements")
            first = REFINE.start_or_resume(
                project,
                refinement_id="example",
                title="Example",
                goal="Agree the shape",
                target="change/example",
                cases=[self.case()],
            )
            second = REFINE.start_or_resume(
                project,
                refinement_id="example",
                title="Example",
                goal="Agree the shape",
                target="change/example",
                cases=[self.case()],
            )
            self.assertEqual("started", first.status)
            self.assertEqual("resumed", second.status)
            self.assertTrue((project / ".usw/refinements/example/session.md").is_file())
            self.assertFalse((project / "shared/refinements").exists())

    def test_unconfirmed_answer_does_not_write_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize(project)
            case = self.case()
            REFINE.start_or_resume(
                project, refinement_id="example", title="Example", goal="Goal",
                target="none", cases=[case],
            )
            decisions = project / ".usw/refinements/example/decisions.md"
            before = decisions.read_bytes()
            result = REFINE.decide_current_case(
                project, refinement_id="example", case=case, decision="small",
                basis="user said so", consequences="bounded", confirmed=False,
            )
            self.assertEqual("confirmation_required", result.status)
            self.assertEqual(before, decisions.read_bytes())

    def test_one_turn_closes_only_one_case(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize(project)
            first = self.case("scope", "Scope")
            second = self.case("storage", "Storage")
            REFINE.start_or_resume(
                project, refinement_id="example", title="Example", goal="Goal",
                target="none", cases=[first, second],
            )
            result = REFINE.decide_current_case(
                project, refinement_id="example", case=first, decision="small",
                basis="user choice", consequences="one package", confirmed=True,
                remaining_cases=[second],
            )
            session = (project / ".usw/refinements/example/session.md").read_text()
            self.assertEqual("active", result.status)
            self.assertEqual("storage", result.current_case)
            self.assertIn("- [x] `scope`", session)
            self.assertIn("- [ ] `storage`", session)
            self.assertEqual(1, (project / ".usw/refinements/example/decisions.md").read_text().count("## `D-"))

    def test_ready_outcome_uses_only_current_accepted_decisions(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize(project)
            case = self.case()
            REFINE.start_or_resume(
                project, refinement_id="example", title="Example", goal="Goal",
                target="none", cases=[case],
            )
            first = REFINE.decide_current_case(
                project, refinement_id="example", case=case, decision="small",
                basis="first", consequences="bounded", confirmed=True,
                timestamp=datetime(2026, 7, 21, 10, tzinfo=timezone.utc),
            )
            self.assertEqual("ready", first.status)
            second = REFINE.decide_current_case(
                project, refinement_id="example", case=case, decision="large",
                basis="revised", consequences="broader", confirmed=True,
                supersedes="D-001",
            )
            decisions = (project / ".usw/refinements/example/decisions.md").read_text()
            outcome = (project / ".usw/refinements/example/outcome.md").read_text()
            self.assertEqual("ready", second.status)
            self.assertIn("- Status: superseded", decisions)
            self.assertIn("- Replaced by: `D-002`", decisions)
            self.assertIn("- large", outcome)
            self.assertNotIn("- small", outcome)
            self.assertIn("- `D-002`", outcome)
            self.assertNotIn("- `D-001`", outcome)
            self.assertIn("## Recommended next flow\n\nnone", outcome)
            self.assertFalse((project / "product.py").exists())

    def test_matching_legacy_session_requires_explicit_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize(project, "shared/refinements")
            legacy = project / "shared/refinements/example/session.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("legacy bytes\n", encoding="utf-8")
            before = legacy.read_bytes()

            with self.assertRaisesRegex(REFINE.RefinementError, "explicit migration"):
                REFINE.start_or_resume(
                    project, refinement_id="example", title="Example", goal="Goal",
                    target="none", cases=[self.case()],
                )

            self.assertEqual(before, legacy.read_bytes())
            self.assertFalse((project / ".usw/refinements/example").exists())

    def test_rejects_symlinked_local_refinement_root(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            outside = Path(directory) / "outside"
            project.mkdir()
            outside.mkdir()
            self.initialize(project)
            os.symlink(outside, project / ".usw/refinements")

            with self.assertRaisesRegex(OSError, "symbolic links"):
                REFINE.start_or_resume(
                    project, refinement_id="example", title="Example", goal="Goal",
                    target="none", cases=[self.case()],
                )

            self.assertEqual([], list(outside.iterdir()))

    def test_rejects_local_state_not_ignored_by_git(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            subprocess.run(["git", "init", "--quiet", str(project)], check=True)
            self.initialize(project)
            (project / ".usw/.gitignore").write_text("*.tmp\n", encoding="utf-8")

            with self.assertRaisesRegex(REFINE.RefinementError, "not ignored"):
                REFINE.start_or_resume(
                    project, refinement_id="example", title="Example", goal="Goal",
                    target="none", cases=[self.case()],
                )

            self.assertFalse((project / ".usw/refinements").exists())

    def test_cases_require_two_or_three_options(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.initialize(project)
            invalid = REFINE.DecisionCase("x", "X", "p", "i", ("one",), "one")
            with self.assertRaisesRegex(REFINE.RefinementError, "two or three"):
                REFINE.start_or_resume(
                    project, refinement_id="example", title="Example", goal="Goal",
                    target="none", cases=[invalid],
                )


if __name__ == "__main__":
    unittest.main()
