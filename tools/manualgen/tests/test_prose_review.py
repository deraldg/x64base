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
    def test_policy_covers_exact_small_packet_topic_set(self) -> None:
        self.assertEqual(
            {
                "DOT|REGRESSION",
                "DOT|TEST",
                "DOT|GENERIC",
                "UI|ARCTICTALK",
                "UI|FOXPRO",
                "DOT|CANARY",
                "FOX|DO",
                "FOX|RUN",
            },
            set(PROSE_REVIEW_POLICY),
        )

    def test_policy_retains_risk_boundaries(self) -> None:
        counts = {}
        for row in PROSE_REVIEW_POLICY.values():
            counts[row["review_disposition"]] = counts.get(row["review_disposition"], 0) + 1
        self.assertEqual(
            {"ADDITIVE_PROSE": 4, "CANARY_CROSS_REFERENCE": 1, "APPENDIX_ONLY": 3},
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
