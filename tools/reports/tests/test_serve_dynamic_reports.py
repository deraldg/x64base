import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "serve_dynamic_reports.py"
SPEC = importlib.util.spec_from_file_location("serve_dynamic_reports", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ReportRouteTests(unittest.TestCase):
    def test_report_routes_keep_existing_urls(self):
        cases = {
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

    def test_live_response_is_visibly_labeled(self):
        original = b'<html><body><div class="wrap"><h1>Report</h1></div></body></html>'
        rendered = MODULE.decorate_live_html(original, "2026-08-03T23:00:00Z")
        text = rendered.decode("utf-8")
        self.assertIn("LIVE LOCAL VIEW", text)
        self.assertIn("2026-08-03T23:00:00Z", text)
        self.assertIn("Reload to re-read", text)


if __name__ == "__main__":
    unittest.main()
