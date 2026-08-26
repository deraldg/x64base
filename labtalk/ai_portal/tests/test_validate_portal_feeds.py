from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal.validate_portal_feeds import validate_registry  # noqa: E402


class PortalFeedValidatorTests(unittest.TestCase):
    def make_repo(self) -> tuple[Path, tempfile.TemporaryDirectory[str]]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for relative, content in (
            ("source.txt", "authority\n"),
            ("producer.py", "print('producer')\n"),
            ("output.json", "{}\n"),
            ("proof.md", "# proof\n"),
            ("consumer.md", "# consumer\n"),
        ):
            (root / relative).write_text(content, encoding="utf-8")
        subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
        subprocess.run(
            ["git", "add", "source.txt", "producer.py", "output.json", "proof.md", "consumer.md"],
            cwd=root,
            check=True,
        )
        return root, temp

    def feed(self) -> dict[str, object]:
        return {
            "feed_id": "feed.test",
            "subject_class": "test_data",
            "status": "active",
            "phase": {"canonical": "development_closeout", "legacy_labels": ["test"]},
            "source_authorities": [
                {"path": "source.txt", "role": "authority", "retention": "tracked"}
            ],
            "producer": {"kind": "tool", "path": "producer.py", "retention": "tracked"},
            "outputs": [
                {"path": "output.json", "role": "projection", "retention": "tracked"}
            ],
            "evidence": {
                "state": "source-evidenced",
                "platform": "test-host",
                "proofs": [{"id": "proof.test", "path": "proof.md", "retention": "tracked"}],
            },
            "sensitivity": "internal",
            "derived_from": [],
            "consumers": [
                {
                    "id": "consumer.test",
                    "path": "consumer.md",
                    "retention": "tracked",
                    "visibility": "internal",
                    "mode": "reads",
                }
            ],
            "freshness": {"policy": "validate_on_change"},
        }

    def registry(self, *feeds: dict[str, object]) -> dict[str, object]:
        return {"schema": "dottalk.portal.feed.v1", "feeds": list(feeds)}

    def issues(self, findings: list[dict[str, str]]) -> str:
        return "\n".join(f"{item['field']}: {item['issue']}" for item in findings)

    def test_known_good_registry_passes(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        findings, observations = validate_registry(self.registry(self.feed()), root)
        self.assertEqual([], findings)
        self.assertGreaterEqual(len(observations), 5)

    def test_missing_path_goes_red(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        feed = self.feed()
        feed["outputs"][0]["path"] = "missing.json"  # type: ignore[index]
        findings, _ = validate_registry(self.registry(feed), root)
        self.assertIn("path does not exist", self.issues(findings))

    def test_bad_hash_is_attestation_stale(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        feed = self.feed()
        feed["outputs"][0]["sha256"] = "0" * 64  # type: ignore[index]
        findings, _ = validate_registry(self.registry(feed), root)
        self.assertIn("ATTESTATION_STALE", self.issues(findings))

    def test_unknown_parent_goes_red(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        feed = self.feed()
        feed["derived_from"] = ["feed.missing"]
        findings, _ = validate_registry(self.registry(feed), root)
        self.assertIn("unknown parent feed", self.issues(findings))

    def test_lineage_cycle_goes_red(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        first = self.feed()
        second = self.feed()
        first["feed_id"] = "feed.first"
        second["feed_id"] = "feed.second"
        first["derived_from"] = ["feed.second"]
        second["derived_from"] = ["feed.first"]
        findings, _ = validate_registry(self.registry(first, second), root)
        self.assertIn("lineage cycle", self.issues(findings))

    def test_runtime_proven_without_proof_goes_red(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        feed = self.feed()
        feed["evidence"] = {"state": "runtime-proven", "platform": "test-host", "proofs": []}
        findings, _ = validate_registry(self.registry(feed), root)
        self.assertIn("runtime-proven feed requires", self.issues(findings))

    def test_visibility_leak_goes_red(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        feed = self.feed()
        feed["sensitivity"] = "restricted"
        feed["consumers"][0]["visibility"] = "public"  # type: ignore[index]
        findings, _ = validate_registry(self.registry(feed), root)
        self.assertIn("visibility leak", self.issues(findings))

    def test_transient_output_requires_hash_and_tracked_proof(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        feed = self.feed()
        feed["outputs"][0]["retention"] = "transient"  # type: ignore[index]
        feed["evidence"]["proofs"] = []  # type: ignore[index]
        findings, _ = validate_registry(self.registry(feed), root)
        issues = self.issues(findings)
        self.assertIn("transient output requires a SHA-256 pin", issues)
        self.assertIn("transient output requires a tracked proof", issues)

    def test_transient_output_with_hash_and_proof_passes(self) -> None:
        root, temp = self.make_repo()
        self.addCleanup(temp.cleanup)
        feed = self.feed()
        digest = hashlib.sha256((root / "output.json").read_bytes()).hexdigest()
        feed["outputs"][0]["retention"] = "transient"  # type: ignore[index]
        feed["outputs"][0]["sha256"] = digest  # type: ignore[index]
        findings, _ = validate_registry(self.registry(feed), root)
        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
