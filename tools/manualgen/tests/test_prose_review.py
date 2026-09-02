from __future__ import annotations

import sys
import unittest
from pathlib import Path


MANUALGEN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MANUALGEN_ROOT))

from manualgen_lib.prose_review import (  # noqa: E402
    COMMAND_SLUG,
    PARTIAL_HELP_SLUG,
    PROSE_REVIEW_POLICY,
    RUNTIME_SLUG,
    render_prose_candidates,
)


class ProseReviewTests(unittest.TestCase):
    """Boundary tests for the prose review packet.

    RE-BASELINED 2026-09-02 to the AIF-068 policy. Both assertions below had
    been failing since the day this file entered version control, and that is
    the useful part of the story:

        2026-07-27  2d138e001  AIF-068 re-baselined the curation chain and moved
                               "prose + selective-merge policy to 16 topics",
                               deliberately and in the commit message.
        2026-07-31  5ca43a7ec  "chore(tools): track manualgen -- manual assembly
                               pipeline, previously untracked" -- this test was
                               UNTRACKED while that happened, so it arrived in
                               git still asserting the PRE-AIF-068 eight-topic
                               set.

    The code was right and the test was stale, not the other way round. A test
    that is red on arrival guards nothing: a standing failure is indistinguish-
    able from a new regression, so the boundary these two exist to hold has been
    unenforced since 2026-07-31.

    THEN A SECOND, SEPARATE CHANGE, same day and worth keeping distinct:

        2026-09-02  owner ruling on V6_HINTS section 4, candidate (b).
                    DOT|UDATE, DOT|UDATETIME, DOT|UNOW and DOT|UTIME removed
                    from the policy. AIF-068 had added them as APPENDIX_ONLY
                    because they were publishing as unsupported DOT command
                    rows; ruling (b) fixed the filter instead (c8aa6a583), so
                    they are function-only and are no longer command topics.

    So the packet went 8 -> 16 (AIF-068, deliberate) -> 12 (this ruling), and
    APPENDIX_ONLY went 3 -> 7 -> 3, landing back on its original value because
    those four WERE the appendix additions. The first edit here fixed staleness;
    the second implemented a ruling. Neither relaxed anything: the set and the
    counts are still EXACT, so the packet cannot grow silently.

    To change the packet again: change the policy FIRST and these assertions
    second, in that order, so the test fails and says what moved.
    """

    def test_policy_covers_exact_small_packet_topic_set(self) -> None:
        self.assertEqual(
            {
                # pre-AIF-068 core, unchanged
                "DOT|REGRESSION",
                "DOT|TEST",
                "DOT|GENERIC",
                "UI|ARCTICTALK",
                "UI|FOXPRO",
                "DOT|CANARY",
                "FOX|DO",
                "FOX|RUN",
                # added by AIF-068 (2d138e001, 2026-07-27) and retained
                "DOT|DEFCMD",
                "DOT|UNDEFCMD",
                "UI|RECORD",
                "UI|RECORDVIEW",
                # AIF-068 also added DOT|UDATE, UDATETIME, UNOW and UTIME as
                # APPENDIX_ONLY. REMOVED 2026-09-02 by the owner ruling on
                # V6_HINTS section 4, candidate (b): the filter was fixed
                # (c8aa6a583) so those four are function-only and are no longer
                # command topics. APPENDIX_ONLY therefore returns to 3, its
                # pre-AIF-068 value -- those four WERE the appendix additions.
            },
            set(PROSE_REVIEW_POLICY),
        )

    def test_policy_retains_risk_boundaries(self) -> None:
        counts = {}
        for row in PROSE_REVIEW_POLICY.values():
            counts[row["review_disposition"]] = counts.get(row["review_disposition"], 0) + 1
        # AIF-068 baseline, less the four V6_HINTS section 4 functions removed by
        # the 2026-09-02 ruling: 8 additive, 1 canary cross-reference, 3 appendix.
        self.assertEqual(
            {"ADDITIVE_PROSE": 8, "CANARY_CROSS_REFERENCE": 1, "APPENDIX_ONLY": 3},
            counts,
        )

    def test_rendered_fragments_are_candidate_only_and_anchored(self) -> None:
        packet_info = {
            RUNTIME_SLUG: {"relative_path": "runtime.md", "sha256": "A" * 64},
            COMMAND_SLUG: {"relative_path": "command.md", "sha256": "B" * 64},
            PARTIAL_HELP_SLUG: {"relative_path": "partial.md", "sha256": "C" * 64},
        }
        rendered = render_prose_candidates(packet_info)
        self.assertEqual(3, len(rendered))
        self.assertTrue(all("Not publication" in body for body in rendered.values()))
        self.assertTrue(all("Replacement authorized: 0" in body for body in rendered.values()))
        self.assertIn("Suggested anchor after", next(body for name, body in rendered.items() if name.startswith(RUNTIME_SLUG)))
        self.assertIn("APPENDIX", next(body for name, body in rendered.items() if name.startswith(PARTIAL_HELP_SLUG)).upper())


if __name__ == "__main__":
    unittest.main()
