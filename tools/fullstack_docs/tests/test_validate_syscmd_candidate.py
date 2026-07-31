from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/validate_syscmd_candidate.py"
SPEC = importlib.util.spec_from_file_location("validate_syscmd_candidate", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def row(**updates: str) -> dict[str, str]:
    value = {
        "CMD_ID": "CMD_SET_ORDER",
        "CAN_NAME": "SET ORDER",
        "TYPE": "command",
        "VIS": "public",
        "HANDLER": "cmd_SETORDER",
        "ACTIVE": "true",
    }
    value.update(updates)
    return value


class SysCmdCandidateValidatorTests(unittest.TestCase):
    def test_valid_row(self) -> None:
        self.assertEqual([], MOD.validate_rows([row()]))

    def test_duplicate_identity_fails(self) -> None:
        findings = MOD.validate_rows([row(), row()])
        self.assertIn("CMD_ID_DUPLICATE:CMD_SET_ORDER:2", findings)
        self.assertIn("CAN_NAME_DUPLICATE:SET ORDER:2", findings)

    def test_projection_and_allowed_values_fail(self) -> None:
        findings = MOD.validate_rows([row(CMD_ID="CMD_SETORDER", TYPE="topic", VIS="hidden")])
        self.assertTrue(any(item.startswith("ROW_2:CMD_ID_PROJECTION") for item in findings))
        self.assertIn("ROW_2:TYPE_VALUE:topic", findings)
        self.assertIn("ROW_2:VIS_VALUE:hidden", findings)

    def test_field_length_fails(self) -> None:
        findings = MOD.validate_rows([row(HANDLER="x" * 97)])
        self.assertIn("ROW_2:FIELD_LENGTH:HANDLER:97>96", findings)

    def test_commented_registration_is_not_backing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src/example.cpp").write_text(
                '// registry().add("SET ORDER", handler);\n', encoding="utf-8"
            )
            findings = MOD.validate_rows([row()], root)
        self.assertIn("ROW_2:STATIC_REGISTRY_BACKING_MISSING:SET ORDER", findings)


if __name__ == "__main__":
    unittest.main()
