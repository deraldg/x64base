"""The Tier 2 fallback table must never drift from the graph it was demoted into.

WHY THIS EXISTS (AIF-118, 2026-08-16)
    The Tier 1 seed's "Going deeper" table was demoted out on 2026-08-16,
    executing AIF-115's proposal. The seed's maintenance contract permits that
    only on one condition: "demoting means *moving*, not restating."

    A hand-copied table in a Tier 2 doc would have restated. `CLAUDE.md` records
    what that produces, citing AIF-082 6.8: "two shims that restate will diverge,
    and have." The same lane had already measured the seed table and the resolver
    diverging in BOTH directions -- four table rows with no trigger, five triggers
    with no row -- which is the divergence this rule exists to stop, having
    already happened once to this exact pair of artifacts.

    So the fallback is GENERATED (`recall.py --write-fallback`) and this test is
    what makes "generated" true rather than aspirational. Without it the file is
    a copy that merely claims to be derived, and the claim decays silently the
    first time someone edits the graph and forgets.

WHAT DRIFT LOOKS LIKE IF THIS TEST IS ABSENT
    Nothing. The doc keeps rendering, every link still resolves, and it quietly
    describes a graph that no longer exists. That is the failure mode this whole
    lane is named for, which is why the assertion is byte equality and not "the
    file exists" or "it has 17 rows".
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RECALL = REPO_ROOT / "labtalk" / "ai_portal" / "recall.py"

SPEC = importlib.util.spec_from_file_location("recall", RECALL)
recall = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(recall)


class FallbackSyncTest(unittest.TestCase):
    def setUp(self):
        self.target = REPO_ROOT / recall.FALLBACK_DOC
        self.graph = recall.load(REPO_ROOT)

    def test_the_fallback_doc_exists(self):
        self.assertTrue(
            self.target.is_file(),
            f"{recall.FALLBACK_DOC} is missing. The Tier 1 seed points at it as "
            "the no-python fallback, so its absence removes the entire trigger "
            "index for anyone who cannot run the resolver.",
        )

    def test_it_is_byte_identical_to_what_the_graph_renders(self):
        expected = recall.fallback_markdown(REPO_ROOT, self.graph)
        actual = self.target.read_text(encoding="utf-8")
        self.assertEqual(
            actual, expected,
            "the fallback table has drifted from portal_recall_graph.yaml. "
            "Regenerate it: python labtalk/ai_portal/recall.py --write-fallback",
        )

    def test_every_trigger_appears(self):
        # Content bound, not just equality: catches a generator that renders
        # nothing while still matching a file it also wrote.
        text = self.target.read_text(encoding="utf-8")
        for trig in self.graph["triggers"]:
            with self.subTest(trigger=trig["id"]):
                self.assertIn(str(trig.get("label", "")), text)

    def test_it_declares_itself_generated(self):
        head = self.target.read_text(encoding="utf-8")[:400]
        self.assertIn("GENERATED", head)
        self.assertIn("DO NOT HAND-EDIT", head)
        self.assertIn("--write-fallback", head)

    def test_the_seed_still_points_at_it(self):
        # The demotion is only safe while the seed names where the content went.
        seed = (REPO_ROOT / "labtalk" / "ai_portal" / "AI_TIER1_SEED_V1.md")
        self.assertIn(recall.FALLBACK_DOC, seed.read_text(encoding="utf-8"),
                      "the seed no longer points at the demoted table -- the "
                      "content is then filed but unreachable, which is the "
                      "defect AIF-082 case study 3 records")


if __name__ == "__main__":
    unittest.main()
