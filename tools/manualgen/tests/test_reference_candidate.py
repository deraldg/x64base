from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


MANUALGEN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MANUALGEN_ROOT))

from manualgen_lib.reference_candidate import (  # noqa: E402
    _classify_unassigned_line,
    _int_value,
    _render_text,
    _resolve_command_topic_key,
)
from manualgen_lib.curation import classify_line, classify_topic  # noqa: E402
from manualgen_lib.disposition import REVIEW_DISPOSITIONS, _section_group  # noqa: E402
from manualgen_lib.structural_reconciliation import STRUCTURAL_REVIEW_DISPOSITIONS, _choose_mapping, _slug  # noqa: E402
from manualgen_lib.section_delta import _parse_topic_blocks  # noqa: E402


DISPOSITION_EVIDENCE = (
    MANUALGEN_ROOT.parents[1]
    / "docs"
    / "manuals"
    / "developer"
    / "manualgen"
    / "generated"
    / "manualgen_disposition_candidates"
    / "MANRUN-20260717T230554Z-DB3F2DC8"
)


class ReferenceCandidateTests(unittest.TestCase):
    def test_render_text_preserves_multiline_content_safely(self) -> None:
        self.assertEqual("A&lt;B<br>C", _render_text("A<B\nC"))

    def test_padded_numeric_ids_sort_as_numbers(self) -> None:
        self.assertEqual(12, _int_value({"LINEID": "       12"}, "LINEID"))

    def test_fox_compact_set_resolves_only_to_existing_spaced_topic(self) -> None:
        resolved = _resolve_command_topic_key(
            {"CATALOG": "FOX", "COMMAND": "SETPATH", "CMDKEY": "FOX|SETPATH"},
            {"FOX|SET PATH"},
        )
        self.assertEqual(("FOX|SET PATH", "FOX_COMPACT_SET_TO_SPACED_TOPIC"), resolved)

    def test_blank_key_system_messages_are_global_evidence(self) -> None:
        classification = _classify_unassigned_line({"CATALOG": "SYSTEM", "SOURCE": "SHARED_MSG", "KIND": "MESSAGE"})
        self.assertEqual("GLOBAL_SHARED_MESSAGE", classification)

    def test_supported_dot_topic_routes_to_current_command_shelf(self) -> None:
        shelf, disposition = classify_topic({"CATALOG": "DOT", "STATUS": "supported"})
        self.assertEqual("01_dot_supported_commands", shelf)
        self.assertEqual("INCLUDE_COMMAND_REFERENCE_CANDIDATE", disposition)

    def test_internal_topic_is_not_public_by_default(self) -> None:
        shelf, disposition = classify_topic({"CATALOG": "INTERNAL", "STATUS": "pending"})
        self.assertEqual("07_developer_internal_topics", shelf)
        self.assertEqual("EXCLUDE_FROM_PUBLIC_MANUAL_BY_DEFAULT", disposition)

    def test_global_message_line_routes_to_system_shelf(self) -> None:
        shelf = classify_line({"TOPICKEY": "", "CATALOG": "SYSTEM", "SOURCE": "SHARED_MSG"}, {})
        self.assertEqual("08_system_message_catalog", shelf)

    def test_review_policy_covers_49_topics(self) -> None:
        self.assertEqual(49, len(REVIEW_DISPOSITIONS))

    def test_partial_help_topics_route_to_separate_section_group(self) -> None:
        group = _section_group({"CATALOG": "DOT"}, "INCLUDE_PARTIAL_HELP_REFERENCE")
        self.assertEqual("05_partial_help_reference", group)

    def test_structural_slug_matches_manual_section_convention(self) -> None:
        self.assertEqual("runtime_operation_invocation_and_automation", _slug("Runtime Operation, Invocation, and Automation"))

    def test_partial_help_mapping_cannot_enter_normal_section(self) -> None:
        mapping = _choose_mapping(
            {"catalog": "FOX", "topic": "DO", "section_group": "05_partial_help_reference"},
            {"DO": {"scripting_and_control_flow"}},
            {"scripting_and_control_flow": 1},
        )
        self.assertEqual("partial_help_reference", mapping["target_slug"])
        self.assertEqual("NEW_CANDIDATE_APPENDIX", mapping["target_kind"])

    def test_fox_topic_stays_inside_compatibility_boundary(self) -> None:
        mapping = _choose_mapping(
            {"catalog": "FOX", "topic": "BROWSE", "section_group": "02_fox_compatibility_reference"},
            {"BROWSE": {"navigation_browsing_and_search"}},
            {"navigation_browsing_and_search": 1},
        )
        self.assertEqual("legacy_and_compatibility_surfaces", mapping["target_slug"])

    def test_structural_review_policy_closes_thirteen_topics(self) -> None:
        self.assertEqual(13, len(STRUCTURAL_REVIEW_DISPOSITIONS))

    def test_exportfunctions_routes_to_function_reference(self) -> None:
        mapping = _choose_mapping(
            {"topic_key": "DOT|EXPORTFUNCTIONS", "catalog": "DOT", "topic": "EXPORTFUNCTIONS", "section_group": "01_developer_command_reference"},
            {},
            {},
        )
        self.assertEqual("functions_and_expression_helpers", mapping["target_slug"])
        self.assertEqual("RESOLVE_STRUCTURAL_REVIEW_TOPIC", mapping["delta_action"])

    def test_topic_block_parser_is_hermetic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            packet = Path(directory) / "01_fixture.md"
            packet.write_text(
                "# Fixture\n\n"
                "## Alpha\n\n- Key/status: `DOT|ALPHA`\n\nAlpha body.\n\n"
                "## Beta\n\n- Key/status: `FOX|BETA`\n\nBeta body.\n",
                encoding="utf-8",
            )
            blocks, duplicates = _parse_topic_blocks(Path(directory))
        self.assertEqual({"DOT|ALPHA", "FOX|BETA"}, set(blocks))
        self.assertIn("Alpha body.", blocks["DOT|ALPHA"])
        self.assertEqual([], duplicates)

    @unittest.skipUnless(
        DISPOSITION_EVIDENCE.exists(),
        "candidate-only disposition evidence is intentionally absent from the public projection",
    )
    def test_development_disposition_packets_expose_all_approved_topic_blocks(self) -> None:
        blocks, duplicates = _parse_topic_blocks(DISPOSITION_EVIDENCE)
        self.assertEqual(462, len(blocks))
        self.assertEqual([], duplicates)


if __name__ == "__main__":
    unittest.main()
