"""Tests for the self-declared byte-budget gate.

WHY THIS FILE EXISTS. check_seed_budget.py enforces the Tier-1 seed's ceiling and
had no tests at all -- a gate nothing was watching, which is the exact shape it
was written to prevent ("An unenforced obligation is a wish"). Added 2026-09-02
alongside the TIGHT band.

Every case below states which behaviour it pins, because a budget gate has three
outcomes that are easy to conflate: within, within-but-tight, and over.
"""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import check_seed_budget as gate


def _doc(budget: int, size: int) -> str:
    """A document declaring `budget` and padded to exactly `size` BYTES."""
    head = f"    budget      : {budget} B hard ceiling\n"
    pad = size - len(head.encode())
    if pad < 0:
        raise ValueError("size smaller than the declaration itself")
    return head + ("x" * pad)


class DeclaredBudgetTests(unittest.TestCase):
    def test_reads_the_aligned_colon_header_style(self):
        self.assertEqual(gate.declared_budget(_doc(8192, 200)), 8192)

    def test_tolerates_separators(self):
        self.assertEqual(gate.declared_budget("budget: 8_192 B\n"), 8192)
        self.assertEqual(gate.declared_budget("budget: 8,192 B\n"), 8192)

    def test_absent_declaration_is_none_not_zero(self):
        """None and 0 must not collide: 0 would mean 'always over'."""
        self.assertIsNone(gate.declared_budget("# nothing here\n"))

    def test_declaration_below_the_header_window_is_not_found(self):
        body = "\n" * (gate.HEADER_LINES + 5) + "budget: 8192 B\n"
        self.assertIsNone(gate.declared_budget(body))


class CheckOutcomeTests(unittest.TestCase):
    def _run(self, size: int, budget: int = 8192, warn_only: bool = False):
        with TemporaryDirectory() as td:
            p = Path(td) / "seed.md"
            p.write_bytes(_doc(budget, size).encode())
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = gate.check(p, "seed.md", warn_only)
            return rc, out.getvalue(), err.getvalue()

    def test_comfortably_within_passes_without_a_tight_notice(self):
        rc, out, _ = self._run(4000)
        self.assertEqual(rc, 0)
        self.assertIn("PASS", out)
        self.assertNotIn("TIGHT", out)

    def test_tight_headroom_still_passes_but_says_so(self):
        """THE POINT OF THE BAND. Before this, 99% and 50% both printed PASS
        and nothing else -- one answer for two very different conditions."""
        rc, out, _ = self._run(8150)  # 42 B headroom, well under 5%
        self.assertEqual(rc, 0, "TIGHT must never block; it is a notice")
        self.assertIn("PASS", out)
        self.assertIn("TIGHT", out)

    def test_over_budget_blocks(self):
        rc, _, err = self._run(9000)
        self.assertEqual(rc, 2)
        self.assertIn("OVER BY", err)
        self.assertIn("808", err)

    def test_warn_only_reports_over_budget_without_blocking(self):
        rc, _, err = self._run(9000, warn_only=True)
        self.assertEqual(rc, 0)
        self.assertIn("WARN", err)

    def test_boundary_exactly_at_ceiling_is_within(self):
        """Off-by-one guard: the ceiling is inclusive, not exclusive."""
        rc, out, _ = self._run(8192)
        self.assertEqual(rc, 0)
        self.assertIn("PASS", out)

    def test_one_byte_over_is_out(self):
        rc, _, err = self._run(8193)
        self.assertEqual(rc, 2)
        self.assertIn("OVER BY 1", err)

    def test_headroom_is_reported_in_lines(self):
        _, out, _ = self._run(4000)
        self.assertIn("line(s)", out)

    def test_undeclared_budget_is_skipped_not_failed(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "plain.md"
            p.write_bytes(b"no declaration\n")
            out = io.StringIO()
            with redirect_stdout(out):
                rc = gate.check(p, "plain.md", False)
        self.assertEqual(rc, 0)
        self.assertIn("skipped", out.getvalue())

    def test_unreadable_target_is_distinct_from_over_budget(self):
        """Exit 1 and exit 2 must stay distinguishable: 'could not check' is
        not 'checked and found bad'."""
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.check(Path("does-not-exist.md"), "missing.md", False)
        self.assertEqual(rc, 1)


class ByteNotCharacterTests(unittest.TestCase):
    def test_multibyte_content_is_counted_as_bytes(self):
        """The docstring calls this a denominator error that already cost the
        lane three times. A char count would grant free room for non-ASCII."""
        with TemporaryDirectory() as td:
            p = Path(td) / "seed.md"
            head = "    budget      : 100 B hard ceiling\n"
            # Written as an escape, not a literal: this file must stay ASCII
            # (house rule), and the test needs a character that is 1 char but
            # 2 bytes in UTF-8. U+00E9 is exactly that.
            body = "\u00e9" * 40  # 40 chars, 80 bytes
            p.write_bytes((head + body).encode("utf-8"))
            self.assertGreater(len(p.read_bytes()), 100)
            err = io.StringIO()
            with redirect_stderr(err):
                rc = gate.check(p, "seed.md", False)
            self.assertEqual(rc, 2, "counted characters instead of bytes")


if __name__ == "__main__":
    unittest.main()
