from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools" / "fullstack_docs" / "command_catalog_sync.py"
SPEC = importlib.util.spec_from_file_location("command_catalog_sync", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CommandCatalogAliasTests(unittest.TestCase):
    def test_aliases_cover_single_token_alias_and_spaced_router(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cli = root / "src" / "cli"
            cli.mkdir(parents=True)
            (cli / "shell_commands.cpp").write_text(
                '\n'.join(
                    [
                        'registry().add("APPGUI", [](DbArea& A, std::istringstream& S){ app_GUI(A,S); });',
                        'registry().add("GUI", [](DbArea& A, std::istringstream& S){ app_GUI(A,S); });',
                        'registry().add("BUILD", [](DbArea& A, std::istringstream& S){ cmd_BUILD(A,S); });',
                    ]
                ),
                encoding="utf-8",
            )
            (cli / "contracts.cpp").write_text(
                """// @dottalk.usage v1
// command: APPGUI
// aliases: GUI
// category: gui
// status: supported
// summary:
//   Launch the GUI.
int appgui;
// @dottalk.usage v1
// command: BUILDVECTORS
// aliases: BUILD VECTORS, BUILD INFO
// category: diagnostics
// status: supported
// summary:
//   Report build vectors.
int buildvectors;
""",
                encoding="utf-8",
            )
            blocks = MODULE.usage_blocks(root)
            self.assertIn(MODULE._norm("GUI"), blocks)
            self.assertIn(MODULE._norm("BUILD"), blocks)
            self.assertEqual("gui", blocks[MODULE._norm("GUI")]["category"])
            self.assertEqual("diagnostics", blocks[MODULE._norm("BUILD")]["category"])


class FunctionCatalogEmitTests(unittest.TestCase):
    def test_fn_emit_derives_details_counts_and_extension_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = root / "src" / "cli" / "expr"
            ext = root / "src" / "ext" / "fn"
            core.mkdir(parents=True)
            ext.mkdir(parents=True)
            (core / "function_catalog.cpp").write_text(
                '''FunctionDoc{
    "RTRIM",
    { "TRIM" },
    FunctionCategory::String,
    1, 1,
    "Trim trailing spaces.",
    {}, {}, {}, {}
},
FunctionDoc{
    "PADL",
    {},
    FunctionCategory::String,
    2, 3,
    "Pad on the left.",
    {}, {}, {}, {}
},
''',
                encoding="utf-8",
            )
            (ext / "sample.cpp").write_text(
                '''register_builtin_fn({
    "STU_UPPER",
    1, 1,
    &fn_STU_UPPER
});
''',
                encoding="utf-8",
            )
            out = root / "function-catalog.mdx"
            self.assertEqual(0, MODULE.fn_emit(root, out))
            text = out.read_text(encoding="utf-8")
            self.assertIn("`2` core documented expression functions", text)
            self.assertIn("plus `1` self-registering", text)
            self.assertIn("| `RTRIM` | TRIM | String | 1 | Trim trailing spaces. |", text)
            self.assertIn("| `PADL` |  | String | 2-3 | Pad on the left. |", text)
            self.assertIn("| `STU_UPPER` |  | Extension | 1 |", text)
            self.assertEqual(0, MODULE.fn_check(root, out))


if __name__ == "__main__":
    unittest.main()
