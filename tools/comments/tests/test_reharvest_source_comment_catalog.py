from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools/comments/reharvest_source_comment_catalog.py"
SPEC = importlib.util.spec_from_file_location("source_comment_reharvester", MODULE_PATH)
assert SPEC and SPEC.loader
REHARVEST = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REHARVEST
SPEC.loader.exec_module(REHARVEST)


class SourceCommentReharvesterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.maint = REHARVEST.harvest_file(REPO_ROOT, REPO_ROOT / "src/cli/cmd_maint.cpp")
        cls.if_command = REHARVEST.harvest_file(REPO_ROOT, REPO_ROOT / "src/cli/cmd_if.cpp")
        cls.ddict = REHARVEST.harvest_file(REPO_ROOT, REPO_ROOT / "src/cli/cmd_ddict.cpp")

    def test_maint_structured_fields_are_preserved(self) -> None:
        fields = self.maint.usage_fields
        self.assertEqual("maintenance", fields["category"])
        self.assertEqual("experimental", fields["status"])
        self.assertEqual("none", fields["mutates"])
        self.assertIn("MAINT AI GATES", fields["usage"])
        self.assertIn("read-only", fields["notes"])
        self.assertEqual("BBOX; CMDHELP; DDICT; MANUAL", fields["related"])

    def test_only_nested_usage_block_emits_semantic_row(self) -> None:
        leading = REHARVEST.usage_row_for_block(self.maint, "LEADING_HEADER", 1, 1, 1, "ACTIVE")
        nested = REHARVEST.usage_row_for_block(self.maint, "DOTTALK_USAGE", 1, 2, 1, "ACTIVE")
        self.assertIsNone(leading)
        self.assertIsNotNone(nested)
        assert nested is not None
        self.assertEqual("2", nested["BLOCKID"])
        self.assertEqual("maintenance", nested["CATEGORY"])
        self.assertTrue(nested["USAGE"])

    def test_multiline_sections_stop_at_next_field(self) -> None:
        lines = [
            "@dottalk.usage v1",
            "command: SAMPLE",
            "summary:",
            "first line",
            "second line",
            "usage:",
            "SAMPLE",
            "SAMPLE USAGE",
            "note: one",
            "note: two",
            "@dottalk.end",
            "ignored",
        ]
        fields = REHARVEST.parse_usage_fields(lines, 1)
        self.assertEqual("first line second line", fields["summary"])
        self.assertEqual("SAMPLE\nSAMPLE USAGE", fields["usage"])
        self.assertEqual("one\ntwo", fields["notes"])

    def test_mid_file_usage_contract_is_harvested_separately(self) -> None:
        self.assertEqual(["IF", "ENDIF"], [
            contract.command for contract in self.if_command.usage_contracts
        ])
        endif = self.if_command.usage_contracts[1]
        self.assertEqual(154, endif.start_line)
        self.assertGreaterEqual(endif.end_line, endif.start_line)
        row = REHARVEST.usage_row_for_contract(endif, 2, 3, 1, "ACTIVE")
        self.assertEqual("ENDIF", row["COMMAND"])
        self.assertEqual("syntax-command", row["CATEGORY"])

    def test_adjacent_usage_contracts_are_not_merged(self) -> None:
        lines = [
            "// @dottalk.usage v1",
            "// owner: UI|ONE",
            "// command: ONE",
            "// status: supported",
            "// usage:",
            "//   ONE",
            "//",
            "// @dottalk.usage v1",
            "// owner: UI|TWO",
            "// command: TWO",
            "// status: developer",
            "// usage:",
            "//   TWO",
        ]
        contracts = REHARVEST.extract_usage_contracts(lines)
        self.assertEqual(["ONE", "TWO"], [contract.command for contract in contracts])
        self.assertEqual("supported", contracts[0].fields["status"])
        self.assertEqual("developer", contracts[1].fields["status"])

    def test_leading_block_comment_contract_is_preserved(self) -> None:
        self.assertEqual(1, len(self.ddict.usage_contracts))
        self.assertEqual("DDICT", self.ddict.usage_contracts[0].command)
        self.assertTrue(self.ddict.usage_contracts[0].complete)


if __name__ == "__main__":
    unittest.main()
