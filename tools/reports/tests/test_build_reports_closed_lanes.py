"""Integration test for the AI Portal closed/documented-only lane disclosure.

build_reports.py runs on import (it reads registries and emits HTML at module
load), so the honest way to test its output is to run it into a temp dir and
assert on the rendered AI_PORTAL_REPORT.html -- the same thing the dynamic
gateway does per request. Skips cleanly if the builder deps are unavailable.

Owner-directed AIF-086 M1 visibility improvement (2026-08-04): closed lanes must
be surfaced (collapsed) and linked, without regressing the active-lane table.
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
BUILDER = REPO / "tools" / "reports" / "build_reports.py"


def _deps_ok() -> bool:
    return importlib.util.find_spec("yaml") is not None


@unittest.skipUnless(BUILDER.is_file(), "build_reports.py not found")
@unittest.skipUnless(_deps_ok(), "pyyaml not installed")
class ClosedLaneDisclosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="dottalk-report-test-")
        out = Path(cls._tmp.name)
        result = subprocess.run(
            [sys.executable, str(BUILDER), "--root", str(REPO), "--out", str(out)],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        cls.returncode = result.returncode
        cls.stderr = result.stderr or ""
        portal = out / "AI_PORTAL_REPORT.html"
        cls.portal_exists = portal.is_file()
        cls.html = portal.read_text(encoding="utf-8", errors="replace") if cls.portal_exists else ""

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_builder_succeeds_and_emits_portal_report(self):
        self.assertEqual(self.returncode, 0, f"build_reports.py failed:\n{self.stderr[-800:]}")
        self.assertTrue(self.portal_exists, "AI_PORTAL_REPORT.html was not emitted")

    def test_active_lane_table_is_not_regressed(self):
        # the collapse is additive; the existing active-lane table must remain
        self.assertIn("Newest run (return here)", self.html)

    def test_closed_lane_disclosure_is_present_and_collapsible(self):
        self.assertIn("Closed / documented-only lanes", self.html)
        # a native <details> so it is collapsed by default, no JS, no redesign
        self.assertIn("<details", self.html)

    def test_closed_lanes_link_to_their_record(self):
        # at least one closed lane must link to its evidence/claim on GitHub
        self.assertIn("blob/development/", self.html)


if __name__ == "__main__":
    unittest.main()
