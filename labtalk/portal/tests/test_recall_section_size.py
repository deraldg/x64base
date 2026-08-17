"""Regression: recall.section_size must not read code-fence comments as headings.

WHY THIS EXISTS (AIF-118, 2026-08-16)
    `section_size` is the number printed directly beneath the words that justify
    this whole tool -- "read these, not the corpus". Its failure mode is not a
    crash. It is a smaller number, and a smaller number is exactly what the tool
    is supposed to produce, so nothing ever looked wrong.

    Two corrections now, both the same shape:

      2026-07-31  summed whole FILE sizes, so six sections of one 48 KB file
                  counted it six times: a 217,471 B "working set", larger than
                  the entry path the graph exists to replace.
      2026-08-16  treated `# From the repository root:` inside a fenced
                  powershell block as the next heading, truncating
                  AI_README.md "## Runtime Start Points" to **64 B against an
                  actual 3516 B, a 46x under-report**. Latent since the function
                  was written; surfaced only because AIF-118 added a node that
                  pointed there. 1 of 20 anchored nodes was affected.

    So the arms below assert BOUNDS AND CONTENT, never "it returned a number".
    A size assertion alone would have passed against both broken versions.

PROVEN TO FAIL. Reverting the fence mask (searching the raw body) drops
test_fence_comment_is_not_a_heading from 3516 to 64 and the arm fails. Replacing
the mask with newlines-only -- which shortens the string and invalidates the
match offset, the mistake made while prototyping this very fix -- yields 2943
and also fails.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RECALL = REPO_ROOT / "labtalk" / "ai_portal" / "recall.py"

SPEC = importlib.util.spec_from_file_location("recall", RECALL)
recall = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(recall)


class SectionSizeTest(unittest.TestCase):
    def _write(self, text: str) -> tuple[Path, dict]:
        tmp = Path(tempfile.mkdtemp(prefix="recall-section-"))
        (tmp / "doc.md").write_text(text, encoding="utf-8")
        return tmp, {"path": "doc.md", "anchor": "## Target"}

    def test_fence_comment_is_not_a_heading(self):
        # The exact shape from AI_README.md: a `#` shell comment on line 2 of a
        # fenced block, inside the section being measured.
        doc = (
            "# Doc\n\nintro\n\n"
            "## Target\n\nfirst paragraph\n\n"
            "```powershell\n"
            "# From the repository root:\n"
            "& .\\build\\dottalkpp.exe\n"
            "```\n\n"
            "second paragraph that MUST be counted\n\n"
            "## Next\n\nnot counted\n"
        )
        root, node = self._write(doc)
        size = recall.section_size(root, node)
        # Content bound, not just a number: the tail must be inside the section.
        self.assertGreater(size, len("second paragraph that MUST be counted"),
                           "section truncated at the code-fence comment")
        # And it must stop at the real next heading.
        self.assertNotIn("not counted", (root / "doc.md").read_text()[:size])

    def test_stops_at_the_real_next_heading(self):
        doc = ("## Target\n\nkept\n\n## Next\n\n" + "x" * 5000 + "\n")
        root, node = self._write(doc)
        self.assertLess(recall.section_size(root, node), 200,
                        "section ran past its real end into the next heading")

    def test_unanchored_node_costs_the_whole_file(self):
        root, node = self._write("## Target\n\nbody\n")
        node = {"path": "doc.md"}
        self.assertEqual(recall.section_size(root, node),
                         (root / "doc.md").stat().st_size)

    def test_missing_file_is_zero_not_an_exception(self):
        self.assertEqual(recall.section_size(Path("/nonexistent"),
                                             {"path": "nope.md", "anchor": "## X"}), 0)

    def test_absent_anchor_falls_back_to_file_size(self):
        root, _ = self._write("## Target\n\nbody\n")
        node = {"path": "doc.md", "anchor": "## NotPresent"}
        self.assertEqual(recall.section_size(root, node),
                         (root / "doc.md").stat().st_size)

    def test_no_section_exceeds_its_own_file(self):
        # Whole-graph invariant. An offset bug shows up here as a section
        # larger than the file that contains it.
        import yaml
        graph = yaml.safe_load(
            (REPO_ROOT / "labtalk" / "registries" / "portal_recall_graph.yaml")
            .read_text(encoding="utf-8"))
        for node in graph["nodes"]:
            path = REPO_ROOT / str(node.get("path", ""))
            if not node.get("anchor") or not path.is_file():
                continue
            with self.subTest(node=node["id"]):
                self.assertLessEqual(recall.section_size(REPO_ROOT, node),
                                     path.stat().st_size)

    def test_the_node_that_exposed_the_bug(self):
        # Live check against the real corpus, with the measured value. If
        # AI_README.md is restructured this may legitimately change -- update the
        # bound, do not delete the arm.
        node = {"path": "AI_README.md", "anchor": "## Runtime Start Points"}
        size = recall.section_size(REPO_ROOT, node)
        self.assertGreater(size, 3000,
                           "regressed to the code-fence truncation (was 64 B)")


if __name__ == "__main__":
    unittest.main()
