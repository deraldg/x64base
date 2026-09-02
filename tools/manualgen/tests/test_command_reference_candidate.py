from __future__ import annotations

import sys
import unittest
from pathlib import Path


MANUALGEN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MANUALGEN_ROOT))

from manualgen_lib.command_reference_candidate import (  # noqa: E402
    PROSE_KINDS,
    _deduplicate_lines,
    _extract_command_links,
    _line_inclusion,
    _normal_identity,
    _WRAP_BAND_MIN,
    _reassemble_parts,
    _rejoin_wrapped_prose,
    _resolve_topic,
    _shift_markdown_headings,
)
from manualgen_lib.command_reference_review_book import _hash_status  # noqa: E402
from manualgen_lib.publication_structure_candidate import build_structure_preview  # noqa: E402
from manualgen_lib.gate4_acceptance import (  # noqa: E402
    command_reference_totals,
    rewrite_reader_command_links,
    rewrite_status_source,
)
from manualgen_lib.gate4_acceptance_apply import (  # noqa: E402
    validate_gate4_authorization,
)


class RejoinWrappedProseTests(unittest.TestCase):
    """HELP_LINE holds ONE ROW PER SOURCE LINE, so a wrapped contract comment
    arrives as several rows with nothing marking paragraph membership. These
    cases pin the rejoin rule, which is deliberately CONSERVATIVE: it must
    under-join rather than weld two separate notes into one false sentence.

    Written 2026-09-02. The run record and commit message for the fix both said
    "eight unit cases now cover it" while NO test referenced the function --
    caught by grepping for the symbol before a second Gate 4 cycle. The claim is
    now true. A test asserted in prose is not a test.
    """

    def test_lowercase_continuation_joins(self) -> None:
        head = "AREA51 is a developer/debug status probe, not a member of the AREA family,"
        self.assertGreaterEqual(len(head), _WRAP_BAND_MIN)
        self.assertEqual(
            _rejoin_wrapped_prose([head, "and the status field above says so."]),
            [f"{head} and the status field above says so."],
        )

    def test_terminated_sentence_does_not_absorb_the_next(self) -> None:
        self.assertEqual(
            _rejoin_wrapped_prose(["First note ends here.", "second note starts here"]),
            ["First note ends here.", "second note starts here"],
        )

    def test_every_terminator_blocks_the_join(self) -> None:
        for end in ".!?:;":
            with self.subTest(terminator=end):
                self.assertEqual(
                    _rejoin_wrapped_prose([f"stops{end}", "and continues"]),
                    [f"stops{end}", "and continues"],
                )

    def test_digit_continuation_joins(self) -> None:
        """The real area51 wrap continues onto a date. A first draft tested only
        islower() and left this split -- the failing test is why digits are in
        the rule at all."""
        head = "and `status: developer` above says so. It read `supported` until"
        self.assertGreaterEqual(len(head), _WRAP_BAND_MIN)
        self.assertEqual(
            _rejoin_wrapped_prose([head, "2026-08-30 while this paragraph said otherwise."]),
            [f"{head} 2026-08-30 while this paragraph said otherwise."],
        )

    def test_numbered_list_marker_is_not_a_continuation(self) -> None:
        self.assertEqual(
            _rejoin_wrapped_prose(["Do these in order", "1. first", "2) second"]),
            ["Do these in order", "1. first", "2) second"],
        )

    def test_uppercase_continuation_stays_split_by_design(self) -> None:
        """Documented UNDER-join. `DBAREAS, WA, WAMREPORT` really does continue
        the previous row, but nothing distinguishes it from a new sentence, and
        guessing here would weld unrelated notes together elsewhere."""
        self.assertEqual(
            _rejoin_wrapped_prose(["a crowded namespace -- AREA, DBAREA,", "DBAREAS, WA, WAMREPORT."]),
            ["a crowded namespace -- AREA, DBAREA,", "DBAREAS, WA, WAMREPORT."],
        )

    def test_three_rows_fold_into_one_paragraph(self) -> None:
        rows = [
            "Order/tag reporting is best-effort; a throwing order-state query is",
            "swallowed and the remaining lines still print, because a diagnostic that",
            "hides the rest of its own output is worse than a missing field.",
        ]
        self.assertEqual(_rejoin_wrapped_prose(rows), [" ".join(rows)])

    def test_empty_and_single_inputs_are_safe(self) -> None:
        self.assertEqual(_rejoin_wrapped_prose([]), [])
        self.assertEqual(_rejoin_wrapped_prose(["alone"]), ["alone"])
        self.assertEqual(_rejoin_wrapped_prose(["", "lower"]), ["", "lower"])

    def test_part_rows_reassemble_with_no_separator(self) -> None:
        """The producer splits a long logical line into 240-byte PART_NO rows and
        says the reader reassembles by LINE_NO + PART_NO. Parts join with NOTHING:
        the split is at a byte boundary, mid-token."""
        rows = [
            {"TOPICKEY": "DOT|CANARY", "KIND": "SUMMARY", "LINE_NO": "1", "PART_NO": "1",
             "TEXT": "cmd_CATALOGCANARY is the handler, not the comm"},
            {"TOPICKEY": "DOT|CANARY", "KIND": "SUMMARY", "LINE_NO": "1", "PART_NO": "2",
             "TEXT": "and name."},
        ]
        out = _reassemble_parts(rows)
        self.assertEqual(1, len(out))
        self.assertTrue(out[0]["TEXT"].endswith("not the command name."))

    def test_three_part_spill_reassembles_in_order(self) -> None:
        rows = [{"TOPICKEY": "DOT|VDISK", "KIND": "SUMMARY", "LINE_NO": "1",
                 "PART_NO": str(i + 1), "TEXT": t}
                for i, t in enumerate(["a" * 3, "b" * 3, "c" * 3])]
        self.assertEqual("aaabbbccc", _reassemble_parts(rows)[0]["TEXT"])

    def test_separate_logical_lines_are_not_merged(self) -> None:
        """Different LINE_NO means different logical lines, however adjacent."""
        rows = [
            {"TOPICKEY": "DOT|X", "KIND": "NOTE", "LINE_NO": "1", "PART_NO": "1", "TEXT": "one"},
            {"TOPICKEY": "DOT|X", "KIND": "NOTE", "LINE_NO": "2", "PART_NO": "1", "TEXT": "two"},
        ]
        self.assertEqual(2, len(_reassemble_parts(rows)))

    def test_short_lines_are_never_joined(self) -> None:
        """A line that stops at 13 characters did not run out of room -- the
        author ended it. Without this floor the rule welded whole lists:
        model.md 'tables'/'records'/'fields', buffering.md 'working state'/
        'persisted state'. Caught in a Gate 4 plan review, before apply."""
        self.assertEqual(
            _rejoin_wrapped_prose(["working state", "persisted state"]),
            ["working state", "persisted state"],
        )
        self.assertEqual(
            _rejoin_wrapped_prose(["tables", "records", "fields", "indexes"]),
            ["tables", "records", "fields", "indexes"],
        )

    def test_wrap_band_floor_is_the_measured_cliff(self) -> None:
        """60 is where the join-length distribution jumps by an order of
        magnitude: 13 joins in 40-59, 116 in 60-69, 577 in 70-79."""
        self.assertEqual(_WRAP_BAND_MIN, 60)
        short = "x" * (_WRAP_BAND_MIN - 1)
        self.assertEqual(_rejoin_wrapped_prose([short, "continues"]), [short, "continues"])
        long_enough = "x" * _WRAP_BAND_MIN
        self.assertEqual(_rejoin_wrapped_prose([long_enough, "continues"]),
                         [f"{long_enough} continues"])

    def test_line_oriented_kinds_are_excluded_from_the_rule(self) -> None:
        """USAGE shows 1954 apparent continuations and SYNTAX 1280, MORE than
        NOTE's 756, because they are indented command forms where a lowercase
        line is layout. Rejoining them would run a command form into the
        description beneath it, so they must stay out of PROSE_KINDS."""
        self.assertEqual(PROSE_KINDS, frozenset({"NOTE", "WARNING", "HINT", "DEPRECATION"}))
        for kind in ("SYNTAX", "USAGE", "ARGUMENT", "EXAMPLE"):
            with self.subTest(kind=kind):
                self.assertNotIn(kind, PROSE_KINDS)


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

    def test_structure_preview_is_idempotent_after_acceptance(self) -> None:
        source = "\r\n".join([
            "<!-- BEGIN SECTION: sections\\one.md -->",
            "# One",
            "<!-- HISTORICAL STATUS: DRAFT / REVIEW_REQUIRED -->",
            "Status: REVIEWED_FOR_PUBLICATION",
            "<!-- END SECTION: sections\\one.md -->",
            "",
        ])
        candidate, markers, statuses, findings = build_structure_preview(source)
        self.assertEqual(source, candidate)
        self.assertEqual([], markers)
        self.assertEqual([], statuses)
        self.assertEqual([], findings)

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

    def test_gate4_authorization_uses_plan_row_count(self) -> None:
        payload = {
            "schema": "dottalk.manualgen.gate4_apply_authorization.v1",
            "decision": "AUTHORIZED_FOR_CANONICAL_APPLY",
            "plan_run": "MANRUN-20260723T000000Z-00000000",
            "plan_manifest_sha256": "A",
            "mutation_ledger_sha256": "B",
            "mutation_rows_authorized": 168,
            "required_interpreter": "Python 3.12",
            "apply_time_finalization_targets": [
                "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json",
                "docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json",
                "docs/manuals/developer/manualgen/accepted_artifacts/command_reference_artifact_v1.json",
            ],
        }
        self.assertEqual(
            [],
            validate_gate4_authorization(
                payload,
                "MANRUN-20260723T000000Z-00000000",
                "A",
                "B",
                168,
            ),
        )

    def test_gate4_refresh_preserves_supplemental_acceptance_totals(self) -> None:
        totals = command_reference_totals(
            {
                "supplemental_standalone_pages": 19,
                "supplemental_lineage_rows": 855,
            },
            164,
            3064,
        )
        self.assertEqual(183, totals["total_pages"])
        self.assertEqual(3919, totals["total_lineage_rows"])


if __name__ == "__main__":
    unittest.main()
