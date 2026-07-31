from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from tools.source_objects.parser import parse_source_text
from tools.source_objects.scan import write_reports


SAMPLE = """/*
 * @dottalk.location v1
 * id: DOTSRC-SAMPLE-001
 * home: src/cli
 * canonical-path: src/cli/cmd_sample.cpp
 * project: dottalkpp
 * role: command-implementation
 * author: Example Author
 * created: 2026-07-01
 * last-modified-by: Example Maintainer
 * last-modified: 2026-07-22
 * @dottalk.end
 */
// @dottalk.usage v1
// owner: UI|SAMPLE
// command: SAMPLE
// summary: Example command.
// @dottalk.end

int sample() {
    return 1; // inline comment remains code
}
"""


class SourceObjectTests(unittest.TestCase):
    def test_complete_object_and_matching_home(self) -> None:
        item = parse_source_text(SAMPLE, "src/cli/cmd_sample.cpp")
        self.assertEqual("MATCH", item.location_status)
        self.assertEqual("DOTSRC-SAMPLE-001", item.source_id)
        self.assertEqual("DECLARED", item.identity_status)
        self.assertEqual("src/cli", item.declared_home)
        self.assertEqual("Example Author", item.author)
        self.assertEqual("2026-07-01", item.date)
        self.assertEqual("2026-07-22", item.last_modified_date)
        self.assertEqual(1, len(item.usage_contracts))
        self.assertEqual("SAMPLE", item.usage_contracts[0].fields["command"])
        self.assertTrue(item.comment_sections)
        self.assertIn("inline comment remains code", item.code_sections[-1].text)

    def test_moved_file_is_reported(self) -> None:
        item = parse_source_text(SAMPLE, "src/runtime/cmd_sample.cpp")
        self.assertEqual("MISMATCH", item.location_status)
        self.assertIn("DECLARED_HOME_MISMATCH", item.findings)

    def test_missing_contract_is_explicit(self) -> None:
        item = parse_source_text("int main() { return 0; }\n", "src/main.cpp")
        self.assertEqual("UNDECLARED", item.location_status)
        self.assertIsNone(item.author)
        self.assertEqual("PATH_DERIVED", item.identity_status)

    def test_git_history_can_supply_tracked_attribution(self) -> None:
        without_claims = SAMPLE.replace(" * author: Example Author\n", "").replace(
            " * created: 2026-07-01\n", ""
        ).replace(" * last-modified-by: Example Maintainer\n", "").replace(
            " * last-modified: 2026-07-22\n", ""
        )
        item = parse_source_text(without_claims, "src/cli/cmd_sample.cpp", history={
            "author": "First Author",
            "created_date": "2025-01-02",
            "last_modified_by": "Latest Author",
            "last_modified_date": "2026-07-22",
        })
        self.assertEqual("First Author", item.author)
        self.assertEqual("git-history", item.metadata_provenance["author"])
        self.assertEqual("2025-01-02", item.date)
        self.assertEqual("Latest Author", item.last_modified_by)
        self.assertEqual("not-checked", item.working_tree_state)

    def test_reports_include_home_and_object(self) -> None:
        item = parse_source_text(SAMPLE, "src/cli/cmd_sample.cpp")
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = write_reports([item], Path(temp_dir))
            self.assertEqual({"MATCH": 1}, summary["location_status"])
            report = (Path(temp_dir) / "location_contract_report.csv").read_text(
                encoding="utf-8-sig"
            )
            self.assertIn("src/cli", report)
            self.assertTrue((Path(temp_dir) / "source_objects.jsonl").is_file())

    def test_location_ledger_tracks_move_without_changing_identity(self) -> None:
        first = parse_source_text(SAMPLE, "src/cli/cmd_sample.cpp")
        moved = parse_source_text(SAMPLE, "src/runtime/cmd_sample.cpp")
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            self.assertEqual(1, write_reports([first], output)["location_events_appended"])
            self.assertEqual(0, write_reports([first], output)["location_events_appended"])
            self.assertEqual(1, write_reports([moved], output)["location_events_appended"])
            events = [
                json.loads(line)
                for line in (output / "source_location_ledger.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(first.source_id, moved.source_id)
            self.assertEqual("src/cli/cmd_sample.cpp", events[-1]["previous_path"])
            self.assertEqual("src/runtime/cmd_sample.cpp", events[-1]["path"])


if __name__ == "__main__":
    unittest.main()
