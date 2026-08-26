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


if __name__ == "__main__":
    unittest.main()
