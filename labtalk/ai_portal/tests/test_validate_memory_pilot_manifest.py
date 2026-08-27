from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import validate_memory_pilot_manifest as validator  # noqa: E402


class MemoryPilotManifestTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[dict[str, object], dict[str, object]]:
        source = root / "labtalk/ai_portal/history.md"
        source.parent.mkdir(parents=True)
        source.write_text("historical body", encoding="utf-8")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        memory_id = "memory.file." + "1" * 20
        item = {
            "memory_id": memory_id,
            "source_uri": "labtalk/ai_portal/history.md",
            "stored_uri": "labtalk/ai_portal/history.md",
            "expected_sha256": digest,
            "expected_size_bytes": source.stat().st_size,
            "current_tier": "W2",
            "proposed_tier": "C3",
            "authority_class": "reviewed_derivative",
            "sensitivity": "development_only",
            "reason": "Dated history.",
            "portal_summary": "Historical review.",
            "lineage_note": "No supersession declared.",
            "physical_move": False,
            "source_deletion": False,
        }
        manifest = {
            "schema": validator.SCHEMA_ID,
            "manifest_id": "AIF136-M3-PILOT-999",
            "lane_id": "AIF-136",
            "phase": "M3",
            "ruling_state": "awaiting_owner_ruling",
            "operation": "cognitive_demotion_only",
            "physical_action": "none_authorized",
            "source_inventory": "inventory.json",
            "source_classification": "classification.json",
            "proposed_store": "in_place_git_tracked_cold_body",
            "retrieval_trigger": "trigger.portal_history",
            "items": [item],
            "rollback": {"method": "Remove metadata.", "data_restore_required": False},
            "exclusions": ["physical mutation"],
            "owner_ruling": {
                "owner": "member.derald", "decision": None,
                "decided_at_utc": None, "recorded_in": "packet.md",
            },
        }
        inventory = {
            "records": [{
                "memory_id": memory_id,
                "source_uri": item["source_uri"],
                "sha256": digest,
                "hash_state": "computed",
                "logical_size_bytes": item["expected_size_bytes"],
            }]
        }
        return manifest, inventory

    def test_valid_awaiting_manifest_passes_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, inventory = self.fixture(root)
            self.assertEqual([], validator.validate_manifest(manifest, inventory, repo_root=root))

    def test_hash_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, inventory = self.fixture(root)
            manifest["items"][0]["expected_sha256"] = "a" * 64
            findings = "\n".join(validator.validate_manifest(manifest, inventory, repo_root=root))
            self.assertIn("does not match the M1 inventory", findings)
            self.assertIn("live hash does not match", findings)

    def test_physical_mutation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, inventory = self.fixture(root)
            manifest["items"][0]["source_deletion"] = True
            findings = "\n".join(validator.validate_manifest(manifest, inventory, repo_root=root))
            self.assertIn("cannot authorize physical mutation", findings)

    def test_approval_requires_owner_decision_and_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, inventory = self.fixture(root)
            manifest["ruling_state"] = "approved"
            findings = "\n".join(validator.validate_manifest(manifest, inventory, repo_root=root))
            self.assertIn("explicit owner decision and timestamp", findings)

    def test_duplicate_item_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, inventory = self.fixture(root)
            manifest["items"].append(copy.deepcopy(manifest["items"][0]))
            findings = "\n".join(validator.validate_manifest(manifest, inventory, repo_root=root))
            self.assertIn("duplicate memory_id", findings)
            self.assertIn("duplicate source_uri", findings)


if __name__ == "__main__":
    unittest.main()
