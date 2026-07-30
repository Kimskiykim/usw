import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "skills/usw-manage-handoff/scripts/handoff_state.py"
SPEC = importlib.util.spec_from_file_location("generic_handoff", SCRIPT)
HANDOFF = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = HANDOFF
SPEC.loader.exec_module(HANDOFF)


class HandoffStateTests(unittest.TestCase):
    identity = "usw-markdown:shared:" + "a" * 64

    def initialize(self, directory: str, *, enabled: bool = True) -> tuple[Path, Path]:
        project = Path(directory)
        (project / "usw.yaml").write_text(
            f"schema_version: 1\nhandoff: {'true' if enabled else 'false'}\n",
            encoding="utf-8",
        )
        local = project / ".usw"
        local.mkdir()
        handoff = local / "HANDOFF.md"
        handoff.write_text(HANDOFF.render_idle(), encoding="utf-8")
        return project, handoff

    def test_idle_format_is_small_and_valid(self):
        content = HANDOFF.render_idle(
            datetime(2026, 7, 30, 10, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(
            "# Developer Handoff\n\n"
            "- Updated: 2026-07-30T10:00:00+00:00\n"
            "- Status: idle\n\n"
            "## Active work\n\n"
            "No active work.\n",
            content,
        )
        self.assertEqual("idle", HANDOFF.validate_handoff(content))

    def test_begin_binds_origin_flow_and_exact_input(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            path, operation = HANDOFF.begin_handoff(
                project,
                "review",
                "shared",
                self.identity,
                "exact\n## not-a-handoff-section\ninput",
            )
            parsed = HANDOFF.parse_handoff(path.read_text(encoding="utf-8"))

            self.assertEqual(handoff.resolve(), path)
            self.assertEqual("in_progress", parsed.status)
            self.assertEqual(operation, parsed.metadata["Operation"])
            self.assertRegex(parsed.metadata["Invocation"], r"^[0-9a-f]{32}$")
            self.assertEqual(
                '"exact\\n## not-a-handoff-section\\ninput"',
                parsed.sections["Input"],
            )
            self.assertEqual(0o600, handoff.stat().st_mode & 0o777)

    def test_operation_identity_is_unique_and_changes_with_input_and_origin(self):
        first = HANDOFF.parse_handoff(
            HANDOFF.render_begin("review", "shared", self.identity, "one")
        )
        repeated = HANDOFF.parse_handoff(
            HANDOFF.render_begin("review", "shared", self.identity, "one")
        )
        different_input = HANDOFF.parse_handoff(
            HANDOFF.render_begin("review", "shared", self.identity, "two")
        )
        local_identity = "usw-markdown:local:" + "a" * 64
        local = HANDOFF.parse_handoff(
            HANDOFF.render_begin("review", "local", local_identity, "one")
        )
        self.assertNotEqual(
            first.metadata["Operation"], repeated.metadata["Operation"]
        )
        self.assertNotEqual(
            first.metadata["Invocation"], repeated.metadata["Invocation"]
        )
        self.assertNotEqual(
            first.metadata["Operation"], different_input.metadata["Operation"]
        )
        self.assertNotEqual(
            first.metadata["Operation"], local.metadata["Operation"]
        )

    def test_recoverable_statuses_block_new_begin(self):
        for status in sorted(HANDOFF.RECOVERABLE_STATUSES):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                project, handoff = self.initialize(directory)
                active = HANDOFF.render_begin(
                    "review", "shared", self.identity, "input"
                ).replace("- Status: in_progress", f"- Status: {status}")
                handoff.write_text(active, encoding="utf-8")
                with self.assertRaisesRegex(HANDOFF.HandoffError, "non-idle"):
                    HANDOFF.begin_handoff(
                        project, "review", "shared", self.identity, "new input"
                    )

    def test_terminal_statuses_are_replaced_by_new_begin(self):
        for status in sorted(HANDOFF.TERMINAL_STATUSES):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                project, handoff = self.initialize(directory)
                _, first = HANDOFF.begin_handoff(
                    project, "review", "shared", self.identity, "first input"
                )
                HANDOFF.outcome_handoff(
                    project,
                    status,
                    operation=first,
                    done="First operation stopped.",
                    position="At a terminal boundary.",
                    next_action="Start another flow when needed.",
                    blocker="None.",
                )

                _, second = HANDOFF.begin_handoff(
                    project, "review", "shared", self.identity, "second input"
                )

                current = HANDOFF.parse_handoff(
                    handoff.read_text(encoding="utf-8")
                )
                self.assertEqual("in_progress", current.status)
                self.assertNotEqual(first, second)
                self.assertEqual('"second input"', current.sections["Input"])

    def test_concurrent_begin_allows_exactly_one_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            arguments = [
                sys.executable,
                str(SCRIPT),
                "begin",
                str(project),
                "review",
                "shared",
                self.identity,
                "same input",
            ]
            processes = [
                subprocess.Popen(
                    arguments,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for _ in range(2)
            ]
            results = [process.communicate(timeout=10) for process in processes]

            self.assertEqual([0, 2], sorted(process.returncode for process in processes))
            self.assertEqual(
                "in_progress",
                HANDOFF.validate_handoff(handoff.read_text(encoding="utf-8")),
            )
            self.assertEqual(1, sum('"status": "in_progress"' in out for out, _ in results))

    def test_begin_requires_exact_readback_and_preserves_competing_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            competing = HANDOFF.render_begin(
                "other", "shared", self.identity, "competing input"
            )
            original_replace = HANDOFF.os.replace

            def replace_then_compete(*args, **kwargs):
                original_replace(*args, **kwargs)
                handoff.write_text(competing, encoding="utf-8")

            with mock.patch.object(
                HANDOFF.os,
                "replace",
                side_effect=replace_then_compete,
            ):
                with self.assertRaisesRegex(
                    HANDOFF.HandoffError, "exact readback"
                ):
                    HANDOFF.begin_handoff(
                        project,
                        "review",
                        "shared",
                        self.identity,
                        "original input",
                    )

            self.assertEqual(competing, handoff.read_text(encoding="utf-8"))

    def test_outcome_statuses_and_terminal_transition(self):
        for status in sorted(HANDOFF.OUTCOME_STATUSES):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                project, handoff = self.initialize(directory)
                _, operation = HANDOFF.begin_handoff(
                    project, "review", "shared", self.identity, "input"
                )
                HANDOFF.outcome_handoff(
                    project,
                    status,
                    operation=operation,
                    done="One fact.",
                    position="At a natural boundary.",
                    next_action="Inspect or finish.",
                    blocker="None.",
                    checks=("check passed",),
                    references=("result.md",),
                )
                self.assertEqual(
                    status,
                    HANDOFF.validate_handoff(
                        handoff.read_text(encoding="utf-8")
                    ),
                )
                if status in {"failed", "completed"}:
                    with self.assertRaisesRegex(
                        HANDOFF.HandoffError, "terminal"
                    ):
                        HANDOFF.outcome_handoff(
                            project,
                            "paused",
                            operation=operation,
                            done="No.",
                            position="No.",
                            next_action="No.",
                            blocker="None.",
                        )

    def test_finish_is_only_transition_to_idle(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "input"
            )
            HANDOFF.finish_handoff(project)
            self.assertEqual(
                "idle", HANDOFF.validate_handoff(handoff.read_text(encoding="utf-8"))
            )

    def test_legacy_is_read_only_recovery_until_finish(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            legacy = (
                "# Developer Handoff\n\n"
                "| Subject | Role | Attempt | Current operation | Status | Updated |\n"
                "|---|---|---|---|---|---|\n"
                "| task/a/1 | Development | x:1/1 | op-001 | paused | 2026-07-30T10:00:00+03:00 |\n"
            )
            handoff.write_text(legacy, encoding="utf-8")

            _, content, status = HANDOFF.read_handoff(project)
            self.assertEqual(("paused", legacy), (status, content))
            self.assertTrue(HANDOFF.parse_handoff(content).legacy)
            with self.assertRaisesRegex(HANDOFF.HandoffError, "legacy"):
                HANDOFF.begin_handoff(
                    project, "review", "shared", self.identity, "input"
                )
            with self.assertRaisesRegex(HANDOFF.HandoffError, "legacy"):
                HANDOFF.outcome_handoff(
                    project,
                    "completed",
                    operation="usw-operation:" + "0" * 64,
                    done="Done.",
                    position="Done.",
                    next_action="Finish.",
                    blocker="None.",
                )
            self.assertEqual(legacy, handoff.read_text(encoding="utf-8"))
            HANDOFF.finish_handoff(project)
            self.assertEqual(
                "idle", HANDOFF.validate_handoff(handoff.read_text(encoding="utf-8"))
            )

    def test_disabled_config_does_not_read_or_change_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory, enabled=False)
            handoff.write_bytes(b"\xff invalid")
            before = handoff.read_bytes()

            for operation in (
                lambda: HANDOFF.read_handoff(project),
                lambda: HANDOFF.finish_handoff(project),
                lambda: HANDOFF.begin_handoff(
                    project, "review", "shared", self.identity, "input"
                ),
            ):
                with self.assertRaisesRegex(HANDOFF.HandoffError, "disabled"):
                    operation()
            self.assertEqual(before, handoff.read_bytes())

    def test_missing_and_symlinked_handoff_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "usw.yaml").write_text(
                "schema_version: 1\nhandoff: true\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(HANDOFF.HandoffError, "/usw-init"):
                HANDOFF.read_handoff(project)

            local = project / ".usw"
            local.mkdir()
            victim = project / "victim"
            victim.write_text(HANDOFF.render_idle(), encoding="utf-8")
            os.symlink(victim, local / "HANDOFF.md")
            with self.assertRaisesRegex(HANDOFF.HandoffError, "unsafe"):
                HANDOFF.read_handoff(project)
            self.assertEqual(
                HANDOFF.render_idle(), victim.read_text(encoding="utf-8")
            )

    def test_save_accepts_only_generic_exact_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "input"
            )
            candidate = project / ".usw/HANDOFF.next.md"
            candidate.write_text(
                handoff.read_text(encoding="utf-8").replace(
                    "Before model execution.",
                    "After one recoverable step.",
                ),
                encoding="utf-8",
            )
            saved, status = HANDOFF.save_handoff(project, candidate)
            self.assertEqual((handoff.resolve(), "in_progress"), (saved, status))
            self.assertFalse(candidate.exists())
            self.assertIn(
                "After one recoverable step.",
                handoff.read_text(encoding="utf-8"),
            )

            wrong = project / "wrong.md"
            wrong.write_text(HANDOFF.render_idle(), encoding="utf-8")
            with self.assertRaisesRegex(HANDOFF.HandoffError, "candidate must"):
                HANDOFF.save_handoff(project, wrong)

    def test_stale_outcome_cannot_rewrite_a_new_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            _, first = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "same input"
            )
            HANDOFF.outcome_handoff(
                project,
                "completed",
                operation=first,
                done="First operation completed.",
                position="At a terminal boundary.",
                next_action="Start another flow when needed.",
                blocker="None.",
            )
            _, second = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "same input"
            )
            before = handoff.read_bytes()

            with self.assertRaisesRegex(HANDOFF.HandoffError, "stale"):
                HANDOFF.outcome_handoff(
                    project,
                    "completed",
                    operation=first,
                    done="Stale result.",
                    position="Wrong operation.",
                    next_action="Do nothing.",
                    blocker="None.",
                )

            self.assertNotEqual(first, second)
            self.assertEqual(before, handoff.read_bytes())

    def test_late_outcome_and_queued_save_cannot_reopen_idle(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            _, operation = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "input"
            )
            candidate = project / ".usw/HANDOFF.next.md"
            candidate.write_bytes(handoff.read_bytes())
            HANDOFF.finish_handoff(project)
            idle = handoff.read_bytes()

            with self.assertRaisesRegex(HANDOFF.HandoffError, "current operation"):
                HANDOFF.outcome_handoff(
                    project,
                    "completed",
                    operation=operation,
                    done="Late result.",
                    position="The operation was already finished.",
                    next_action="Do nothing.",
                    blocker="None.",
                )
            with self.assertRaisesRegex(HANDOFF.HandoffError, "Begin"):
                HANDOFF.save_handoff(project, candidate)

            self.assertEqual(idle, handoff.read_bytes())
            self.assertTrue(candidate.exists())

    def test_save_cannot_clear_replace_legacy_or_change_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            candidate = project / ".usw/HANDOFF.next.md"
            _, operation = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "input"
            )
            current = handoff.read_bytes()

            candidate.write_text(HANDOFF.render_idle(), encoding="utf-8")
            with self.assertRaisesRegex(HANDOFF.HandoffError, "finish"):
                HANDOFF.save_handoff(project, candidate)
            self.assertEqual(current, handoff.read_bytes())

            candidate.write_text(
                HANDOFF.render_begin(
                    "review", "shared", self.identity, "different input"
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(HANDOFF.HandoffError, "operation identity"):
                HANDOFF.save_handoff(project, candidate)
            self.assertIn(operation, handoff.read_text(encoding="utf-8"))

            legacy = (
                "# Developer Handoff\n\n"
                "| Subject | Role | Attempt | Current operation | Status | Updated |\n"
                "|---|---|---|---|---|---|\n"
                "| task/a/1 | Development | x:1/1 | op-001 | paused | 2026-07-30T10:00:00+03:00 |\n"
            )
            handoff.write_text(legacy, encoding="utf-8")
            candidate.write_text(
                HANDOFF.render_begin(
                    "review", "shared", self.identity, "candidate"
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(HANDOFF.HandoffError, "legacy"):
                HANDOFF.save_handoff(project, candidate)
            self.assertEqual(legacy, handoff.read_text(encoding="utf-8"))

    def test_save_cannot_change_exact_input_or_flow_context(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            candidate = project / ".usw/HANDOFF.next.md"
            HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "original input"
            )
            current = handoff.read_text(encoding="utf-8")

            candidate.write_text(
                current.replace('"original input"', '"different input"'),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(HANDOFF.HandoffError, "input digest"):
                HANDOFF.save_handoff(project, candidate)
            self.assertEqual(current, handoff.read_text(encoding="utf-8"))

            candidate.write_text(
                current.replace("- Flow: review", "- Flow: other"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                HANDOFF.HandoffError, "immutable operation context"
            ):
                HANDOFF.save_handoff(project, candidate)
            self.assertEqual(current, handoff.read_text(encoding="utf-8"))

    def test_invalid_next_action_is_rejected(self):
        content = HANDOFF.render_begin(
            "review", "shared", self.identity, "input"
        ).replace(
            "Execute the loaded Markdown flow.",
            "First action.\nSecond action.",
        )
        with self.assertRaisesRegex(HANDOFF.HandoffError, "Next action"):
            HANDOFF.parse_handoff(content)


if __name__ == "__main__":
    unittest.main()
