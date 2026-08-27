from __future__ import annotations

import sys
import unittest
from pathlib import Path


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import verify_memory_pilot_recall as verifier  # noqa: E402


class MemoryPilotRecallTests(unittest.TestCase):
    def manifest(self) -> dict[str, object]:
        return {
            "ruling_state": "approved",
            "items": [{
                "source_uri": "labtalk/ai_portal/history.md",
                "expected_sha256": "a" * 64,
            }],
        }

    def test_exact_summary_and_onboarding_exclusion_pass(self) -> None:
        findings = verifier.verify_outputs(
            self.manifest(),
            "labtalk/ai_portal/history.md\n" + "a" * 64,
            "AI_TIER1_SEED_V1.md",
            "PORTAL_HISTORY_SUMMARY_V1.md",
        )
        self.assertEqual([], findings)

    def test_body_in_onboarding_or_missing_hash_fails(self) -> None:
        findings = "\n".join(verifier.verify_outputs(
            self.manifest(),
            "labtalk/ai_portal/history.md",
            "history.md",
            "PORTAL_HISTORY_SUMMARY_V1.md",
        ))
        self.assertIn("ordinary onboarding loads cold body", findings)
        self.assertIn("does not resolve expected hash", findings)


if __name__ == "__main__":
    unittest.main()
