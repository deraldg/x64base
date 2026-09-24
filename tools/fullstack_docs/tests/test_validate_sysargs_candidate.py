from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/validate_sysargs_candidate.py"
SPEC = importlib.util.spec_from_file_location("validate_sysargs_candidate", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def row(**updates: str) -> dict[str, str]:
    value = {
        "ARG_ID": "ARG_SET_PATH",
        "OWNER_KND": "command",
        "OWNER_NAM": "SET",
        "ARG_NAME": "PATH",
        "DEF_LOCALE": "en-US",
        "REGION_ID": "GLOBAL",
        "ARG_KIND": "keyword",
        "VAL_SHAPE": "literal",
        "REQUIRED": "false",
        "REPEAT": "false",
        "SRC_AUTH": "usage_contract_v1",
        "SRC_FILE": "src/cli/cmd_set.cpp",
        "ACTIVE": "true",
        "VER_AT": "",
        "NOTES": "usage=SET PATH <slot> <path>",
    }
    value.update(updates)
    return value


class SysArgsCandidateValidatorTests(unittest.TestCase):
    def test_valid_row(self) -> None:
        self.assertEqual([], MOD.validate_rows([row()]))

    def test_keyword_and_placeholder_collide_on_one_id(self) -> None:
        """THE FINDING. Same word, two roles, one id -- and the rows differ.

        This is the real ARG_SET_PATH pair from the 2026-09-24 candidate. The
        check exists to make this loud; do not relax it to make the suite green.
        """
        keyword = row()
        placeholder = row(
            ARG_KIND="placeholder",
            VAL_SHAPE="path",
            NOTES="usage=SET DEVICE TO FILE <path> ; usage=SET PATH <slot> <path>",
        )
        self.assertNotEqual(keyword, placeholder)
        findings = MOD.validate_rows([keyword, placeholder])
        self.assertEqual(["ARG_ID_DUPLICATE:ARG_SET_PATH:2"], findings)

    def test_projection_and_reserved_values_fail(self) -> None:
        findings = MOD.validate_rows(
            [row(ARG_ID="ARG_SETPATH", ARG_KIND="flag", OWNER_KND="function")]
        )
        self.assertTrue(any(item.startswith("ROW_2:ARG_ID_PROJECTION") for item in findings))
        self.assertIn("ROW_2:ARG_KIND_VALUE:flag", findings)
        self.assertIn("ROW_2:OWNER_KND_VALUE:function", findings)

    def test_shape_must_agree_with_kind(self) -> None:
        self.assertIn("ROW_2:KEYWORD_SHAPE:path", MOD.validate_rows([row(VAL_SHAPE="path")]))
        self.assertIn(
            "ROW_2:PLACEHOLDER_SHAPE_LITERAL",
            MOD.validate_rows([row(ARG_KIND="placeholder")]),
        )

    def test_booleans_and_authority(self) -> None:
        findings = MOD.validate_rows([row(REQUIRED="maybe", SRC_AUTH="guessed")])
        self.assertIn("ROW_2:REQUIRED_NOT_BOOLEAN:maybe", findings)
        self.assertIn("ROW_2:SRC_AUTH_VALUE:guessed", findings)

    def test_missing_source_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            findings = MOD.validate_rows([row()], Path(temp))
        self.assertIn("ROW_2:SRC_FILE_MISSING:src/cli/cmd_set.cpp", findings)

    def test_owner_without_a_syscmd_row_fails(self) -> None:
        findings = MOD.validate_rows([row()], None, {"USE", "LIST"})
        self.assertIn("ROW_2:OWNER_NOT_IN_SYSCMD:SET", findings)

    def test_owner_grouping_is_checked(self) -> None:
        findings = MOD.validate_rows(
            [row(OWNER_NAM="USE", ARG_ID="ARG_USE_TABLE", ARG_NAME="TABLE"), row()]
        )
        self.assertIn("OWNER_NAM_ORDER_NOT_GROUPED", findings)


if __name__ == "__main__":
    unittest.main()
