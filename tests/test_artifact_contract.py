import importlib.util
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = (
    ROOT
    / "skills"
    / "usw-initialize-project"
    / "scripts"
    / "artifact_contract.py"
)
SPEC = importlib.util.spec_from_file_location("artifact_contract", SCRIPT_PATH)
ARTIFACTS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ARTIFACTS)


class ArtifactContractTests(unittest.TestCase):
    def test_active_change_has_only_explicit_frozen_legacy_tasks(self):
        change = ROOT / "openspec/changes/establish-standalone-usw-workflow"
        legacy = {
            "1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "3.3",
            "4.1", "5.1", "5.2", "5.3", "6.1",
        }

        ARTIFACTS.validate_change_tasks(change, legacy)

    def test_v1_contract_requires_sections_and_excludes_milestones_from_identity(self):
        template = (
            ROOT / "skills/usw-initialize-project/templates/task/task.md"
        ).read_text(encoding="utf-8")
        for section in ARTIFACTS.REQUIRED_V1_SECTIONS:
            self.assertIn(f"## {section}", template)
        self.assertIn("- `v1`", template)

        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / "task.md"
            task.write_text(template, encoding="utf-8")
            first = ARTIFACTS.task_contract_identity(task)
            task.write_text(template + "| 2 | repair | c | s | done | r |\n", encoding="utf-8")
            self.assertEqual(first, ARTIFACTS.task_contract_identity(task))

    def test_checkbox_outside_tasks_index_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            change = Path(directory)
            task_dir = change / "tasks/7-new"
            task_dir.mkdir(parents=True)
            (change / "tasks.md").write_text(
                "- [ ] 7 [New](tasks/7-new/task.md)\n", encoding="utf-8"
            )
            (task_dir / "task.md").write_text(
                "## Artifact model\n\n- `legacy`\n\n- [ ] duplicated\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ARTIFACTS.ContractError, "checkbox"):
                ARTIFACTS.validate_change_tasks(change, {"7"})

    def test_task_outside_frozen_allowlist_cannot_be_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            change = Path(directory)
            task_dir = change / "tasks/7-new"
            task_dir.mkdir(parents=True)
            (change / "tasks.md").write_text(
                "- [ ] 7 [New](tasks/7-new/task.md)\n", encoding="utf-8"
            )
            (task_dir / "task.md").write_text(
                "## Artifact model\n\n- `legacy`\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(ARTIFACTS.ContractError, "not frozen"):
                ARTIFACTS.validate_change_tasks(change, set())

    def test_unlinked_checkbox_in_tasks_index_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            change = Path(directory)
            (change / "tasks.md").write_text("- [x] undocumented work\n", encoding="utf-8")
            with self.assertRaisesRegex(ARTIFACTS.ContractError, "linked task"):
                ARTIFACTS.validate_change_tasks(change, set())

    def test_completed_v1_task_requires_current_successful_development_evidence(self):
        source = "usw-source-v1:" + "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            change = Path(directory)
            task_dir = change / "tasks/7-new"
            task_dir.mkdir(parents=True)
            (change / "tasks.md").write_text(
                "- [x] 7 [New](tasks/7-new/task.md)\n", encoding="utf-8"
            )
            task_content = (
                "## Artifact model\n\n- `v1`\n\n"
                + "".join(
                    f"## {section}\n\nvalue\n\n"
                    for section in ARTIFACTS.REQUIRED_V1_SECTIONS
                    if section not in {"Verification", "Contract revision", "Milestone log"}
                )
                + "## Verification\n\n- Run: `unit-test`\n\n"
                + "## Contract revision\n\n- `c1`\n\n"
                + "## Milestone log\n\n"
                + "| Attempt | Trigger | Contract | Source | Outcome | References |\n"
                + "|---|---|---|---|---|---|\n"
            )
            (task_dir / "task.md").write_text(task_content, encoding="utf-8")

            with self.assertRaisesRegex(ARTIFACTS.ContractError, "Development evidence"):
                ARTIFACTS.validate_change_tasks(
                    change, set(), current_source_identity=source
                )

            (task_dir / "development-evidence.md").write_text(
                "# Development evidence\n\n"
                "| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |\n"
                "|---|---|---|---|---|---|\n"
                f"| dev-1 | `c1` | `{source}` | `unit-test` | passed | now |\n",
                encoding="utf-8",
            )
            ARTIFACTS.validate_change_tasks(
                change, set(), current_source_identity=source
            )

    def test_typed_subjects_are_distinct_and_unsafe_segments_are_rejected(self):
        self.assertEqual(("refinement", "same"), ARTIFACTS.receipt_subject_parts("refinement/same"))
        self.assertEqual(("change", "same"), ARTIFACTS.receipt_subject_parts("change/same"))
        self.assertEqual(("task", "same", "1.1"), ARTIFACTS.receipt_subject_parts("task/same/1.1"))
        for subject in ("task/../1", "change/a/b", "/change/a", "unknown/a"):
            with self.subTest(subject=subject), self.assertRaises(ARTIFACTS.ContractError):
                ARTIFACTS.receipt_subject_parts(subject)

    def test_internal_receipt_is_immutable_and_tracks_artifact_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            artifact = project / "proposal.md"
            artifact.write_text("v1\n", encoding="utf-8")
            receipt = ARTIFACTS.write_receipt(
                project,
                project / "usw/reviews",
                receipt_id="review-1",
                gate="internal",
                owner_role="Analysis",
                subject="change/example",
                reviewed_scope="proposal",
                reviewer="human",
                verdict="accepted",
                artifacts=[artifact],
                timestamp=datetime(2026, 7, 21, tzinfo=timezone.utc),
            )

            content = receipt.read_text(encoding="utf-8")
            self.assertIn("- Gate: `internal`", content)
            self.assertNotIn("- Sender:", content)
            self.assertTrue(ARTIFACTS.receipt_is_current(project, receipt))
            artifact.write_text("v2\n", encoding="utf-8")
            self.assertFalse(ARTIFACTS.receipt_is_current(project, receipt))
            with self.assertRaisesRegex(ARTIFACTS.ContractError, "already exists"):
                ARTIFACTS.write_receipt(
                    project,
                    project / "usw/reviews",
                    receipt_id="review-1",
                    gate="internal",
                    owner_role="Analysis",
                    subject="change/example",
                    reviewed_scope="proposal",
                    reviewer="human",
                    verdict="accepted",
                    artifacts=[artifact],
                )

    def test_transition_and_task_model_fields_are_conditional(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            task = project / "task.md"
            task.write_text("legacy task\n", encoding="utf-8")
            contract_identity = "sha256:" + hashlib.sha256(task.read_bytes()).hexdigest()
            receipt = ARTIFACTS.write_receipt(
                project,
                project / "reviews",
                receipt_id="transition-1",
                gate="transition",
                owner_role="Testing",
                subject="task/example/1.1",
                reviewed_scope="task",
                reviewer="human",
                verdict="accepted",
                artifacts=[task],
                artifact_model="legacy",
                contract_identity=contract_identity,
                evidence_references=["python3 -m unittest: passed"],
                sender="Development",
                receiver="Testing",
            )
            content = receipt.read_text(encoding="utf-8")
            self.assertIn("- Sender: `Development`", content)
            self.assertNotIn("Product source identity", content)

            with self.assertRaisesRegex(ARTIFACTS.ContractError, "requires sender"):
                ARTIFACTS.write_receipt(
                    project,
                    project / "reviews",
                    receipt_id="bad-transition",
                    gate="transition",
                    owner_role="Testing",
                    subject="change/example",
                    reviewed_scope="change",
                    reviewer="human",
                    verdict="accepted",
                    artifacts=[task],
                )

    def test_receipt_rejects_empty_artifacts_invalid_fields_and_stale_task_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            with self.assertRaisesRegex(ARTIFACTS.ContractError, "reviewed artifacts"):
                ARTIFACTS.write_receipt(
                    project,
                    project / "reviews",
                    receipt_id="empty",
                    gate="internal",
                    owner_role="Analysis",
                    subject="change/example",
                    reviewed_scope="proposal",
                    reviewer="human",
                    verdict="accepted",
                    artifacts=[],
                )

            proposal = project / "proposal.md"
            proposal.write_text("proposal\n", encoding="utf-8")
            with self.assertRaisesRegex(ARTIFACTS.ContractError, "non-task"):
                ARTIFACTS.write_receipt(
                    project,
                    project / "reviews",
                    receipt_id="bad-fields",
                    gate="internal",
                    owner_role="Analysis",
                    subject="change/example",
                    reviewed_scope="proposal",
                    reviewer="human",
                    verdict="accepted",
                    artifacts=[proposal],
                    artifact_model="v1",
                    contract_identity="c1",
                    source_identity="usw-source-v1:" + "a" * 64,
                )

            task = project / "task.md"
            task.write_text(
                "## Contract revision\n\n- `c1`\n", encoding="utf-8"
            )
            evidence = project / "development-evidence.md"
            evidence.write_text(
                "| Evidence ID | Contract revision | Source identity | Check | Result | Timestamp |\n"
                "|---|---|---|---|---|---|\n"
                f"| dev-1 | `c1` | `{'usw-source-v1:' + 'a' * 64}` | `unit` | passed | now |\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ARTIFACTS.ContractError, "absent or stale"):
                ARTIFACTS.write_receipt(
                    project,
                    project / "reviews",
                    receipt_id="stale",
                    gate="transition",
                    owner_role="Testing",
                    subject="task/example/1.1",
                    reviewed_scope="task",
                    reviewer="human",
                    verdict="accepted",
                    artifacts=[task, evidence],
                    artifact_model="v1",
                    contract_identity="c1",
                    source_identity="usw-source-v1:" + "b" * 64,
                    evidence_references=["dev-1"],
                    sender="Development",
                    receiver="Testing",
                )

    def test_evidence_freshness_requires_both_current_identities(self):
        self.assertTrue(ARTIFACTS.evidence_is_current("c1", "s1", "c1", "s1"))
        self.assertFalse(ARTIFACTS.evidence_is_current("c0", "s1", "c1", "s1"))
        self.assertFalse(ARTIFACTS.evidence_is_current("c1", "s0", "c1", "s1"))


if __name__ == "__main__":
    unittest.main()
