from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/build_dotref_migration_closure_v1.py"
SPEC = importlib.util.spec_from_file_location("build_dotref_migration_closure_v1", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class DotrefMigrationClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.commands = {
            "FOO": {"HANDLER": "cmd_FOO", "SRC_FILE": "src/cmd_foo.cpp"},
            "SET": {"HANDLER": "cmd_SET", "SRC_FILE": "src/cmd_set.cpp"},
        }

    def test_resolves_all_four_entity_shapes(self) -> None:
        scope, aliases, report = MOD.resolve_members(
            ["FOO", "F", "SET CASE", "STU_FN"],
            self.commands,
            {"SETCASE": {"PARENT": "SET", "SRC_FILE": "src/cmd_set.cpp"}},
            {"F": [MOD.Evidence("FOO", "SHORTCUT_RESOLVER", "src/shortcut.hpp", "SHORTCUT")]},
            {"STU_FN": MOD.Evidence("STU_FN", "EXT_FUNCTION_SOURCE", "src/ext/fn.cpp", "FUNCTION")},
            {"FOO": "cmd_FOO"},
            {},
        )
        self.assertEqual(["COMMAND", "ALIAS", "SUBCOMMAND", "FUNCTION"], [row["ENT_KIND"] for row in scope])
        self.assertEqual("FOO", aliases[0]["CAN_NAME"])
        self.assertFalse(any(row["BLOCKING"] == "T" for row in report))

    def test_same_handler_resolves_registered_compatibility_name(self) -> None:
        scope, aliases, report = MOD.resolve_members(
            ["FOO OLD"], self.commands, {}, {}, {},
            {"FOO OLD": "cmd_FOO"}, {},
        )
        self.assertEqual("ALIAS", scope[0]["ENT_KIND"])
        self.assertEqual("FOO", aliases[0]["CAN_NAME"])
        self.assertEqual("REGISTRY_HANDLER_EQUIVALENCE", report[0]["SRC_AUTH"])

    def test_ambiguous_alias_target_blocks(self) -> None:
        scope, aliases, report = MOD.resolve_members(
            ["OLD"], self.commands, {},
            {"OLD": [
                MOD.Evidence("FOO", "A", "a"),
                MOD.Evidence("SET", "B", "b"),
            ]},
            {}, {}, {},
        )
        self.assertEqual([], scope)
        self.assertEqual([], aliases)
        self.assertEqual("T", report[0]["BLOCKING"])

    def test_unresolved_member_blocks_instead_of_carrying(self) -> None:
        scope, aliases, report = MOD.resolve_members(
            ["PHANTOM"], self.commands, {}, {}, {}, {}, {},
        )
        self.assertEqual([], scope)
        self.assertEqual([], aliases)
        self.assertEqual("UNRESOLVED_HEADER_MEMBER", report[0]["CLASSIFICATION"])


if __name__ == "__main__":
    unittest.main()
