from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import run_aif136_m5b_restore_drill as m5b


class Aif136M5BRestoreDrillTests(unittest.TestCase):
    def test_manifest_records_completed_restore_and_reclaim_lifecycle(self) -> None:
        manifest = m5b.load_and_validate_manifest(m5b.DEFAULT_MANIFEST)
        self.assertEqual(manifest["restore_drill"]["ruling_state"], "approved")
        self.assertFalse(manifest["restore_drill"]["physical_reclaim_authorized"])
        self.assertEqual(manifest["restore_drill"]["status"], "PASS")
        self.assertTrue(manifest["m5b_action_authorized"])
        self.assertEqual(manifest["execution"]["status"], "PASS")
        self.assertTrue(manifest["directory_must_persist"])

    def test_dump_commands_read_the_timestamped_directory_directly(self) -> None:
        restored = Path("D:/proof/DATA_DICTIONARY_OBJECTS.cdx.d_20260529_111604")
        commands = m5b.dump_commands(
            restored_dir=restored,
            capture_path=Path("D:/proof/capture.txt"),
            tags=["ID", "TYPE", "NAME"],
        )
        dump_lines = [line for line in commands if line.startswith("LMDBDUMP ")]
        self.assertEqual(len(dump_lines), 4)
        self.assertTrue(all(str(restored) in line for line in dump_lines))

    def test_dump_validator_requires_all_tags_and_counts(self) -> None:
        manifest = m5b.load_and_validate_manifest(m5b.DEFAULT_MANIFEST)
        text = "\n".join(
            [
                *(f"DB '{tag}' exists (entries=10)" for tag in manifest["expected_container_tags"]),
                *("Scanned: 10 record(s)" for _ in manifest["expected_container_tags"]),
                *manifest["expected_ordered_keys"],
            ]
        )
        self.assertEqual(m5b.validate_dump_capture(text, manifest), [])
        self.assertTrue(m5b.validate_dump_capture(text.replace("DB 'CATALOG_OBJECT_NAME'", "DB 'MISSING'"), manifest))

    def test_cleanup_requires_exact_owned_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            allowed = Path(temp).resolve()
            workspace = allowed / "owned"
            workspace.mkdir()
            (workspace / ".aif136_m5b_owned.json").write_text(
                json.dumps({"run_id": "RUN-1"}) + "\n", encoding="ascii"
            )
            (workspace / "generated.bin").write_bytes(b"generated")
            m5b.remove_owned_workspace(workspace, allowed, "RUN-1")
            self.assertFalse(workspace.exists())

    def test_cleanup_refuses_foreign_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            allowed = Path(temp).resolve()
            workspace = allowed / "foreign"
            workspace.mkdir()
            (workspace / ".aif136_m5b_owned.json").write_text(
                json.dumps({"run_id": "OTHER"}) + "\n", encoding="ascii"
            )
            with self.assertRaises(RuntimeError):
                m5b.remove_owned_workspace(workspace, allowed, "RUN-1")
            self.assertTrue(workspace.exists())

    def test_manifest_is_ascii_json(self) -> None:
        raw = m5b.DEFAULT_MANIFEST.read_bytes()
        raw.decode("ascii")
        self.assertEqual(json.loads(raw)["phase"], "M5-B")


if __name__ == "__main__":
    unittest.main()
