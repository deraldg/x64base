from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from generate_dual_schema_contract import DEFAULT_SQLITE, generate, sha256  # noqa: E402


class DualSchemaContractTests(unittest.TestCase):
    def test_complete_cascade_contract_is_deterministic_and_read_only(self) -> None:
        before = sha256(DEFAULT_SQLITE)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            contract = generate(DEFAULT_SQLITE, output)
            first = (output / "dual_schema_contract.json").read_bytes()
            generate(DEFAULT_SQLITE, output)
            second = (output / "dual_schema_contract.json").read_bytes()

            self.assertEqual(first, second)
            self.assertEqual(contract["counts"]["tables"], 34)
            self.assertEqual(contract["counts"]["views"], 9)
            self.assertEqual(contract["counts"]["rows_in_tables"], 330)
            self.assertEqual(contract["counts"]["foreign_key_field_edges"], 58)
            self.assertEqual(contract["counts"]["x64base_physical_tables_planned"], 43)
            self.assertEqual(len(list((output / "views").glob("*.csv"))), 9)
            self.assertEqual(len(list((output / "schemas").glob("*.schema.json"))), 43)

            loaded = json.loads(first)
            self.assertEqual(len(loaded["objects"]), 43)
            for obj in loaded["objects"]:
                schema = json.loads(
                    (output / "schemas" / f"{obj['name']}.schema.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(
                    [field["name"] for field in schema["fields"]],
                    [column["name"] for column in obj["columns"]],
                    obj["name"],
                )
            build = (output / "build_x64base_mirror.dts").read_text(encoding="utf-8")
            self.assertEqual(build.count("DDL CREATE DBF X64 "), 43)
            self.assertEqual(build.count("DDL VALIDATE "), 43)
            # System-bundle layout (owner ruling 2026-08-10): the sealed package
            # lives under systems/cascade_erp/sqlite/ -- tables import from its
            # data/, views from its x64base_mirror/views/.
            self.assertEqual(build.count("IMPORT systems/cascade_erp/sqlite/"), 43)

            gl_accounts = json.loads(
                (output / "schemas" / "GL_Accounts.schema.json").read_text(encoding="utf-8")
            )
            fields = {field["name"]: field for field in gl_accounts["fields"]}
            self.assertEqual(fields["Account_Code"]["type"], "C")
            self.assertEqual(fields["Parent_ID"]["type"], "N")

        self.assertEqual(before, sha256(DEFAULT_SQLITE))


if __name__ == "__main__":
    unittest.main()
