from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "emit_dotref_m3d_candidate_v1.py"
SPEC = importlib.util.spec_from_file_location("emit_dotref_m3d_candidate_v1", MODULE)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


def policy(supported: bool) -> dict[str, str]:
    return {
        "SUPPORTED": "T" if supported else "F",
        "MATURITY": "stable" if supported else "review",
        "AUDIENCE": "public" if supported else "internal",
    }


class DotrefM3dEmitterTests(unittest.TestCase):
    def test_stable_id_is_case_and_space_normalized(self) -> None:
        self.assertEqual(
            M.stable_id("dot", "command", " help "),
            M.stable_id("DOT", "COMMAND", "HELP"),
        )

    def test_alias_support_uses_approved_compatibility_mapping(self) -> None:
        scope = {"ENT_KIND": "ALIAS", "TARGET_NAME": "HELP", "NAME": "COMMANDSHELP"}
        status, row, authority = M.choose_support(
            scope, None, {}, {"compatibility-alias": policy(True)}
        )
        self.assertEqual("compatibility-alias", status)
        self.assertEqual("T", row["SUPPORTED"])
        self.assertEqual("APPROVED_ALIAS_POLICY", authority)

    def test_primary_contract_status_beats_auxiliary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            inventory = Path(td) / "inventory.json"
            inventory.write_text(
                '{"contracts":['
                '{"command":"HELP","status":"supported","file":"cmd_help.cpp"},'
                '{"command":"HELP","status":"implementation-helper","file":"cmd_help_grouped.cpp"}'
                ']}', encoding="utf-8"
            )
            statuses, audit = M.primary_contract_statuses(inventory)
        self.assertEqual({"HELP": "supported"}, statuses)
        self.assertTrue(any(row["DISPOSITION"] == "AUXILIARY_IGNORED" for row in audit))

    def test_unknown_support_status_fails_closed(self) -> None:
        scope = {"ENT_KIND": "COMMAND", "TARGET_NAME": "HELP", "NAME": "HELP"}
        with self.assertRaisesRegex(M.EmissionError, "UNKNOWN_SUPPORT_STATUS"):
            M.choose_support(scope, None, {"HELP": "invented"}, {"supported": policy(True)})

    def test_cpp_string_roundtrips_escapes(self) -> None:
        value = 'A "quoted" path C:\\tmp\nnext'
        encoded = M.cpp_string(value)
        self.assertTrue(encoded.startswith('"') and encoded.endswith('"'))
        self.assertIn('\\"quoted\\"', encoded)
        self.assertIn('C:\\\\tmp', encoded)
        self.assertIn('\\nnext', encoded)


if __name__ == "__main__":
    unittest.main()
