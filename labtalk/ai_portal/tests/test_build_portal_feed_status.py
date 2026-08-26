from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import build_portal_feed_status as status_builder  # noqa: E402


class PortalFeedStatusTests(unittest.TestCase):
    def build(self) -> dict[str, object]:
        feed_data = {
            "feeds": [
                {
                    "feed_id": "feed.test",
                    "subject_class": "test",
                    "status": "active",
                    "phase": {"canonical": "development_closeout"},
                    "evidence": {"state": "source-evidenced"},
                    "sensitivity": "internal",
                    "outputs": [{"path": "out"}],
                    "consumers": [{"path": "consumer"}],
                }
            ]
        }
        assertion_data = {
            "assertions": [
                {
                    "claim_id": "assertion.test",
                    "subject": "test",
                    "predicate": "state",
                    "validity": "invariant",
                    "expected": "green",
                }
            ]
        }
        current_data = {
            "observed_at_utc": "2026-08-26T04:29:19Z",
            "current": {
                "run_id": "DOCFLUSH-TEST",
                "canonical_process": "development_closeout",
                "state": "closed_review_needed",
                "publication_state": "not_entered",
                "next_process": "publication_ascent",
                "next_entry_state": "partial",
                "first_open_entry": "E5",
            },
        }
        with patch.object(status_builder, "validate_registry", return_value=([], [{"path": "out"}])), patch.object(
            status_builder,
            "validate_assertions",
            return_value=([], [{"claim_id": "assertion.test", "actual": "green", "passed": True}]),
        ):
            return status_builder.build_status(
                repo_root=Path.cwd(),
                feed_data=feed_data,
                assertion_data=assertion_data,
                current_data=current_data,
            )

    def test_builds_summary_from_validator_results(self) -> None:
        status = self.build()
        self.assertEqual(1, status["summary"]["feeds"])  # type: ignore[index]
        self.assertEqual(1, status["summary"]["assertions_passing"])  # type: ignore[index]
        self.assertEqual(1, status["summary"]["feed_artifact_observations"])  # type: ignore[index]

    def test_markdown_names_publication_boundary(self) -> None:
        markdown = status_builder.render_markdown(self.build())
        self.assertIn("publication_state", markdown)
        self.assertIn("not a promotion, deployment, or public publication receipt", markdown)

    def test_generation_is_deterministic(self) -> None:
        status = self.build()
        self.assertEqual(status_builder.render_markdown(status), status_builder.render_markdown(status))

    def test_yaml_timestamp_normalizes_to_json_utc(self) -> None:
        self.assertEqual(
            "2026-08-26T04:29:19Z",
            status_builder.json_scalar(datetime(2026, 8, 26, 4, 29, 19, tzinfo=timezone.utc)),
        )


if __name__ == "__main__":
    unittest.main()
