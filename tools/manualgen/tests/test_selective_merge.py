from __future__ import annotations

import sys
import unittest
from pathlib import Path


MANUALGEN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MANUALGEN_ROOT))

from manualgen_lib.selective_merge import (  # noqa: E402
    _delta_counts,
    _extract_from_heading,
    _insert_after_h2_section,
)


class SelectiveMergeTests(unittest.TestCase):
    def test_insert_occurs_after_complete_named_subsection(self) -> None:
        base = "# T\n\n## A\n\nExisting A.\n\n## B\n\nExisting B.\n"
        candidate = _insert_after_h2_section(base, "## A", "### Added\n\nNew text.")
        self.assertLess(candidate.index("Existing A."), candidate.index("### Added"))
        self.assertLess(candidate.index("### Added"), candidate.index("## B"))

    def test_extraction_preserves_reviewed_fragment_heading(self) -> None:
        source = "# Candidate\n\n## Start\n\nText\n\n## Stop\n\nLater\n"
        self.assertEqual("## Start\n\nText", _extract_from_heading(source, "## Start", "## Stop"))

    def test_selective_section_merge_is_additive_only(self) -> None:
        base = "# T\n\n## A\n\nExisting.\n\n## B\n\nEnd.\n"
        candidate = _insert_after_h2_section(base, "## A", "### Added\n\nNew.")
        additions, deletions = _delta_counts(base, candidate)
        self.assertGreater(additions, 0)
        self.assertEqual(0, deletions)

    def test_merge_preserves_base_eof_blank_lines(self) -> None:
        base = "# T\n\n## A\n\nExisting.\n\n## B\n\nEnd.\n\n\n"
        candidate = _insert_after_h2_section(base, "## A", "### Added\n\nNew.")
        self.assertTrue(candidate.endswith("\n\n\n"))
        self.assertEqual((4, 0), _delta_counts(base, candidate))


if __name__ == "__main__":
    unittest.main()
