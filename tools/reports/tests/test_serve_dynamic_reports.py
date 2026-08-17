import importlib.util
import io
import threading
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "serve_dynamic_reports.py"
SPEC = importlib.util.spec_from_file_location("serve_dynamic_reports", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ReportRouteTests(unittest.TestCase):
    def test_report_routes_keep_existing_urls(self):
        cases = {
            "/AI": "index.html",
            "/AI/": "index.html",
            "/AI/AI_PORTAL_REPORT.html": "AI_PORTAL_REPORT.html",
            "/reports": "index.html",
            "/reports/": "index.html",
            "/reports/index.html?v=local-preview": "index.html",
            "/reports/AI_PORTAL_REPORT.html": "AI_PORTAL_REPORT.html",
            "/reports/AI_PORTAL_REPORT/": "AI_PORTAL_REPORT.html",
            "/reports/BBS_BOARDS_REPORT.html": "BBS_BOARDS_REPORT.html",
            "/reports/BBS_ACCESS_REPORT/": "BBS_ACCESS_REPORT.html",
            "/reports/AIF_RULINGS_REPORT.html": "AIF_RULINGS_REPORT.html",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(MODULE.report_name_for_path(path), expected)

    def test_non_report_and_unknown_report_routes_are_not_aliases(self):
        self.assertIsNone(MODULE.report_name_for_path("/products/labtalk/"))
        self.assertIsNone(MODULE.report_name_for_path("/reports/not-a-report.html"))
        self.assertIsNone(MODULE.report_name_for_path("/AI/console"))

    def test_live_response_is_visibly_labeled(self):
        original = (
            b'<html><body><div class="wrap" data-pagefind-body>'
            b'<h1>Report</h1></div></body></html>'
        )
        rendered = MODULE.decorate_live_html(original, "2026-08-03T23:00:00Z")
        text = rendered.decode("utf-8")
        self.assertIn("LIVE LOCAL VIEW", text)
        self.assertIn("2026-08-03T23:00:00Z", text)
        self.assertIn("Reload to re-read", text)

    def test_live_builder_uses_authoritative_fragments(self):
        repo = Path("repo-root")
        out = Path("temporary-output")
        command = MODULE.report_builder_command(repo, out)
        source = command.index("--source")
        self.assertEqual(command[source + 1], "fragments")
        self.assertNotIn("--public", command)

    def test_development_startup_requires_explicit_write_opt_in(self):
        startup = (MODULE_PATH.parents[2] / "start-ai.ps1").read_text(encoding="utf-8")
        self.assertIn("[switch]$EnableWrite", startup)
        self.assertIn("if ($EnableWrite)", startup)
        self.assertNotIn("Stop-Process", startup)
        self.assertIn("refusing to stop an unverified process", startup)
        self.assertIn("/AI/health", startup)
        self.assertIn("READY will not be announced", startup)
        gateway_line = next(
            line for line in startup.splitlines() if line.lstrip().startswith("$gwArgs =")
        )
        self.assertIn("{2}", gateway_line)
        self.assertNotIn("--enable-write", gateway_line)

    def test_health_payload_names_live_and_snapshot_sources(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        server = MODULE.DynamicReportServer(
            ("127.0.0.1", 0),
            MODULE.Handler,
            repo_root=Path("repo-root"),
            upstream="http://127.0.0.1:3002",
            write_enabled=False,
        )
        server.last_render_at = "2026-08-16T00:00:00Z"
        try:
            with mock.patch.object(MODULE.urllib.request, "urlopen", return_value=Response()), \
                 mock.patch.object(
                     MODULE.maint_server,
                     "_registry_health",
                     return_value={"ok": True, "items": [], "pending_total": 0},
                 ):
                payload = server.health_payload()
        finally:
            server.server_close()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "live-development")
        self.assertEqual(payload["report_source"], "authoritative registry fragments")
        self.assertEqual(payload["snapshot_source"], "reviewed flat registries")
        self.assertFalse(payload["execute_enabled"])

    def test_unhealthy_payload_uses_service_unavailable(self):
        self.assertEqual(MODULE.health_status_code({"ok": True}), 200)
        self.assertEqual(MODULE.health_status_code({"ok": False}), 503)

    def test_health_route_returns_503_when_upstream_is_down(self):
        server = MODULE.DynamicReportServer(
            ("127.0.0.1", 0),
            MODULE.Handler,
            repo_root=Path("repo-root"),
            upstream="http://127.0.0.1:1",
            write_enabled=False,
        )
        server.last_render_at = "2026-08-16T00:00:00Z"
        worker = threading.Thread(target=server.handle_request, daemon=True)
        try:
            with mock.patch.object(MODULE.Handler, "log_message"), \
                 mock.patch.object(
                     MODULE.maint_server,
                     "_registry_health",
                     return_value={"ok": True, "items": [], "pending_total": 0},
                 ):
                worker.start()
                url = f"http://127.0.0.1:{server.server_address[1]}/AI/health"
                with self.assertRaises(MODULE.urllib.error.HTTPError) as failed:
                    MODULE.urllib.request.urlopen(url, timeout=5)
                self.assertEqual(failed.exception.code, 503)
                self.assertIn(b'"ok": false', failed.exception.read())
        finally:
            worker.join(timeout=5)
            server.server_close()

    def test_fresh_health_probes_report_generation_before_ready(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        server = MODULE.DynamicReportServer(
            ("127.0.0.1", 0),
            MODULE.Handler,
            repo_root=Path("repo-root"),
            upstream="http://127.0.0.1:3002",
            write_enabled=False,
        )

        def rendered(_name):
            server.last_render_at = "2026-08-16T00:00:00Z"
            server.last_render_error = ""
            return b"ok", server.last_render_at

        try:
            with mock.patch.object(server, "render_report", side_effect=rendered) as render, \
                 mock.patch.object(MODULE.urllib.request, "urlopen", return_value=Response()), \
                 mock.patch.object(
                     MODULE.maint_server,
                     "_registry_health",
                     return_value={"ok": True, "items": [], "pending_total": 0},
                 ):
                payload = server.health_payload()
        finally:
            server.server_close()
        render.assert_called_once_with("index.html")
        self.assertTrue(payload["ok"])

    def test_render_failure_is_recorded_for_health(self):
        server = MODULE.DynamicReportServer(
            ("127.0.0.1", 0),
            MODULE.Handler,
            repo_root=Path("repo-root"),
            upstream="http://127.0.0.1:3002",
            write_enabled=False,
        )
        try:
            with mock.patch.object(
                MODULE.subprocess,
                "run",
                side_effect=MODULE.subprocess.TimeoutExpired(["builder"], 30),
            ):
                with self.assertRaises(MODULE.subprocess.TimeoutExpired):
                    server.render_report("index.html")
            self.assertIn("TimeoutExpired", server.last_render_error)
        finally:
            server.server_close()

    def test_write_enabled_gateway_rejects_non_loopback_bind(self):
        with mock.patch.object(MODULE.sys, "stderr", io.StringIO()):
            result = MODULE.main(["--bind", "0.0.0.0", "--enable-write"])
        self.assertEqual(result, 2)

    def test_gateway_refuses_a_second_listener_on_the_same_port(self):
        first = MODULE.DynamicReportServer(
            ("127.0.0.1", 0),
            MODULE.Handler,
            repo_root=Path("repo-root"),
            upstream="http://127.0.0.1:3002",
            write_enabled=False,
        )
        try:
            with self.assertRaises(OSError):
                MODULE.DynamicReportServer(
                    first.server_address,
                    MODULE.Handler,
                    repo_root=Path("repo-root"),
                    upstream="http://127.0.0.1:3002",
                    write_enabled=False,
                )
        finally:
            first.server_close()


if __name__ == "__main__":
    unittest.main()
