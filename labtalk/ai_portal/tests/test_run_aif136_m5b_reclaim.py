from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import run_aif136_m5b_reclaim as reclaim


class Aif136M5BReclaimTests(unittest.TestCase):
    def test_manifest_authorizes_exact_reclaim(self) -> None:
        manifest = reclaim.load_and_validate_manifest(reclaim.DEFAULT_MANIFEST)
        self.assertTrue(manifest["m5b_action_authorized"])
        self.assertEqual(manifest["owner_ruling"]["decision"], "approved")
        self.assertEqual({Path(row["path"]).name for row in manifest["delete_files"]}, reclaim.EXPECTED_FILES)
        self.assertEqual(sum(row["size_bytes"] for row in manifest["delete_files"]), 16384)

    def test_restore_proof_is_valid(self) -> None:
        manifest = reclaim.load_and_validate_manifest(reclaim.DEFAULT_MANIFEST)
        proof = reclaim.validate_restore_proof(manifest)
        self.assertEqual(proof["status"], "PASS")
        self.assertTrue(proof["restored_files_match_standard_environment"])

    def test_rollback_restores_quarantined_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.mdb"
            destination = root / "quarantine.mdb"
            source.write_bytes(b"payload")
            source.replace(destination)
            reclaim.rollback_moves([(source, destination)])
            self.assertEqual(source.read_bytes(), b"payload")
            self.assertFalse(destination.exists())

    def test_finalize_quarantine_deletes_only_exact_payload(self) -> None:
        with tempfile.TemporaryDirectory(dir=reclaim.REPO_ROOT / "tmp") as temp:
            allowed = (reclaim.REPO_ROOT / "tmp/aif136_m5b_reclaim").resolve()
            allowed.mkdir(parents=True, exist_ok=True)
            workspace = allowed / ("test-" + Path(temp).name)
            payload = workspace / "payload"
            payload.mkdir(parents=True)
            for name in reclaim.EXPECTED_FILES:
                (payload / name).write_bytes(b"generated")
            (workspace / ".aif136_m5b_owned.json").write_text(
                json.dumps({"run_id": "RUN-1"}) + "\n", encoding="ascii"
            )
            reclaim.finalize_quarantine(workspace, payload, "RUN-1")
            self.assertFalse(workspace.exists())

    def test_finalize_refuses_unexpected_quarantine_content(self) -> None:
        allowed = (reclaim.REPO_ROOT / "tmp/aif136_m5b_reclaim").resolve()
        allowed.mkdir(parents=True, exist_ok=True)
        workspace = allowed / "test-unexpected"
        if workspace.exists():
            self.fail("test workspace unexpectedly exists")
        payload = workspace / "payload"
        payload.mkdir(parents=True)
        try:
            for name in reclaim.EXPECTED_FILES:
                (payload / name).write_bytes(b"generated")
            (payload / "extra.bin").write_bytes(b"unexpected")
            (workspace / ".aif136_m5b_owned.json").write_text(
                json.dumps({"run_id": "RUN-1"}) + "\n", encoding="ascii"
            )
            with self.assertRaises(RuntimeError):
                reclaim.finalize_quarantine(workspace, payload, "RUN-1")
            self.assertTrue((payload / "extra.bin").exists())
        finally:
            for child in payload.iterdir():
                child.unlink()
            payload.rmdir()
            (workspace / ".aif136_m5b_owned.json").unlink()
            workspace.rmdir()


if __name__ == "__main__":
    unittest.main()
