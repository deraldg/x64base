from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "audit_help_contract_continuation.py"
SPEC = importlib.util.spec_from_file_location("continuation_audit", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class HelpContractContinuationTests(unittest.TestCase):
    def test_detects_lost_continuation_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            srcusage = root / "srcusage.csv"
            topics = root / "topics.csv"
            lines = root / "lines.csv"
            write_csv(
                srcusage,
                ["OWNER", "COMMAND", "USAGE", "EXAMPLES", "NOTES", "RELATED"],
                [
                    {
                        "OWNER": "DOT|DIR",
                        "COMMAND": "DIR",
                        "USAGE": "DIR\nDIR <path>",
                        "EXAMPLES": "",
                        "NOTES": "first line\ncontinuation",
                        "RELATED": "SETPATH",
                    }
                ],
            )
            write_csv(
                topics,
                ["TOPICKEY", "SUPPORTED"],
                [{"TOPICKEY": "DOT|DIR", "SUPPORTED": "T"}],
            )
            write_csv(
                lines,
                ["TOPICKEY", "SOURCE", "TEXT"],
                [
                    {"TOPICKEY": "DOT|DIR", "SOURCE": "USAGE_CONTRACT", "TEXT": "DIR"},
                    {"TOPICKEY": "DOT|DIR", "SOURCE": "USAGE_CONTRACT", "TEXT": "DIR <path>"},
                    {"TOPICKEY": "DOT|DIR", "SOURCE": "USAGE_CONTRACT", "TEXT": "first line"},
                    {"TOPICKEY": "DOT|DIR", "SOURCE": "USAGE_CONTRACT", "TEXT": "SETPATH"},
                ],
            )
            manifest = MOD.audit(srcusage, topics, lines, root / "out")
            self.assertEqual("FAIL", manifest["status"])
            self.assertEqual(1, manifest["counts"]["missing_lines"])

    def test_complete_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            srcusage = root / "srcusage.csv"
            topics = root / "topics.csv"
            lines = root / "lines.csv"
            write_csv(
                srcusage,
                ["OWNER", "COMMAND", "USAGE", "EXAMPLES", "NOTES", "RELATED"],
                [
                    {
                        "OWNER": "DOT|USER",
                        "COMMAND": "USER",
                        "USAGE": "USER LOGIN\nUSER VERIFY",
                        "EXAMPLES": "",
                        "NOTES": "owner gated",
                        "RELATED": "SECURITY",
                    }
                ],
            )
            write_csv(
                topics,
                ["TOPICKEY", "SUPPORTED"],
                [{"TOPICKEY": "DOT|USER", "SUPPORTED": "T"}],
            )
            write_csv(
                lines,
                ["TOPICKEY", "SOURCE", "TEXT"],
                [
                    {"TOPICKEY": "DOT|USER", "SOURCE": "USAGE_CONTRACT", "TEXT": "USER LOGIN"},
                    {"TOPICKEY": "DOT|USER", "SOURCE": "USAGE_CONTRACT", "TEXT": "USER VERIFY"},
                    {"TOPICKEY": "DOT|USER", "SOURCE": "USAGE_CONTRACT", "TEXT": "owner gated"},
                    {"TOPICKEY": "DOT|USER", "SOURCE": "USAGE_CONTRACT", "TEXT": "SECURITY"},
                ],
            )
            manifest = MOD.audit(srcusage, topics, lines, root / "out")
            self.assertEqual("PASS", manifest["status"])
            self.assertEqual(0, manifest["counts"]["missing_lines"])


if __name__ == "__main__":
    unittest.main()
