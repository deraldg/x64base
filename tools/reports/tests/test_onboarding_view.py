"""Proof that the onboarding page reads live local sources without publishing them."""

import http.client
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


REPORTS = Path(__file__).resolve().parents[1]
if str(REPORTS) not in sys.path:
    sys.path.insert(0, str(REPORTS))
import onboarding_view as view
import serve_dynamic_reports as gateway


class OnboardingViewTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.repo = Path(workspace.name)
        self.put(view.SEED, "Getting started: <script>untrusted</script>")
        self.put(view.LAWS, "Rules for people and agents")
        self.put(view.SNAPSHOT, "Branch: development")
        self.put(view.recall.REGISTRY, f"""entry_path:
  - path: {view.SEED}
  - path: {view.LAWS}
  - path: {view.SNAPSHOT}
triggers:
  - id: trigger.onboard
    label: start cold
  - id: trigger.review
    label: review a lane
nodes:
  - id: seed
    tier: 1
    path: {view.SEED}
  - id: laws
    tier: 1
    path: {view.LAWS}
  - id: state
    tier: 0
    path: {view.SNAPSHOT}
  - id: reference
    tier: 2
    label: Lane doctrine
    path: docs/lane.md
    anchor: Approval
edges:
  - {{from: trigger.onboard, to: seed, type: fires_at}}
  - {{from: trigger.review, to: reference, type: fires_at}}
""")

    def put(self, relative, text):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_three_tiers_come_from_local_sources(self):
        rendered = view.render(self.repo)
        for tier in (0, 1, 2):
            self.assertIn(f'<section id="tier-{tier}">', rendered)
        order = rendered.split("<ol>", 1)[1].split("</ol>", 1)[0]
        self.assertLess(order.index("#tier-1-seed"), order.index("#agent-laws"))
        self.assertLess(order.index("#agent-laws"), order.index("#tier-0-snapshot"))
        self.assertIn("&lt;script&gt;untrusted&lt;/script&gt;", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertIn("Rules for people and agents", rendered)
        self.assertIn("Branch: development", rendered)
        self.assertIn("Lane doctrine", rendered)
        self.assertIn("review a lane", rendered)
        self.assertIn("docs/lane.md", rendered)
        self.assertIn("Approval", rendered)

    def test_reloading_rereads_but_does_not_regenerate_snapshot(self):
        self.put(view.SNAPSHOT, "Branch: rendered again")
        self.assertIn("Branch: rendered again", view.render(self.repo))
        self.assertEqual((self.repo / view.SNAPSHOT).read_text(), "Branch: rendered again")
        (self.repo / view.SNAPSHOT).unlink()
        self.assertIn("Source unavailable in this checkout", view.render(self.repo))
        self.assertFalse((self.repo / view.SNAPSHOT).exists())

    def test_http_route_is_loopback_read_only(self):
        with gateway.DynamicReportServer(
            ("127.0.0.1", 0), gateway.Handler, repo_root=self.repo,
            upstream="http://127.0.0.1:1", write_enabled=True,
        ) as server, mock.patch.object(gateway.Handler, "log_message"):
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                def request(method, host="localhost"):
                    with self.subTest(method=method, host=host):
                        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                        try:
                            conn.request(method, view.ONBOARDING_PATH, headers={"Host": host})
                            response = conn.getresponse()
                            return response.status, dict(response.getheaders()), response.read()
                        finally:
                            conn.close()

                status, headers, body = request("GET")
                self.assertEqual(status, 200)
                self.assertIn(b"AI Portal Onboarding", body)
                self.assertEqual(headers["Cache-Control"], "no-store")
                self.assertIn("form-action 'none'", headers["Content-Security-Policy"])
                self.assertEqual(request("HEAD")[2], b"")
                self.assertEqual(request("POST")[0], 404)
                self.assertEqual(request("GET", host="public.example")[0], 404)
            finally:
                server.shutdown()
                worker.join(timeout=5)

    def test_local_navigation_link_is_opt_in_and_not_a_report_export(self):
        html = "<html><body>Report</body></html>"
        self.assertNotIn(view.ONBOARDING_PATH, gateway.inject_nav(html))
        self.assertIn(view.ONBOARDING_PATH, gateway.inject_nav(html, show_onboarding=True))
        self.assertIsNone(gateway.report_name_for_path(view.ONBOARDING_PATH))
        self.assertFalse(gateway.local_onboarding_request("0.0.0.0", "127.0.0.1", ["localhost"]))
        self.assertFalse(gateway.local_onboarding_request("127.0.0.1", "192.0.2.1", ["localhost"]))
        self.assertFalse(gateway.local_onboarding_request("127.0.0.1", "127.0.0.1", ["localhost", "localhost"]))


if __name__ == "__main__":
    unittest.main()
