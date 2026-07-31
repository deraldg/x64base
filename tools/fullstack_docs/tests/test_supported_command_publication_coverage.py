from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "audit_supported_command_publication_coverage.py"
SPEC = importlib.util.spec_from_file_location("coverage_audit", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


def write_topics(path: Path, topics: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["TOPICKEY", "CATALOG", "TOPIC", "STATUS", "SUPPORTED"],
            lineterminator="\n",
        )
        writer.writeheader()
        for topic in topics:
            writer.writerow(
                {
                    "TOPICKEY": f"DOT|{topic}",
                    "CATALOG": "DOT",
                    "TOPIC": topic,
                    "STATUS": "supported",
                    "SUPPORTED": "T",
                }
            )


class SupportedCommandPublicationCoverageTests(unittest.TestCase):
    def test_new_supported_gap_fails_while_baseline_gap_is_backlog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "current.csv"
            baseline = root / "baseline.csv"
            commands = root / "commands"
            commands.mkdir()
            write_topics(baseline, ["OLD"])
            write_topics(current, ["OLD", "NEW"])
            manifest = MOD.audit(current, baseline, commands, None, root / "out")
            self.assertEqual("FAIL", manifest["status"])
            self.assertEqual(1, manifest["counts"]["historical_backlog"])
            self.assertEqual(["DOT|NEW"], manifest["blocking_topic_keys"])

    def test_new_supported_page_closes_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "current.csv"
            baseline = root / "baseline.csv"
            commands = root / "commands"
            commands.mkdir()
            write_topics(baseline, ["OLD"])
            write_topics(current, ["OLD", "NEW COMMAND"])
            (commands / "new_command.md").write_text("# New\n", encoding="utf-8")
            manifest = MOD.audit(current, baseline, commands, None, root / "out")
            self.assertEqual("PASS", manifest["status"])
            self.assertEqual(0, manifest["counts"]["blocking_new_supported_gaps"])

    def test_reviewed_hold_is_explicit_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "current.csv"
            baseline = root / "baseline.csv"
            dispositions = root / "dispositions.csv"
            commands = root / "commands"
            commands.mkdir()
            write_topics(baseline, [])
            write_topics(current, ["NEW"])
            with dispositions.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["topic_key", "disposition", "rationale"],
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "topic_key": "DOT|NEW",
                        "disposition": "HOLD",
                        "rationale": "Runtime proof pending.",
                    }
                )
            manifest = MOD.audit(
                current, baseline, commands, dispositions, root / "out"
            )
            self.assertEqual("PASS", manifest["status"])
            self.assertEqual(1, manifest["counts"]["covered_by_disposition"])


if __name__ == "__main__":
    unittest.main()
