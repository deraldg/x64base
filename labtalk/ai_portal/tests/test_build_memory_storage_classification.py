from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import build_memory_storage_classification as classifier  # noqa: E402


def record(
    memory_id: str,
    source_uri: str,
    *,
    collection: str = "portal_core",
    kind: str = "documentation",
    digest: str | None = None,
    hash_state: str = "deferred_size_policy",
) -> dict[str, object]:
    return {
        "memory_id": memory_id,
        "source_uri": source_uri,
        "collection": collection,
        "artifact_kind": kind,
        "sha256": digest,
        "hash_state": hash_state,
        "logical_size_bytes": 12,
        "sensitivity": "development_only",
    }


def inventory(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "dottalk.portal.memory-inventory.v1",
        "generated_at_utc": "2026-08-26T00:00:00Z",
        "records": records,
    }


class MemoryStorageClassificationTests(unittest.TestCase):
    def test_exact_duplicates_require_computed_hash(self) -> None:
        digest = "a" * 64
        rows = [
            record("memory.file." + "1" * 20, "docs/a.md", digest=digest, hash_state="computed"),
            record("memory.file." + "2" * 20, "docs/b.md", digest=digest, hash_state="computed"),
            record("memory.file." + "3" * 20, "docs/c.md"),
            record("memory.file." + "4" * 20, "docs/d.md"),
        ]
        groups = classifier.exact_duplicate_groups(rows)
        self.assertEqual(1, len(groups))
        self.assertEqual(2, len(groups[0]["memory_ids"]))

    def test_version_family_is_same_directory_and_requires_version_token(self) -> None:
        rows = [
            record("memory.file." + "1" * 20, "docs/lane/REPORT_V1.md"),
            record("memory.file." + "2" * 20, "docs/lane/REPORT_V2.md"),
            record("memory.file." + "3" * 20, "docs/other/REPORT_V3.md"),
            record("memory.file." + "4" * 20, "docs/lane/REPORT.md"),
        ]
        groups = classifier.version_family_groups(rows)
        self.assertEqual(1, len(groups))
        self.assertEqual(2, len(groups[0]["memory_ids"]))

    def test_lmdb_expected_names_strip_archive_timestamp(self) -> None:
        self.assertEqual(
            ("table.cdx", "table.dbf"),
            classifier.lmdb_expected_names("docs/lane/table.cdx.d_20260826_120101/data.mdb"),
        )
        self.assertEqual((None, None), classifier.lmdb_expected_names("docs/lane/random/data.mdb"))

    def test_recovery_postures_are_candidate_only(self) -> None:
        target = record(
            "memory.file." + "1" * 20,
            "docs/lane/table.cdx.d/data.mdb",
            collection="docs_lmdb",
            kind="database_derived",
        )
        both = classifier.recovery_for(
            target,
            {"table.cdx": ["docs/lane/table.cdx"], "table.dbf": ["docs/lane/table.dbf"]},
        )
        self.assertEqual("candidate_inputs_found", both["posture"])
        self.assertEqual("unverified", both["state"])
        only_container = classifier.recovery_for(target, {"table.cdx": ["docs/lane/table.cdx"]})
        self.assertEqual("container_candidate_only", only_container["posture"])
        none = classifier.recovery_for(target, {})
        self.assertEqual("inputs_not_found", none["posture"])

    def test_candidate_ranking_prefers_nearest_path(self) -> None:
        ranked = classifier.rank_candidates(
            "docs/lane/archive/table.cdx.d/data.mdb",
            ["docs/other/table.cdx", "docs/lane/table.cdx", "docs/lane/archive/table.cdx"],
        )
        self.assertEqual("docs/lane/archive/table.cdx", ranked[0])

    def test_unknown_authority_is_quarantined_without_move(self) -> None:
        authority, tier, sensitivity, _reason = classifier.classify_record(
            record(
                "memory.file." + "1" * 20,
                "D:/code/Frontal_Mem/private.md",
                collection="frontal_mem_external",
            )
        )
        self.assertEqual(("unknown", "Q5", "private"), (authority, tier, sensitivity))

    def test_build_is_deterministic_and_preserves_inventory_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            body = inventory([
                record("memory.file." + "1" * 20, "labtalk/ai_portal/body.md"),
            ])
            first = classifier.build_classification(body, repo_root=root)
            second = classifier.build_classification(body, repo_root=root)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(body["generated_at_utc"], first["generated_at_utc"])
        self.assertEqual("none_authorized", first["classifications"][0]["physical_action"])

    def test_contract_rejects_duplicate_invalid_and_unknown_outside_q5(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            body = classifier.build_classification(
                inventory([record("memory.file." + "1" * 20, "unknown/item.bin", collection="other")]),
                repo_root=root,
            )
        duplicate = dict(body["classifications"][0])
        duplicate["proposed_storage_tier"] = "HOT"
        body["classifications"].append(duplicate)
        body["summary"]["records"] += 1
        findings = "\n".join(classifier.validate_classification(body))
        self.assertIn("unsupported value: HOT", findings)
        self.assertIn("duplicate memory_id", findings)
        self.assertIn("unknown authority must remain Q5", findings)

    def test_contract_rejects_dangling_lineage_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            body = classifier.build_classification(
                inventory([record("memory.file." + "1" * 20, "labtalk/ai_portal/body.md")]),
                repo_root=root,
            )
        body["classifications"][0]["exact_duplicate_group_id"] = "duplicate." + "a" * 16
        findings = "\n".join(classifier.validate_classification(body))
        self.assertIn("dangling or inconsistent group reference", findings)

    def test_markdown_states_non_destructive_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            report = classifier.build_classification(inventory([]), repo_root=root)
        markdown = classifier.render_markdown(report)
        self.assertIn("does not declare a document superseded", markdown)
        self.assertIn("No physical action is authorized", markdown)

    def test_approved_pilot_changes_only_exact_ids_to_owner_confirmed_c3(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            first_id = "memory.file." + "1" * 20
            second_id = "memory.file." + "2" * 20
            body = inventory([
                record(first_id, "labtalk/ai_portal/history.md"),
                record(second_id, "labtalk/ai_portal/current.md"),
            ])
            pilot = {
                "ruling_state": "approved",
                "operation": "cognitive_demotion_only",
                "physical_action": "none_authorized",
                "items": [{
                    "memory_id": first_id,
                    "source_uri": "labtalk/ai_portal/history.md",
                    "current_tier": "W2",
                    "proposed_tier": "C3",
                    "physical_move": False,
                    "source_deletion": False,
                    "reason": "Owner-approved history pilot.",
                }],
            }
            result = classifier.build_classification(body, repo_root=root, pilot_manifest=pilot)
        rows = {item["memory_id"]: item for item in result["classifications"]}
        self.assertEqual(("C3", "owner_confirmed"), (
            rows[first_id]["proposed_storage_tier"], rows[first_id]["classification_state"],
        ))
        self.assertEqual("W2", rows[second_id]["proposed_storage_tier"])
        self.assertEqual(1, result["summary"]["owner_confirmed_records"])


if __name__ == "__main__":
    unittest.main()
