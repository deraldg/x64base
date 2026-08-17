"""Focused tests for the local AI Portal maintenance surface."""
from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest import mock

import yaml


MODULE_PATH = Path(__file__).resolve().parents[1] / "maint_server.py"
SPEC = importlib.util.spec_from_file_location("maint_server_under_test", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class MaintenanceConsoleTests(unittest.TestCase):
    def test_render_page_uses_operational_dashboard_and_injected_posture(self):
        page = MODULE.render_page("/AI/console/api", write_enabled=False)
        self.assertIn("AI Portal Maintenance", page)
        self.assertIn("Development truth vs production snapshot inputs", page)
        self.assertIn("Filter visible rows", page)
        self.assertIn("Export CSV", page)
        self.assertIn('const API = "/AI/console/api"', page)
        self.assertIn("const WRITE = (false)", page)
        self.assertIn('const WRITE_TOKEN = ""', page)
        self.assertIn("Preview as DotScript (safe default)", page)
        self.assertIn("const generation = ++state.loadGeneration", page)
        self.assertIn("requestedTable !== state.cur", page)

    def test_render_page_injects_write_session_token(self):
        page = MODULE.render_page("/api", write_enabled=True, write_token="test-token")
        self.assertIn('const WRITE_TOKEN = "test-token"', page)
        self.assertNotIn("__WRITE_TOKEN__", page)

    def test_execute_requires_explicit_single_writer_acknowledgement(self):
        with self.assertRaisesRegex(MODULE.crud.CrudError, "explicit acknowledgement"):
            MODULE._do_op(
                {
                    "op": "create",
                    "table": "SYSLANE",
                    "mode": "execute",
                    "set": {"LKEY": "AIF-TEST"},
                },
                write_enabled=True,
            )

    def test_unknown_mode_fails_closed_before_writer_open(self):
        with mock.patch.object(MODULE.crud, "_open_real_area") as open_area:
            with self.assertRaisesRegex(MODULE.crud.CrudError, "unknown mode"):
                MODULE._do_op(
                    {
                        "op": "create",
                        "table": "SYSLANE",
                        "mode": "typo",
                        "set": {"LKEY": "AIF-TEST"},
                        "ack_execute": True,
                    },
                    write_enabled=True,
                )
        open_area.assert_not_called()

    def test_http_write_boundary_requires_json_loopback_and_session_token(self):
        headers = Message()
        headers["Content-Type"] = "text/plain"
        headers["Host"] = "127.0.0.1:8770"
        with self.assertRaisesRegex(MODULE.crud.CrudError, "Content-Type"):
            MODULE.require_local_json(headers, "secret")

        headers.replace_header("Content-Type", "application/json")
        headers["Origin"] = "https://example.invalid"
        with self.assertRaisesRegex(MODULE.crud.CrudError, "Origin"):
            MODULE.require_local_json(headers, "secret")

        headers.replace_header("Origin", "http://localhost:8770")
        headers["X-DotTalk-Maint-Token"] = "wrong"
        with self.assertRaisesRegex(MODULE.crud.CrudError, "session token"):
            MODULE.require_local_json(headers, "secret")

        headers.replace_header("X-DotTalk-Maint-Token", "secret")
        MODULE.require_local_json(headers, "secret")

    def test_write_server_rejects_non_loopback_bind(self):
        with mock.patch.object(MODULE.sys, "stderr", io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                MODULE.main(["--host", "0.0.0.0"])
        self.assertEqual(stopped.exception.code, 2)

    def test_purge_requires_exact_typed_token_even_for_preview(self):
        body = {
            "op": "delete",
            "table": "SYSLANE",
            "mode": "dts",
            "key": "AIF-TEST",
            "purge": True,
        }
        with self.assertRaisesRegex(MODULE.crud.CrudError, "PURGE SYSLANE"):
            MODULE._do_op(body, write_enabled=False)
        body["confirm"] = "PURGE SYSLANE"
        result = MODULE._do_op(body, write_enabled=False)
        self.assertTrue(result["ok"])
        self.assertIn("DELETE", result["dotscript"])

    def test_execute_refuses_stale_row_version_before_opening_writer(self):
        current = {"LKEY": "AIF-TEST", "ROWVER": "4"}
        body = {
            "op": "update",
            "table": "SYSLANE",
            "mode": "execute",
            "key": "AIF-TEST",
            "set": {"TITLE": "new title"},
            "ack_execute": True,
            "expected_rowver": "3",
        }
        with mock.patch.object(MODULE.crud, "read_rows", return_value=[current]), \
             mock.patch.object(MODULE.crud, "_open_real_area") as open_area:
            with self.assertRaisesRegex(MODULE.crud.CrudError, "stale row version"):
                MODULE._do_op(body, write_enabled=True)
        open_area.assert_not_called()

    def test_table_payload_includes_typed_field_metadata(self):
        with mock.patch.object(MODULE.crud, "read_rows", return_value=[]):
            payload = MODULE._table_payload("SYSLANE", include_deleted=False)
        fields = {field["name"]: field for field in payload["fields"]}
        self.assertEqual(fields["LKEY"], {"name": "LKEY", "type": "C", "width": 16})
        self.assertEqual(fields["ROWVER"]["type"], "N")

    def test_tables_payload_reports_actual_execute_posture(self):
        summary = {
            "name": "SYSLANE", "subdir": "portal", "writable": True,
            "close": "status", "append_only": False, "pk": "ID", "key": "LKEY",
            "ckey": [], "field_count": 1, "exists": True, "modified_at": "",
            "count": 3, "live": 2, "error": "",
        }
        health = {"ok": True, "items": [], "pending_total": 0}
        with mock.patch.object(MODULE, "_table_summary", return_value=summary), \
             mock.patch.object(MODULE, "_registry_health", return_value=health):
            payload = MODULE._tables_payload(Path("repo"), write_enabled=False)
        self.assertFalse(payload["posture"]["execute_enabled"])
        self.assertEqual(payload["posture"]["default_mode"], "dts")
        self.assertEqual(payload["registry_health"], health)

    def test_registry_health_exposes_live_vs_snapshot_lag_without_writing_flat(self):
        with tempfile.TemporaryDirectory(prefix="maint-health-") as temporary:
            root = Path(temporary)
            registries = root / "labtalk" / "registries"
            for name in ("runs.d", "proofs.d", "lessons.d"):
                (registries / name).mkdir(parents=True, exist_ok=True)

            def write_yaml(path: Path, value) -> None:
                path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")

            write_yaml(
                registries / "ai_runs.yaml",
                {"runs_registry": {}, "runs": [{"run_id": "RUN-1", "lanes": ["AIF-001"]}],
                 "current_by_lane": {"AIF-001": "RUN-1"}},
            )
            write_yaml(registries / "runs.d" / "_header.yaml", {"runs_registry": {}})
            write_yaml(registries / "runs.d" / "RUN-1.yaml", {"run_id": "RUN-1", "lanes": ["AIF-001"], "started": "2026-08-15"})
            write_yaml(registries / "runs.d" / "RUN-2.yaml", {"run_id": "RUN-2", "lanes": ["AIF-086"], "started": "2026-08-16"})

            write_yaml(registries / "proofs.yaml", {"proof_states": {}, "proofs": [{"id": "proof.one"}]})
            write_yaml(registries / "proofs.d" / "_header.yaml", {"proof_states": {}})
            write_yaml(registries / "proofs.d" / "proof.one.yaml", {"id": "proof.one"})

            write_yaml(registries / "lessons.yaml", {"schema": {}, "lessons": [{"id": "lesson.one"}]})
            write_yaml(registries / "lessons.d" / "_header.yaml", {"schema": {}})
            write_yaml(registries / "lessons.d" / "lesson.one.yaml", {"id": "lesson.one"})

            flat = registries / "ai_runs.yaml"
            before = (flat.read_bytes(), flat.stat().st_mtime_ns)
            health = MODULE._registry_health(root)
            after = (flat.read_bytes(), flat.stat().st_mtime_ns)

        self.assertTrue(health["ok"], health)
        runs = next(item for item in health["items"] if item["name"] == "ai_runs.yaml")
        self.assertEqual(runs["live_count"], 2)
        self.assertEqual(runs["snapshot_count"], 1)
        self.assertEqual(runs["new_ids"], ["RUN-2"])
        self.assertEqual(runs["changed_ids"], ["RUN-1"])
        self.assertEqual(runs["pending_ids"], ["RUN-1", "RUN-2"])
        self.assertEqual(runs["live_lane_count"], 2)
        self.assertEqual(before, after)

    def test_deleted_rows_are_view_only_in_the_dashboard(self):
        page = MODULE.render_page("/api", write_enabled=True, write_token="test")
        self.assertIn(
            "const actionable = row._live && !row._deleted && spec.writable",
            page,
        )

    def test_table_payload_preserves_tombstone_identity_and_marks_it_not_live(self):
        tombstone = {
            "ID": "9",
            "LKEY": "AIF-OLD",
            "STATUS": "1",
            "_deleted": True,
            "_recno": 14,
        }
        with mock.patch.object(MODULE.crud, "read_rows", return_value=[tombstone]) as read:
            payload = MODULE._table_payload("SYSLANE", include_deleted=True)
        read.assert_called_once_with(
            "SYSLANE",
            include_deleted=True,
            include_metadata=True,
        )
        self.assertFalse(payload["rows"][0]["_live"])
        self.assertTrue(payload["rows"][0]["_deleted"])
        self.assertEqual(payload["rows"][0]["_recno"], 14)


if __name__ == "__main__":
    unittest.main()
