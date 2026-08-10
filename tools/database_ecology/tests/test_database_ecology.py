from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from database_ecology import (  # noqa: E402
    SQLITE_HEADER,
    cascade_duplicate_state,
    scan_roots,
    sha256,
    sidecar_rows,
    verify_sidecar_plan,
    write_csv,
)


class DatabaseEcologyTests(unittest.TestCase):
    def test_scan_detects_carriers_companions_and_integrity_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "table.dbf").write_bytes(b"dbf")
            (root / "table.dbt").write_bytes(b"memo")
            (root / "orphan.fpt").write_bytes(b"memo")
            (root / "table.ddl.json").write_text("{}", encoding="utf-8")
            (root / "stray.load.json").write_text("{}", encoding="utf-8")
            (root / "index.cdx").write_bytes(b"cdx")
            (root / "index.cnx").write_bytes(b"cnx")
            (root / "sample.sqlite").write_bytes(SQLITE_HEADER + b"payload")
            environment = root / "sample.cdx.d"
            environment.mkdir()
            (environment / "data.mdb").write_bytes(b"data")
            (environment / "lock.mdb").write_bytes(b"lock")
            broken = root / "broken.cdx.d"
            broken.mkdir()
            (broken / "data.mdb").write_bytes(b"data")

            scan = scan_roots(root, [root])
            primary = scan["physical_census"]["primary_stores"]
            self.assertEqual(primary["dbf_tables"], 1)
            self.assertEqual(primary["lmdb_environments"], 1)
            self.assertEqual(primary["sqlite_files_by_signature"], 1)
            self.assertEqual(primary["dbf_content_distinct_sha256"], 1)
            integrity = scan["integrity_findings"]
            self.assertEqual(len(integrity["memo_companions_without_colocated_dbf"]), 1)
            self.assertEqual(len(integrity["generated_sidecars_without_colocated_dbf"]), 1)
            self.assertEqual(len(integrity["lmdb_data_without_lock_peer"]), 1)
            self.assertEqual(len(integrity["lmdb_lock_without_data_peer"]), 0)

    def test_cascade_duplicate_state_distinguishes_exact_and_timestamp_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy = root / "dottalkpp/data/dbf"
            # System-bundle layout (owner ruling 2026-08-10): canonical DBFs
            # live under systems/cascade_erp/dbf, JSON sidecars under
            # systems/cascade_erp/meta.
            system = root / "dottalkpp/data/systems/cascade_erp"
            (system / "dbf").mkdir(parents=True)
            (system / "meta").mkdir(parents=True)
            legacy.mkdir(parents=True, exist_ok=True)
            (legacy / "CASCADE_A.dbf").write_bytes(b"same")
            (system / "dbf" / "CASCADE_A.dbf").write_bytes(b"same")
            (legacy / "CASCADE_A.load.json").write_text(
                json.dumps({"rows": 3, "finished": "old"}), encoding="utf-8"
            )
            (system / "meta" / "CASCADE_A.load.json").write_text(
                json.dumps({"rows": 3, "finished": "new"}), encoding="utf-8"
            )
            state = cascade_duplicate_state(root)
            self.assertEqual(state["legacy_root_artifacts"], 2)
            self.assertEqual(state["paired_with_canonical"], 2)
            self.assertEqual(state["byte_equal"], 1)
            self.assertEqual(state["load_timestamp_equivalent"], 1)
            self.assertEqual(state["divergent"], [])

    def test_sidecar_plan_is_hash_bound_and_does_not_move_source(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML not installed")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidate = root / "data/orphan.bin"
            candidate.parent.mkdir(parents=True)
            candidate.write_bytes(b"candidate")
            canonical = root / "data/cascade_erp"
            canonical.mkdir()
            (canonical / "keep.bin").write_bytes(b"canonical")
            glob_candidate = root / "data/CASCADE_A.bin"
            glob_candidate.write_bytes(b"legacy")
            registry = root / "registry.yaml"
            registry.write_text(
                "database_ecology:\n"
                "  orphan_review_queue:\n"
                "    - id: orphan.test\n"
                "      path: data/orphan.bin\n"
                "      classification: probe_residue\n"
                "      disposition: review_then_sidecar\n"
                "    - id: orphan.glob\n"
                "      path_glob: data/CASCADE_*\n"
                "      classification: duplicate_generated_output\n"
                "      disposition: review_then_sidecar\n",
                encoding="utf-8",
            )
            rows = sidecar_rows(root, registry, "BATCH-1", root / "sidecar")
            self.assertEqual(len(rows), 2)
            by_source = {row["SOURCE_RELATIVE"]: row for row in rows}
            self.assertEqual(by_source["data/orphan.bin"]["SOURCE_SHA256"], sha256(candidate))
            self.assertEqual(by_source["data/orphan.bin"]["REVIEW_STATE"], "candidate_not_approved")
            self.assertNotIn("data/cascade_erp/keep.bin", by_source)
            self.assertTrue(candidate.exists())
            output = root / "plan.csv"
            write_csv(rows, output)
            with output.open(encoding="utf-8", newline="") as handle:
                loaded = list(csv.DictReader(handle))
            self.assertEqual(len(loaded), 2)
            self.assertEqual(verify_sidecar_plan(root, output), [])
            candidate.write_bytes(b"changed")
            self.assertIn("source hash drift", "\n".join(verify_sidecar_plan(root, output)))
            self.assertTrue(candidate.exists())


if __name__ == "__main__":
    unittest.main()
