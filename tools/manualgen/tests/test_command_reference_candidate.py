from __future__ import annotations

import sys
import unittest
from pathlib import Path


MANUALGEN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MANUALGEN_ROOT))

from manualgen_lib.command_reference_candidate import (  # noqa: E402
    _deduplicate_lines,
    _extract_command_links,
    _line_inclusion,
    _normal_identity,
    _resolve_topic,
    _shift_markdown_headings,
)
from manualgen_lib.command_reference_review_book import _hash_status  # noqa: E402
from manualgen_lib.publication_structure_candidate import build_structure_preview  # noqa: E402
from manualgen_lib.gate4_acceptance import (  # noqa: E402
    rewrite_reader_command_links,
    rewrite_status_source,
)


class CommandReferenceCandidateTests(unittest.TestCase):
    def test_extract_links_collapses_repeated_destinations(self) -> None:
        text = "[APPEND](../../command_reference_v1/commands/append.md) and [APPEND](../../command_reference_v1/commands/append.md)"
        rows = _extract_command_links(text)
        self.assertEqual(1, len(rows))
        self.assertEqual(2, rows[0]["occurrences"])

    def test_identity_treats_underscore_and_space_as_equivalent(self) -> None:
        self.assertEqual(_normal_identity("REL_ENUM"), _normal_identity("REL ENUM"))

    def test_topic_resolution_prefers_dot_over_fox(self) -> None:
        topic, rule, count = _resolve_topic(
            "ASCII",
            "ascii",
            [
                {"TOPICKEY": "FOX|ASCII", "CATALOG": "FOX", "TOPIC": "ASCII"},
                {"TOPICKEY": "DOT|ASCII", "CATALOG": "DOT", "TOPIC": "ASCII"},
            ],
        )
        self.assertEqual("DOT|ASCII", topic["TOPICKEY"])
        self.assertEqual("EXACT_LABEL_OR_SLUG_PREFERRED_CATALOG", rule)
        self.assertEqual(2, count)

    def test_local_paths_and_source_facts_are_excluded(self) -> None:
        self.assertEqual((False, "EXCLUDE_LOCAL_PATH_FROM_PUBLIC_BODY"), _line_inclusion({"KIND": "NOTE", "TEXT": "D:/code/ccode/source.cpp:7"}))
        self.assertEqual((False, "EXCLUDE_SOURCE_FACT_FROM_PUBLIC_BODY"), _line_inclusion({"KIND": "SOURCE_FACT", "TEXT": "handler"}))

    def test_contract_envelope_and_source_include_are_not_public_prose(self) -> None:
        self.assertEqual(
            (False, "EXCLUDE_CONTRACT_ENVELOPE_FROM_PUBLIC_BODY"),
            _line_inclusion({"KIND": "USAGE", "SOURCE": "USAGE_CONTRACT", "NAME": "USAGE_CONTRACT", "TEXT": "APPEND usage contract"}),
        )
        self.assertEqual(
            (False, "EXCLUDE_SOURCE_INCLUDE_FROM_PUBLIC_BODY"),
            _line_inclusion({"KIND": "RELATED", "TEXT": "include <cctype>"}),
        )

    def test_deduplication_prefers_curated_evidence(self) -> None:
        rows = [
            {"LINEID": "2", "KIND": "NOTE", "CONFID": "AUTHORITATIVE", "TEXT": "Same text"},
            {"LINEID": "1", "KIND": "NOTE", "CONFID": "CURATED", "TEXT": "Same text"},
        ]
        selected, dispositions = _deduplicate_lines(rows)
        self.assertEqual("1", selected[0]["LINEID"])
        self.assertEqual("EXCLUDE_DUPLICATE_PUBLIC_TEXT", dispositions["2"])

    def test_combined_book_shifts_page_headings_under_book_title(self) -> None:
        self.assertEqual("## APPEND\n\n### Syntax\n", _shift_markdown_headings("# APPEND\n\n## Syntax\n"))

    def test_review_book_accepts_only_proven_newline_equivalence(self) -> None:
        import hashlib
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.md"
            path.write_bytes(b"# PAGE\n\nText\n")
            expected = hashlib.sha256(b"# PAGE\r\n\r\nText\r\n").hexdigest().upper()
            self.assertEqual("NEWLINE_EQUIVALENT", _hash_status(path, expected))
            path.write_bytes(b"# PAGE\n\nChanged\n")
            self.assertEqual("MISMATCH", _hash_status(path, expected))

    def test_structure_preview_balances_markers_and_preserves_status_history(self) -> None:
        source = "\r\n".join([
            "<!-- BEGIN SECTION: sections\\one.md -->",
            "# One",
            "Status: DRAFT / REVIEW_REQUIRED",
            "",
            "---",
            "",
            "<!-- BEGIN SECTION: sections\\two.md -->",
            "# Two",
            "<!-- END SECTION: sections\\two.md -->",
            "",
        ])
        candidate, markers, statuses, findings = build_structure_preview(source)
        self.assertEqual(1, len(markers))
        self.assertEqual(1, len(statuses))
        self.assertEqual([], findings)
        self.assertIn("<!-- END SECTION: sections\\one.md -->\r\n\r\n---", candidate)
        self.assertIn("<!-- HISTORICAL STATUS: DRAFT / REVIEW_REQUIRED -->", candidate)
        self.assertIn("Status: REVIEWED_FOR_PUBLICATION", candidate)

    def test_gate4_status_rewrite_is_exact_and_preserves_history(self) -> None:
        source = "# One\r\n\r\nStatus: DRAFT / REVIEW_REQUIRED\r\n"
        candidate = rewrite_status_source(source, "DRAFT / REVIEW_REQUIRED")
        self.assertIn("<!-- HISTORICAL STATUS: DRAFT / REVIEW_REQUIRED -->\r\n", candidate)
        self.assertIn("Status: REVIEWED_FOR_PUBLICATION", candidate)
        with self.assertRaises(ValueError):
            rewrite_status_source(source, "SOME OTHER STATUS")

    def test_gate4_reader_link_rewrite_keeps_section_link_shape_separate(self) -> None:
        source = (
            "[APPEND](../../command_reference_v1/commands/append.md)\n"
            "[INDEX](command_reference_v1/commands/index.md)\n"
        )
        candidate, rewrites = rewrite_reader_command_links(source)
        self.assertEqual(1, rewrites)
        self.assertEqual(2, candidate.count("](command_reference_v1/commands/"))


if __name__ == "__main__":
    unittest.main()
