from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal.validate_portal_assertions import validate_assertions  # noqa: E402


NOW = datetime(2026, 8, 26, 4, 30, tzinfo=timezone.utc)


class PortalAssertionValidatorTests(unittest.TestCase):
    def make_repo(self) -> tuple[Path, tempfile.TemporaryDirectory[str]]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "evidence.md").write_text("# Evidence\n\nAnchor once.\n", encoding="utf-8")
        (root / "source.yaml").write_text(
            "schema: test.v1\nitems:\n  - id: alpha\n  - id: beta\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
        subprocess.run(["git", "add", "evidence.md", "source.yaml"], cwd=root, check=True)
        return root, temp

    def assertion(self) -> dict[str, object]:
        return {
            "claim_id": "assertion.test",
            "subject": "test",
            "predicate": "schema",
            "expected": "test.v1",
            "status": "active",
            "validity": "invariant",
            "platform": "test-host",
            "evidence": [
                {
                    "path": "evidence.md",
                    "retention": "tracked",
                    "anchor": "Anchor once.",
                }
            ],
            "check": {
                "kind": "yaml_value",
                "path": "source.yaml",
                "selector": "schema",
                "operator": "equals",
                "expected": "test.v1",
            },
        }

    def registry(self, *assertions: dict[str, object]) -> dict[str, object]:
        return {"schema": "dottalk.portal.assertions.v1", "assertions": list(assertions)}

    def issues(self, findings: list[dict[str, str]]) -> str:
        return "\n".join(item["issue"] for item in findings)

    def test_known_good_structured_assertion_passes(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        findings, observations = validate_assertions(self.registry(self.assertion()), root, now=NOW)
        self.assertEqual([], findings)
        self.assertTrue(observations[0]["passed"])

    def test_false_value_goes_red(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        assertion = self.assertion()
        assertion["check"]["expected"] = "wrong"  # type: ignore[index]
        findings, _ = validate_assertions(self.registry(assertion), root, now=NOW)
        self.assertIn("ASSERTION_FALSE", self.issues(findings))

    def test_expired_perishable_assertion_goes_red(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        assertion = self.assertion()
        assertion["validity"] = "perishable"
        assertion["measured_at_utc"] = "2026-08-20T00:00:00Z"
        assertion["expires_at_utc"] = "2026-08-25T00:00:00Z"
        findings, _ = validate_assertions(self.registry(assertion), root, now=NOW)
        self.assertIn("ASSERTION_EXPIRED", self.issues(findings))

    def test_missing_anchor_goes_red(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        assertion = self.assertion()
        assertion["evidence"][0]["anchor"] = "Absent"  # type: ignore[index]
        findings, _ = validate_assertions(self.registry(assertion), root, now=NOW)
        self.assertIn("observed 0", self.issues(findings))

    def test_duplicate_anchor_goes_red(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        (root / "evidence.md").write_text("Anchor once.\nAnchor once.\n", encoding="utf-8")
        findings, _ = validate_assertions(self.registry(self.assertion()), root, now=NOW)
        self.assertIn("observed 2", self.issues(findings))

    def test_untracked_evidence_goes_red(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        (root / "untracked.md").write_text("Anchor once.\n", encoding="utf-8")
        assertion = self.assertion()
        assertion["evidence"][0]["path"] = "untracked.md"  # type: ignore[index]
        findings, _ = validate_assertions(self.registry(assertion), root, now=NOW)
        self.assertIn("evidence is not tracked", self.issues(findings))

    def test_collection_membership_passes(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        assertion = self.assertion()
        assertion["expected"] = "beta"
        assertion["check"] = {
            "kind": "yaml_collection_has",
            "path": "source.yaml",
            "selector": "items",
            "match_field": "id",
            "expected": "beta",
        }
        findings, observations = validate_assertions(self.registry(assertion), root, now=NOW)
        self.assertEqual([], findings)
        self.assertEqual(["alpha", "beta"], observations[0]["actual"])

    def test_unsupported_free_text_check_is_rejected(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        assertion = self.assertion()
        assertion["check"]["kind"] = "grep_phrase"  # type: ignore[index]
        findings, _ = validate_assertions(self.registry(assertion), root, now=NOW)
        self.assertIn("unsupported structured check", self.issues(findings))


if __name__ == "__main__":
    unittest.main()
