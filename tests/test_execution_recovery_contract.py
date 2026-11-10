import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = (ROOT / "openspec/specs/execution-artifacts/spec.md").read_text(encoding="utf-8")
LIVE = (ROOT / "openspec/specs/live-operation-state/spec.md").read_text(encoding="utf-8")


def block(text, heading, next_heading):
    match = re.search(rf"^{re.escape(heading)}\n(.*?)(?=^{next_heading}|\Z)", text, re.M | re.S)
    if not match:
        raise AssertionError(f"Missing heading: {heading}")
    return match.group(1)


class ExecutionRecoveryContractTests(unittest.TestCase):
    def test_pause_owner_and_router(self):
        owner = block(SPEC, "### Requirement: Один владелец для каждого вида состояния исполнения", r"### Requirement:")
        pause = block(owner, "#### Scenario: Работа приостанавливается", r"#### Scenario:")
        for token in ("`live-operation-state`", "`.usw/HANDOFF.md`", "router", "`.usw/handoffs/<operation-hex>.md`"):
            self.assertIn(token, owner)
        for token in ("operation document", "HANDOFF", "router", "shared task artifacts"):
            self.assertIn(token, pause)
        for token in ("`tasks.md`", "`task.md`", "`development-evidence.md`", "`testing-evidence.md`", "review receipts"):
            self.assertIn(token, owner)

    def test_generic_handoff_keeps_local_operation_context(self):
        generic = block(SPEC, "### Requirement: Generic handoff не требует artifact roles", r"### Requirement:")
        for token in ("`live-operation-state`", "router", "operation document", "developer-local", "typed subject", "write authority", "shared evidence", "review receipts"):
            self.assertIn(token, generic)

    def test_replanning_uses_operation_document_and_preserves_facts(self):
        replanning = block(SPEC, "### Requirement: Replanning сохраняет факты без отдельного plan artifact", r"### Requirement:")
        for token in ("`live-operation-state`", "operation document", "HANDOFF", "router", "Milestone log", "evidence", "receipts", "contract revision", "freshness evidence"):
            self.assertIn(token, replanning)
        self.assertNotIn("`.usw/HANDOFF.md`, но MUST сохранять", replanning)

    def test_live_operation_spec_anchors_authority(self):
        live = block(LIVE, "### Requirement: Generic handoff маршрутизирует text operations", r"### Requirement:")
        for token in ("`.usw/HANDOFF.md`", "router", "operation document", "authoritative", "recovery content"):
            self.assertIn(token, live)


if __name__ == "__main__":
    unittest.main()
