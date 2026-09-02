"""Tests for the capability-currency comparison in build_website_tree.

WHY THESE EXIST. The currency check answers "has a human read this page since
its authority changed?" -- and its whole value is that it does NOT collapse
distinct conditions into one word. That is easy to write and easy to regress,
and it already regressed once: the first version scoped the engine scan to
`src/`, so a contract declared under `include/` produced no date and was
reported as NO-CONTRACT ("nothing declared") when a contract WAS declared.

So every state below is pinned, and each is checked to be REACHABLE. A state
that cannot fire is decoration.
"""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build_website_tree import CURRENCY_NOTE, currency, last_touched  # noqa: E402


class CurrencyStateTests(unittest.TestCase):
    def setUp(self):
        self._td = TemporaryDirectory()
        self.engine = Path(self._td.name)
        (self.engine / "src" / "cli").mkdir(parents=True)
        (self.engine / "src" / "cli" / "cmd_thing.cpp").write_text("// x\n")
        self.addCleanup(self._td.cleanup)

    C = "src/cli/cmd_thing.cpp"

    def test_no_contract_when_none_declared(self):
        """Most pages make no capability claim. Not a finding."""
        state, _ = currency("2026-01-01", [], self.engine, [])
        self.assertEqual(state, "NO-CONTRACT")

    def test_current_when_page_is_newer(self):
        state, detail = currency("2026-09-02", ["2026-08-26"], self.engine, [self.C])
        self.assertEqual(state, "CURRENT")
        self.assertIn("2026-09-02", detail)

    def test_current_when_dates_are_equal(self):
        """Boundary: same-day is AT the contract, not behind it."""
        state, _ = currency("2026-08-26", ["2026-08-26"], self.engine, [self.C])
        self.assertEqual(state, "CURRENT")

    def test_unverified_when_contract_moved_after_the_page(self):
        """THE CASE THE TOOL EXISTS FOR -- workspaces.mdx, 2026-09-02."""
        state, detail = currency("2026-08-26", ["2026-08-30"], self.engine, [self.C])
        self.assertEqual(state, "UNVERIFIED")
        self.assertIn("2026-08-26", detail)
        self.assertIn("2026-08-30", detail)

    def test_newest_contract_wins_when_several_are_bound(self):
        state, detail = currency(
            "2026-08-27", ["2026-08-26", "2026-08-30"], self.engine, [self.C])
        self.assertEqual(state, "UNVERIFIED", "must compare against the NEWEST binding")
        self.assertIn("2026-08-30", detail)

    def test_missing_when_the_declared_contract_does_not_exist(self):
        state, detail = currency(
            "2026-09-02", ["2026-08-26"], self.engine, ["src/cli/cmd_ghost.cpp"])
        self.assertEqual(state, "MISSING")
        self.assertIn("cmd_ghost.cpp", detail)

    def test_missing_beats_dates(self):
        """A broken binding is reported even when the dates would say CURRENT."""
        state, _ = currency("2026-09-02", [], self.engine, ["src/nope.cpp"])
        self.assertEqual(state, "MISSING")

    def test_undated_is_not_no_contract(self):
        """THE REGRESSION THIS FILE WAS WRITTEN FOR.

        The file EXISTS, so it is not MISSING; but no date resolved. Reporting
        NO-CONTRACT here would say "nothing was declared" about a page that
        declared something -- one answer for two conditions, which is the exact
        defect the currency states were designed to avoid.
        """
        state, detail = currency("2026-09-02", [None], self.engine, [self.C])
        self.assertEqual(state, "UNDATED")
        self.assertNotEqual(state, "NO-CONTRACT")
        self.assertIn("declared", detail)

    def test_undated_when_the_page_itself_has_no_date(self):
        state, _ = currency(None, ["2026-08-26"], self.engine, [self.C])
        self.assertEqual(state, "UNDATED")

    def test_every_documented_state_is_reachable(self):
        """No decoration: each key in CURRENCY_NOTE must be producible."""
        produced = {
            currency("2026-09-02", ["2026-08-26"], self.engine, [self.C])[0],
            currency("2026-08-26", ["2026-08-30"], self.engine, [self.C])[0],
            currency("2026-01-01", [], self.engine, [])[0],
            currency("2026-09-02", [], self.engine, ["src/nope.cpp"])[0],
            currency("2026-09-02", [None], self.engine, [self.C])[0],
        }
        self.assertEqual(produced, set(CURRENCY_NOTE), "a documented state cannot fire")


class LastTouchedTests(unittest.TestCase):
    def test_missing_repo_returns_empty_not_an_exception(self):
        """A tool that dies on a bad root teaches nobody anything."""
        self.assertEqual(last_touched(Path("/nonexistent-repo-xyz")), {})


if __name__ == "__main__":
    unittest.main()
