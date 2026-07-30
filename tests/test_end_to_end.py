import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


INIT = load("e2e_init", "skills/usw-initialize-project/scripts/init_usw.py")
RUNNER = load("e2e_runner", "skills/usw-run-flow/scripts/run_flow.py")
HANDOFF = load("e2e_handoff", "skills/usw-manage-handoff/scripts/handoff_state.py")


class TextFirstEndToEndTests(unittest.TestCase):
    def test_init_resolve_begin_outcome_and_finish(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            INIT.initialize_usw(project)
            flow = project / "usw/flows/review.md"
            flow.write_text("# Review\n\nFollow the input.\n", encoding="utf-8")

            invocation = RUNNER.prepare_markdown_run(
                project, project / "usw/flows", "review", "check the change"
            )
            handoff, operation = HANDOFF.begin_handoff(
                project,
                invocation.flow.name,
                invocation.flow.origin,
                invocation.flow.identity,
                invocation.user_input,
            )
            self.assertIn(operation, handoff.read_text(encoding="utf-8"))

            HANDOFF.outcome_handoff(
                project,
                "completed",
                operation=operation,
                done="Reviewed the change.",
                position="Flow completed.",
                next_action="Start another flow when needed.",
                blocker="None.",
                checks=("unit tests passed",),
                references=("review.md",),
            )
            self.assertEqual(
                "completed",
                HANDOFF.validate_handoff(handoff.read_text(encoding="utf-8")),
            )
            _, next_operation = HANDOFF.begin_handoff(
                project,
                invocation.flow.name,
                invocation.flow.origin,
                invocation.flow.identity,
                "new input",
            )
            self.assertNotEqual(operation, next_operation)
            self.assertEqual(
                "in_progress",
                HANDOFF.validate_handoff(handoff.read_text(encoding="utf-8")),
            )

            HANDOFF.finish_handoff(project)
            self.assertEqual(
                "idle",
                HANDOFF.validate_handoff(handoff.read_text(encoding="utf-8")),
            )

    def test_handoff_false_runs_without_reading_existing_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "usw.yaml").write_text(
                "schema_version: 1\nhandoff: false\n", encoding="utf-8"
            )
            existing = project / ".usw/HANDOFF.md"
            existing.parent.mkdir()
            existing.write_text("invalid user bytes\n", encoding="utf-8")
            before = existing.read_bytes()

            INIT.initialize_usw(project)
            flow = project / "usw/flows/review.md"
            flow.write_text("Review.\n", encoding="utf-8")
            invocation = RUNNER.prepare_markdown_run(
                project, project / "usw/flows", "review", "input"
            )

            self.assertEqual("Review.\n", invocation.flow.markdown)
            self.assertEqual(before, existing.read_bytes())
            with self.assertRaisesRegex(HANDOFF.HandoffError, "disabled"):
                HANDOFF.read_handoff(project)
            self.assertEqual(before, existing.read_bytes())

    def test_legacy_flow_and_handoff_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            INIT.initialize_usw(project)
            legacy_flow = project / ".usw/FLOW.json"
            legacy_flow.write_text("{legacy", encoding="utf-8")
            legacy_handoff = (
                "# Developer Handoff\n\n"
                "| Subject | Role | Attempt | Current operation | Status | Updated |\n"
                "|---|---|---|---|---|---|\n"
                "| task/a/1 | Development | old:1/1 | op-001 | paused | 2026-07-30T10:00:00+03:00 |\n"
            )
            handoff = project / ".usw/HANDOFF.md"
            handoff.write_text(legacy_handoff, encoding="utf-8")
            flow = project / "usw/flows/review.md"
            flow.write_text("Review.\n", encoding="utf-8")

            invocation = RUNNER.prepare_markdown_run(
                project, project / "usw/flows", "review", "input"
            )
            _, content, status = HANDOFF.read_handoff(project)

            self.assertEqual(1, len(invocation.warnings))
            self.assertEqual(("paused", legacy_handoff), (status, content))
            with self.assertRaisesRegex(HANDOFF.HandoffError, "legacy"):
                HANDOFF.begin_handoff(
                    project,
                    invocation.flow.name,
                    invocation.flow.origin,
                    invocation.flow.identity,
                    invocation.user_input,
                )
            self.assertEqual("{legacy", legacy_flow.read_text(encoding="utf-8"))
            self.assertEqual(legacy_handoff, handoff.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
