import importlib.util
import json
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

    def test_router_round_trips_empty_and_sorted_operations(self):
        empty = HANDOFF.render_router()
        self.assertEqual(
            "# Developer Handoff Router\n\n"
            "## Operations\n\n"
            "No registered operations.\n",
            empty,
        )
        self.assertEqual((), HANDOFF.validate_router(empty))

        first = "usw-operation:" + "1" * 64
        second = "usw-operation:" + "2" * 64
        content = HANDOFF.render_router([second, first])

        self.assertEqual((first, second), HANDOFF.validate_router(content))
        self.assertEqual(content, HANDOFF.render_router([first, second]))
        self.assertNotIn("Status", content)

    def test_router_rejects_duplicate_malformed_and_arbitrary_paths(self):
        operation = "usw-operation:" + "1" * 64
        entry = (
            f"- `{operation}` -> "
            f"`{HANDOFF.operation_relative_path(operation)}`"
        )
        prefix = "# Developer Handoff Router\n\n## Operations\n\n"

        for content in (
            prefix + f"{entry}\n{entry}\n",
            prefix + f"- `{operation}` -> `../outside.md`\n",
            prefix + f"- `{operation}` -> `handoffs/{'2' * 64}.md`\n",
            prefix + "No registered operations.\n" + entry + "\n",
        ):
            with self.subTest(content=content), self.assertRaises(
                HANDOFF.HandoffError
            ):
                HANDOFF.parse_router(content)

        with self.assertRaisesRegex(HANDOFF.HandoffError, "duplicate"):
            HANDOFF.render_router([operation, operation])

    def test_router_generic_and_legacy_formats_are_distinguishable(self):
        legacy = (
            "# Developer Handoff\n\n"
            "| Subject | Role | Attempt | Current operation | Status | Updated |\n"
            "|---|---|---|---|---|---|\n"
            "| task/a/1 | Development | x:1/1 | op-001 | paused | 2026-07-30T10:00:00+03:00 |\n"
        )

        self.assertEqual("router", HANDOFF.handoff_format(HANDOFF.render_router()))
        self.assertEqual("generic", HANDOFF.handoff_format(HANDOFF.render_idle()))
        self.assertEqual("legacy", HANDOFF.handoff_format(legacy))

    def test_operation_paths_are_derived_and_read_descriptor_relative(self):
        with tempfile.TemporaryDirectory() as directory:
            project, _ = self.initialize(directory)
            content = HANDOFF.render_begin(
                "review", "shared", self.identity, "input"
            )
            operation = HANDOFF.parse_handoff(content).metadata["Operation"]

            with HANDOFF._locked_local_directory(project) as (_, local_descriptor):
                with HANDOFF._opened_operation_directory(
                    project, local_descriptor, create=True
                ) as (operation_directory, _):
                    self.assertEqual(
                        project / ".usw/handoffs",
                        operation_directory,
                    )
                    self.assertEqual(
                        0o700, operation_directory.stat().st_mode & 0o777
                    )
                    operation_path = (
                        operation_directory / HANDOFF.operation_filename(operation)
                    )
                    operation_path.write_text(content, encoding="utf-8")

                path, saved, parsed = HANDOFF._read_operation_at(
                    project, local_descriptor, operation
                )

            self.assertEqual(operation_path, path)
            self.assertEqual(content, saved)
            self.assertEqual(operation, parsed.metadata["Operation"])
            self.assertEqual(
                f"handoffs/{HANDOFF.operation_filename(operation)}",
                HANDOFF.operation_relative_path(operation),
            )
            for invalid in ("../../outside", "usw-operation:" + "g" * 64):
                with self.assertRaisesRegex(
                    HANDOFF.HandoffError, "operation identity"
                ):
                    HANDOFF.operation_filename(invalid)

    def test_operation_directory_symlink_and_identity_mismatch_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            project, _ = self.initialize(directory)
            outside = project / "outside"
            outside.mkdir()
            os.symlink(outside, project / ".usw/handoffs")

            with HANDOFF._locked_local_directory(project) as (_, descriptor):
                with self.assertRaisesRegex(HANDOFF.HandoffError, "unsafe"):
                    with HANDOFF._opened_operation_directory(project, descriptor):
                        pass

        with tempfile.TemporaryDirectory() as directory:
            project, _ = self.initialize(directory)
            first_content = HANDOFF.render_begin(
                "review", "shared", self.identity, "first"
            )
            second_content = HANDOFF.render_begin(
                "review", "shared", self.identity, "second"
            )
            first = HANDOFF.parse_handoff(first_content).metadata["Operation"]
            second = HANDOFF.parse_handoff(second_content).metadata["Operation"]
            operation_directory = project / ".usw/handoffs"
            operation_directory.mkdir()
            victim = project / "victim.md"
            victim.write_text(first_content, encoding="utf-8")
            os.symlink(
                victim,
                operation_directory / HANDOFF.operation_filename(first),
            )

            with HANDOFF._locked_local_directory(project) as (_, descriptor):
                with self.assertRaisesRegex(HANDOFF.HandoffError, "unsafe"):
                    HANDOFF._read_operation_at(project, descriptor, first)

                mismatched = (
                    operation_directory / HANDOFF.operation_filename(second)
                )
                mismatched.write_text(first_content, encoding="utf-8")
                with self.assertRaisesRegex(
                    HANDOFF.HandoffError, "identity does not match"
                ):
                    HANDOFF._read_operation_at(project, descriptor, second)

    def test_generic_idle_and_active_state_migrate_to_router(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)

            path, content, status = HANDOFF.read_handoff(project)

            self.assertEqual(handoff.resolve(), path)
            self.assertEqual("idle", status)
            self.assertEqual(HANDOFF.render_router(), content)
            self.assertEqual(content, handoff.read_text(encoding="utf-8"))
            self.assertFalse((project / ".usw/handoffs").exists())

        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            active = HANDOFF.render_begin(
                "review", "shared", self.identity, "recover me"
            ).replace("- Status: in_progress", "- Status: paused")
            operation = HANDOFF.parse_handoff(active).metadata["Operation"]
            handoff.write_text(active, encoding="utf-8")

            path, content, status = HANDOFF.read_handoff(project)

            self.assertEqual("paused", status)
            self.assertEqual(active, content)
            self.assertEqual(
                (
                    project
                    / ".usw"
                    / HANDOFF.operation_relative_path(operation)
                ).resolve(),
                path,
            )
            self.assertEqual(
                (operation,),
                HANDOFF.parse_router(
                    handoff.read_text(encoding="utf-8")
                ).operations,
            )
            self.assertEqual(active, path.read_text(encoding="utf-8"))

    def test_failed_generic_migration_preserves_original_and_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            active = HANDOFF.render_begin(
                "review", "shared", self.identity, "recover me"
            ).replace("- Status: in_progress", "- Status: paused")
            operation = HANDOFF.parse_handoff(active).metadata["Operation"]
            handoff.write_text(active, encoding="utf-8")

            with (
                mock.patch.object(
                    HANDOFF,
                    "_atomic_write",
                    side_effect=HANDOFF.HandoffError(
                        "write_verification", "simulated router failure"
                    ),
                ),
                self.assertRaisesRegex(
                    HANDOFF.HandoffError, "simulated router failure"
                ),
            ):
                HANDOFF.read_handoff(project)

            operation_path = (
                project / ".usw" / HANDOFF.operation_relative_path(operation)
            )
            self.assertEqual(active, handoff.read_text(encoding="utf-8"))
            self.assertFalse(operation_path.exists())

            path, content, status = HANDOFF.read_handoff(project)
            self.assertEqual(
                (operation_path.resolve(), active, "paused"),
                (path, content, status),
            )

    def test_show_and_resume_use_zero_one_many_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            project, _ = self.initialize(directory)
            empty = subprocess.run(
                [sys.executable, str(SCRIPT), "show", str(project)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual("idle", json.loads(empty.stdout)["status"])

            first_path, first = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "first"
            )
            path, content, status = HANDOFF.read_handoff(project)
            self.assertEqual(
                (first_path, "in_progress"),
                (path, status),
            )
            self.assertIn(first, content)

            _, second = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "second"
            )
            with self.assertRaisesRegex(
                HANDOFF.HandoffError, "select one"
            ):
                HANDOFF.read_handoff(project)

            selected_path, selected_content, selected_status = (
                HANDOFF.read_handoff(project, first)
            )
            self.assertEqual(first_path, selected_path)
            self.assertEqual("in_progress", selected_status)
            self.assertIn(first, selected_content)

            many = subprocess.run(
                [sys.executable, str(SCRIPT), "resume", str(project)],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(many.stdout)
            self.assertEqual("selection_required", payload["status"])
            self.assertEqual(
                sorted((first, second)),
                sorted(
                    item["operation"] for item in payload["operations"]
                ),
            )

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

            self.assertEqual(
                project.resolve()
                / ".usw"
                / HANDOFF.operation_relative_path(operation),
                path,
            )
            self.assertEqual("in_progress", parsed.status)
            self.assertEqual(operation, parsed.metadata["Operation"])
            self.assertRegex(parsed.metadata["Invocation"], r"^[0-9a-f]{32}$")
            self.assertEqual(
                '"exact\\n## not-a-handoff-section\\ninput"',
                parsed.sections["Input"],
            )
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            self.assertEqual(
                (operation,),
                HANDOFF.parse_router(
                    handoff.read_text(encoding="utf-8")
                ).operations,
            )

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

    def test_recoverable_statuses_do_not_block_independent_begin(self):
        for status in sorted(HANDOFF.RECOVERABLE_STATUSES):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                project, handoff = self.initialize(directory)
                active = HANDOFF.render_begin(
                    "review", "shared", self.identity, "input"
                ).replace("- Status: in_progress", f"- Status: {status}")
                handoff.write_text(active, encoding="utf-8")
                first = HANDOFF.parse_handoff(active).metadata["Operation"]
                _, second = HANDOFF.begin_handoff(
                    project, "review", "shared", self.identity, "new input"
                )
                self.assertNotEqual(first, second)
                self.assertEqual(
                    tuple(sorted((first, second))),
                    HANDOFF.parse_router(
                        handoff.read_text(encoding="utf-8")
                    ).operations,
                )

    def test_terminal_statuses_remain_registered_after_new_begin(self):
        for status in sorted(HANDOFF.TERMINAL_STATUSES):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                project, handoff = self.initialize(directory)
                first_path, first = HANDOFF.begin_handoff(
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

                second_path, second = HANDOFF.begin_handoff(
                    project, "review", "shared", self.identity, "second input"
                )

                self.assertNotEqual(first, second)
                self.assertEqual(
                    tuple(sorted((first, second))),
                    HANDOFF.parse_router(
                        handoff.read_text(encoding="utf-8")
                    ).operations,
                )
                self.assertEqual(
                    status,
                    HANDOFF.validate_handoff(
                        first_path.read_text(encoding="utf-8")
                    ),
                )
                current = HANDOFF.parse_handoff(
                    second_path.read_text(encoding="utf-8")
                )
                self.assertEqual("in_progress", current.status)
                self.assertEqual('"second input"', current.sections["Input"])

    def test_concurrent_begin_registers_both_operations(self):
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

            self.assertEqual([0, 0], sorted(process.returncode for process in processes))
            operations = HANDOFF.parse_router(
                handoff.read_text(encoding="utf-8")
            ).operations
            self.assertEqual(2, len(operations))
            self.assertEqual(
                2, sum('"status": "in_progress"' in out for out, _ in results)
            )
            for operation in operations:
                state = (
                    project
                    / ".usw"
                    / HANDOFF.operation_relative_path(operation)
                )
                self.assertEqual(
                    "in_progress",
                    HANDOFF.validate_handoff(
                        state.read_text(encoding="utf-8")
                    ),
                )

    def test_begin_requires_exact_readback_and_preserves_competing_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            competing = HANDOFF.render_begin(
                "other", "shared", self.identity, "competing input"
            )
            competing_operation = HANDOFF.parse_handoff(
                competing
            ).metadata["Operation"]
            competing_router = HANDOFF.render_router([competing_operation])
            original_replace = HANDOFF.os.replace

            def replace_then_compete(*args, **kwargs):
                original_replace(*args, **kwargs)
                handoff.write_text(competing_router, encoding="utf-8")

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

            self.assertEqual(
                competing_router, handoff.read_text(encoding="utf-8")
            )

    def test_outcome_statuses_and_terminal_transition(self):
        for status in sorted(HANDOFF.OUTCOME_STATUSES):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                project, handoff = self.initialize(directory)
                path, operation = HANDOFF.begin_handoff(
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
                        path.read_text(encoding="utf-8")
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

    def test_concurrent_outcomes_update_only_their_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            first_path, first = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "first"
            )
            second_path, second = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "second"
            )
            processes = []
            for operation in (first, second):
                processes.append(
                    subprocess.Popen(
                        [
                            sys.executable,
                            str(SCRIPT),
                            "outcome",
                            str(project),
                            "completed",
                            "--operation",
                            operation,
                            "--done",
                            "Completed independently.",
                            "--position",
                            "At the terminal boundary.",
                            "--next-action",
                            "Finish this operation.",
                            "--blocker",
                            "None.",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                )
            results = [process.communicate(timeout=10) for process in processes]

            self.assertEqual([0, 0], [process.returncode for process in processes])
            self.assertTrue(all(not error for _, error in results))
            self.assertEqual(
                tuple(sorted((first, second))),
                HANDOFF.parse_router(
                    handoff.read_text(encoding="utf-8")
                ).operations,
            )
            for path in (first_path, second_path):
                self.assertEqual(
                    "completed",
                    HANDOFF.validate_handoff(
                        path.read_text(encoding="utf-8")
                    ),
                )

    def test_finish_unregisters_and_removes_the_selected_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            path, operation = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "input"
            )
            HANDOFF.finish_handoff(project, operation)
            self.assertEqual(
                (), HANDOFF.validate_router(handoff.read_text(encoding="utf-8"))
            )
            self.assertFalse(path.exists())

    def test_finish_requires_selection_and_preserves_competing_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            first_path, first = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "first"
            )
            second_path, second = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "second"
            )

            with self.assertRaisesRegex(
                HANDOFF.HandoffError, "select one"
            ):
                HANDOFF.finish_handoff(project)
            HANDOFF.finish_handoff(project, first)

            self.assertFalse(first_path.exists())
            self.assertTrue(second_path.exists())
            self.assertEqual(
                (second,),
                HANDOFF.parse_router(
                    handoff.read_text(encoding="utf-8")
                ).operations,
            )
            HANDOFF.finish_handoff(project)
            self.assertFalse(second_path.exists())
            self.assertEqual(
                (), HANDOFF.validate_router(handoff.read_text(encoding="utf-8"))
            )

    def test_finish_unregistration_makes_cleanup_failure_a_safe_orphan(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            path, operation = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "input"
            )
            original_unlink = HANDOFF.os.unlink

            def fail_operation_cleanup(name, *args, **kwargs):
                if name == HANDOFF.operation_filename(operation):
                    raise OSError("simulated cleanup failure")
                return original_unlink(name, *args, **kwargs)

            with (
                mock.patch.object(
                    HANDOFF.os,
                    "unlink",
                    side_effect=fail_operation_cleanup,
                ),
                self.assertRaisesRegex(OSError, "cleanup failure"),
            ):
                HANDOFF.finish_handoff(project, operation)

            self.assertEqual(
                (), HANDOFF.validate_router(handoff.read_text(encoding="utf-8"))
            )
            self.assertTrue(path.exists())

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
                (),
                HANDOFF.validate_router(handoff.read_text(encoding="utf-8")),
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

    def test_assert_current_is_read_only_for_exact_recoverable_parent(self):
        for status in sorted(HANDOFF.RECOVERABLE_STATUSES):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                project, handoff = self.initialize(directory)
                path, operation = HANDOFF.begin_handoff(
                    project, "review", "shared", self.identity, "input"
                )
                if status != "in_progress":
                    path.write_text(
                        path.read_text(encoding="utf-8").replace(
                            "- Status: in_progress", f"- Status: {status}"
                        ),
                        encoding="utf-8",
                    )
                before_router = handoff.read_bytes()
                before_operation = path.read_bytes()

                self.assertEqual(
                    path,
                    HANDOFF.assert_current_handoff(project, operation),
                )
                self.assertEqual(before_router, handoff.read_bytes())
                self.assertEqual(before_operation, path.read_bytes())

    def test_assert_current_rejects_stale_terminal_legacy_and_disabled_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            path, operation = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "input"
            )
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "- Status: in_progress", "- Status: completed"
                ),
                encoding="utf-8",
            )
            before = (handoff.read_bytes(), path.read_bytes())

            for requested in (operation, "usw-operation:" + "0" * 64):
                with self.subTest(requested=requested), self.assertRaisesRegex(
                    HANDOFF.HandoffError, "parent"
                ):
                    HANDOFF.assert_current_handoff(project, requested)
            self.assertEqual(before, (handoff.read_bytes(), path.read_bytes()))

        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            legacy = (
                "# Developer Handoff\n\n"
                "| Subject | Role | Attempt | Current operation | Status | Updated |\n"
                "|---|---|---|---|---|---|\n"
                "| task/a/1 | Development | x:1/1 | op-001 | paused | 2026-07-30T10:00:00+03:00 |\n"
            )
            handoff.write_text(legacy, encoding="utf-8")
            with self.assertRaisesRegex(HANDOFF.HandoffError, "routed parent"):
                HANDOFF.assert_current_handoff(
                    project, "usw-operation:" + "0" * 64
                )
            self.assertEqual(legacy, handoff.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory, enabled=False)
            handoff.write_bytes(b"\xff invalid")
            before = handoff.read_bytes()
            with self.assertRaisesRegex(HANDOFF.HandoffError, "disabled"):
                HANDOFF.assert_current_handoff(
                    project, "usw-operation:" + "0" * 64
                )
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
            path, operation = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "input"
            )
            candidate = (
                project
                / ".usw"
                / HANDOFF.operation_candidate_relative_path(operation)
            )
            candidate.write_text(
                path.read_text(encoding="utf-8").replace(
                    "Before model execution.",
                    "After one recoverable step.",
                ),
                encoding="utf-8",
            )
            saved, status = HANDOFF.save_handoff(
                project, operation, candidate
            )
            self.assertEqual((path, "in_progress"), (saved, status))
            self.assertFalse(candidate.exists())
            self.assertIn(
                "After one recoverable step.",
                path.read_text(encoding="utf-8"),
            )

            wrong = project / "wrong.md"
            wrong.write_text(HANDOFF.render_idle(), encoding="utf-8")
            with self.assertRaisesRegex(HANDOFF.HandoffError, "candidate must"):
                HANDOFF.save_handoff(project, operation, wrong)

    def test_concurrent_operation_scoped_save_candidates_do_not_collide(self):
        with tempfile.TemporaryDirectory() as directory:
            project, _ = self.initialize(directory)
            operations = [
                HANDOFF.begin_handoff(
                    project, "review", "shared", self.identity, value
                )
                for value in ("first", "second")
            ]
            processes = []
            for index, (path, operation) in enumerate(operations, start=1):
                candidate = (
                    project
                    / ".usw"
                    / HANDOFF.operation_candidate_relative_path(operation)
                )
                candidate.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "Before model execution.",
                        f"Saved operation {index}.",
                    ),
                    encoding="utf-8",
                )
                processes.append(
                    subprocess.Popen(
                        [
                            sys.executable,
                            str(SCRIPT),
                            "save",
                            str(project),
                            operation,
                            str(candidate),
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                )

            results = [process.communicate(timeout=10) for process in processes]

            self.assertEqual([0, 0], [process.returncode for process in processes])
            self.assertTrue(all(not error for _, error in results))
            for index, (path, operation) in enumerate(operations, start=1):
                self.assertIn(
                    f"Saved operation {index}.",
                    path.read_text(encoding="utf-8"),
                )
                self.assertFalse(
                    (
                        project
                        / ".usw"
                        / HANDOFF.operation_candidate_relative_path(operation)
                    ).exists()
                )

    def test_stale_outcome_cannot_rewrite_after_exact_finish(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            _, first = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "same input"
            )
            _, second = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "same input"
            )
            HANDOFF.finish_handoff(project, first)
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

    def test_late_outcome_and_queued_save_cannot_restore_finished_route(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            path, operation = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "input"
            )
            saved_state = path.read_bytes()
            candidate = (
                project
                / ".usw"
                / HANDOFF.operation_candidate_relative_path(operation)
            )
            HANDOFF.finish_handoff(project, operation)
            idle = handoff.read_bytes()
            candidate.write_bytes(saved_state)

            with self.assertRaisesRegex(HANDOFF.HandoffError, "stale"):
                HANDOFF.outcome_handoff(
                    project,
                    "completed",
                    operation=operation,
                    done="Late result.",
                    position="The operation was already finished.",
                    next_action="Do nothing.",
                    blocker="None.",
                )
            with self.assertRaisesRegex(HANDOFF.HandoffError, "stale"):
                HANDOFF.save_handoff(project, operation, candidate)

            self.assertEqual(idle, handoff.read_bytes())
            self.assertTrue(candidate.exists())

    def test_save_cannot_clear_replace_legacy_or_change_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            path, operation = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "input"
            )
            candidate = (
                project
                / ".usw"
                / HANDOFF.operation_candidate_relative_path(operation)
            )
            current = path.read_bytes()

            candidate.write_text(HANDOFF.render_idle(), encoding="utf-8")
            with self.assertRaisesRegex(HANDOFF.HandoffError, "finish"):
                HANDOFF.save_handoff(project, operation, candidate)
            self.assertEqual(current, path.read_bytes())

            candidate.write_text(
                HANDOFF.render_begin(
                    "review", "shared", self.identity, "different input"
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(HANDOFF.HandoffError, "operation identity"):
                HANDOFF.save_handoff(project, operation, candidate)
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
                HANDOFF.save_handoff(project, operation, candidate)
            self.assertEqual(legacy, handoff.read_text(encoding="utf-8"))

    def test_save_cannot_change_exact_input_or_flow_context(self):
        with tempfile.TemporaryDirectory() as directory:
            project, handoff = self.initialize(directory)
            path, operation = HANDOFF.begin_handoff(
                project, "review", "shared", self.identity, "original input"
            )
            candidate = (
                project
                / ".usw"
                / HANDOFF.operation_candidate_relative_path(operation)
            )
            current = path.read_text(encoding="utf-8")

            candidate.write_text(
                current.replace('"original input"', '"different input"'),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(HANDOFF.HandoffError, "input digest"):
                HANDOFF.save_handoff(project, operation, candidate)
            self.assertEqual(current, path.read_text(encoding="utf-8"))

            candidate.write_text(
                current.replace("- Flow: review", "- Flow: other"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                HANDOFF.HandoffError, "immutable operation context"
            ):
                HANDOFF.save_handoff(project, operation, candidate)
            self.assertEqual(current, path.read_text(encoding="utf-8"))

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
