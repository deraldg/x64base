from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import run_aif136_m5a_reconstruction as m5a


class Aif136M5AReconstructionTests(unittest.TestCase):
    def test_manifest_authorizes_proof_but_not_reclaim(self) -> None:
        manifest = m5a.load_and_validate_manifest(m5a.DEFAULT_MANIFEST)
        self.assertEqual(manifest["operation"], "isolated_reconstruction_proof_only")
        self.assertEqual(manifest["container_role"], "metadata_index_generator")
        self.assertTrue(manifest["container_must_persist"])
        self.assertEqual(manifest["expected_container_tag_count"], 3)
        self.assertEqual(len(manifest["expected_container_tags"]), 3)
        self.assertTrue(manifest["mdb_files_reconstructible"])
        self.assertTrue(manifest["lmdb_environment_directory_must_persist"])
        self.assertFalse(manifest["m5b_action_authorized"])

    def test_both_stages_reuse_the_preserved_cdx(self) -> None:
        common = {
            "dbf_dir": Path("D:/proof/dbf"),
            "index_dir": Path("D:/proof/indexes"),
            "lmdb_root": Path("D:/proof/lmdb"),
            "cdx_path": Path("D:/proof/indexes/OBJECTS.cdx"),
            "capture_path": Path("D:/proof/capture.txt"),
            "table": "OBJECTS",
            "tag": "OBJECT_ID",
        }
        stage1 = m5a.build_commands(stage=1, **common)
        stage2 = m5a.build_commands(stage=2, **common)
        self.assertFalse(any(line.startswith("CDX CREATE ") for line in stage1))
        self.assertFalse(any(line.startswith("CDX ADDTAG ") for line in stage1))
        self.assertTrue(any(line.startswith("SET INDEX TO ") for line in stage1))
        self.assertTrue(any(line.startswith("SET INDEX TO ") for line in stage2))

    def test_clear_removes_only_generated_files_and_preserves_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            env = Path(temp) / "OBJECTS.cdx.d"
            env.mkdir()
            for name in m5a.EXPECTED_ENV_FILES:
                (env / name).write_bytes(b"generated")
            m5a.clear_isolated_env_files(env)
            self.assertTrue(env.is_dir())
            self.assertEqual(list(env.iterdir()), [])

    def test_clear_refuses_unexpected_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            env = Path(temp) / "OBJECTS.cdx.d"
            env.mkdir()
            (env / "data.mdb").write_bytes(b"generated")
            (env / "lock.mdb").write_bytes(b"generated")
            (env / "keep.me").write_bytes(b"unexpected")
            with self.assertRaises(RuntimeError):
                m5a.clear_isolated_env_files(env)
            self.assertTrue((env / "keep.me").exists())

    def test_manifest_is_ascii_json(self) -> None:
        raw = m5a.DEFAULT_MANIFEST.read_bytes()
        raw.decode("ascii")
        self.assertEqual(json.loads(raw)["phase"], "M5-A")

    def test_capture_validator_uses_manifest_tag_count(self) -> None:
        manifest = m5a.load_and_validate_manifest(m5a.DEFAULT_MANIFEST)
        transcript = "\n".join(
            (
                "Opened DATA_DICTIONARY_OBJECTS (v64) : Record count 10",
                "Tags     : 3",
                "CATALOG_OBJECT_ID",
                "CATALOG_OBJECT_TYPE",
                "CATALOG_OBJECT_NAME",
                "BUILDLMDB: done OK=3 tags rebuilt.",
                "SET ORDER: CDX TAG 'CATALOG_OBJECT_ID' (ASC)",
                *manifest["expected_ordered_keys"],
                "10 cdx(lmdb) indexed record(s)",
            )
        )
        self.assertEqual(m5a.validate_capture(transcript, manifest, 1), [])

    def test_capture_normalization_removes_only_trailing_padding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            capture = Path(temp) / "capture.txt"
            capture.write_bytes(b"  kept leading   \r\nplain\t\r\n")
            normalized = m5a.normalize_capture(capture)
            self.assertEqual(normalized, "  kept leading\nplain\n")
            self.assertEqual(capture.read_bytes(), b"  kept leading\nplain\n")


if __name__ == "__main__":
    unittest.main()
