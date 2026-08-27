from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import build_memory_storage_inventory as inventory_builder  # noqa: E402


class MemoryStorageInventoryTests(unittest.TestCase):
    def make_repo(self, root: Path) -> None:
        (root / ".git").mkdir()
        for relative in inventory_builder.BOOTSTRAP_PATHS + inventory_builder.FRONTAL_PATHS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(relative, encoding="utf-8")
        (root / "labtalk/ai_portal").mkdir(parents=True, exist_ok=True)
        (root / "labtalk/ai_portal/body.md").write_text("body", encoding="utf-8")
        (root / "docs/ai-friendly").mkdir(parents=True, exist_ok=True)
        (root / "docs/ai-friendly/rule.md").write_text("rule", encoding="utf-8")
        (root / "coordination/aif").mkdir(parents=True, exist_ok=True)
        (root / "coordination/aif/AIF-136.claim").write_text("aif: AIF-136\n", encoding="utf-8")
        lmdb = root / "docs/evidence/table.cdx.d"
        lmdb.mkdir(parents=True)
        (lmdb / "data.mdb").write_bytes(b"0123456789")
        for relative in inventory_builder.SUMMARY_ROOTS:
            (root / relative).mkdir(parents=True, exist_ok=True)

    def test_walk_skips_alias_before_descending(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            real = root / "real"
            alias = root / "alias"
            real.mkdir()
            alias.mkdir()
            (real / "kept.txt").write_text("keep", encoding="utf-8")
            (alias / "must_not_be_seen.txt").write_text("skip", encoding="utf-8")

            def detector(path: Path, _entry: object) -> bool:
                return path.name == "alias"

            files, skipped, errors = inventory_builder.walk_files(root, reparse_detector=detector)
            self.assertEqual(["kept.txt"], [item.name for item in files])
            self.assertEqual([str(alias).replace("\\", "/")], skipped)
            self.assertEqual([], errors)

    def test_large_file_hash_is_deferred_and_size_is_still_counted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            target = root / "docs/evidence/table.cdx.d/data.mdb"
            with patch.object(inventory_builder, "allocated_size", return_value=16):
                record, error = inventory_builder.make_record(
                    target,
                    repo_root=root,
                    collection="docs_lmdb",
                    tracked=set(),
                    ignored={"docs/evidence/table.cdx.d/data.mdb"},
                    hash_max_bytes=4,
                )
            self.assertIsNone(error)
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual("deferred_size_policy", record["hash_state"])
            self.assertIsNone(record["sha256"])
            self.assertEqual(10, record["logical_size_bytes"])
            self.assertEqual(16, record["allocated_size_bytes"])
            self.assertEqual("ignored", record["git_posture"])
            self.assertEqual("R4", record["storage_tier"])

    def test_small_file_is_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "small.md"
            path.write_text("small", encoding="utf-8")
            record, error = inventory_builder.make_record(
                path,
                repo_root=root,
                collection="portal_core",
                tracked={"small.md"},
                ignored=set(),
                hash_max_bytes=100,
            )
            self.assertIsNone(error)
            assert record is not None
            self.assertEqual("computed", record["hash_state"])
            self.assertEqual(64, len(record["sha256"]))
            self.assertEqual("tracked", record["git_posture"])

    def test_build_is_deterministic_with_fixed_observation_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            with patch.object(inventory_builder, "git_paths", return_value=(set(), set())), patch.object(
                inventory_builder, "allocated_size", return_value=None
            ):
                first = inventory_builder.build_inventory(
                    repo_root=root,
                    observed_at_utc="2026-08-26T00:00:00Z",
                    hash_max_bytes=4,
                    include_external=False,
                )
                second = inventory_builder.build_inventory(
                    repo_root=root,
                    observed_at_utc="2026-08-26T00:00:00Z",
                    hash_max_bytes=4,
                    include_external=False,
                )
            self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
            self.assertEqual(len(first["records"]), len({row["source_uri"] for row in first["records"]}))
            self.assertEqual(1, first["summary"]["docs_lmdb"]["records"])
            self.assertEqual(
                [{"logical_size_bytes": 10, "records": 1}],
                first["summary"]["docs_lmdb"]["size_distribution"],
            )
            hierarchy = {row["path"]: row for row in first["hierarchy"]}
            self.assertEqual(1, hierarchy["docs/ai-friendly"]["direct_documents"])

    def test_markdown_states_non_destructive_boundary(self) -> None:
        inventory = {
            "generated_at_utc": "2026-08-26T00:00:00Z",
            "summary": {
                "records": 0,
                "logical_size_bytes": 0,
                "allocated_size_bytes_known": 0,
                "allocated_size_known_records": 0,
                "hashes_computed": 0,
                "hashes_deferred": 0,
                "reparse_points_skipped": 0,
                "findings": 0,
                "by_storage_tier": {},
                "docs_lmdb": {
                    "records": 0,
                    "logical_size_bytes": 0,
                    "allocated_size_bytes_known": 0,
                    "size_distribution": [],
                    "by_docs_area": {},
                },
            },
            "collections": [],
            "hierarchy": [],
            "records": [],
            "findings": [],
        }
        markdown = inventory_builder.render_markdown(inventory)
        self.assertIn("does not approve a move, archive, deletion", markdown)
        self.assertIn("Database payloads were measured as files and were not opened", markdown)

    def test_schema_requires_every_record_field_emitted_by_builder(self) -> None:
        schema_path = Path(inventory_builder.DEFAULT_SCHEMA)
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        required = set(schema["properties"]["records"]["items"]["required"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "sample.md"
            path.write_text("sample", encoding="utf-8")
            record, error = inventory_builder.make_record(
                path,
                repo_root=root,
                collection="portal_core",
                tracked=set(),
                ignored=set(),
                hash_max_bytes=100,
            )
        self.assertIsNone(error)
        assert record is not None
        self.assertEqual(required, set(record))

    def test_contract_validator_fails_duplicate_and_unknown_tier(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            with patch.object(inventory_builder, "git_paths", return_value=(set(), set())), patch.object(
                inventory_builder, "allocated_size", return_value=None
            ):
                inventory = inventory_builder.build_inventory(
                    repo_root=root,
                    observed_at_utc="2026-08-26T00:00:00Z",
                    hash_max_bytes=4,
                    include_external=False,
                )
            duplicate = dict(inventory["records"][0])
            duplicate["storage_tier"] = "HOT"
            inventory["records"].append(duplicate)
            inventory["summary"]["records"] += 1
            findings = inventory_builder.validate_inventory(inventory)
            self.assertIn("unsupported value: HOT", "\n".join(findings))
            self.assertIn("duplicate memory_id", "\n".join(findings))
            self.assertIn("duplicate source_uri", "\n".join(findings))

    def test_check_reuses_prior_observation_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            output_json = root / "inventory.json"
            output_markdown = root / "inventory.md"
            fixed = "2026-08-26T00:00:00Z"
            with patch.object(inventory_builder, "git_paths", return_value=(set(), set())), patch.object(
                inventory_builder, "allocated_size", return_value=None
            ):
                self.assertEqual(
                    0,
                    inventory_builder.main(
                        [
                            "--repo-root", str(root), "--out-json", str(output_json),
                            "--out-markdown", str(output_markdown), "--observed-at", fixed,
                            "--no-external", "--hash-max-bytes", "4",
                        ]
                    ),
                )
                self.assertEqual(
                    0,
                    inventory_builder.main(
                        [
                            "--repo-root", str(root), "--out-json", str(output_json),
                            "--out-markdown", str(output_markdown), "--no-external",
                            "--hash-max-bytes", "4", "--check",
                        ]
                    ),
                )


if __name__ == "__main__":
    unittest.main()
