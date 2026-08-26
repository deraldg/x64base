from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "audit_contracts.py"
SPEC = importlib.util.spec_from_file_location("audit_contracts", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class AuditContractsTests(unittest.TestCase):
    def test_file_layer_helper_is_exempt_from_usage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, "include/dotref.hpp", '{"REAL", "TOPIC", "text", true}\n')
            write(
                root,
                "src/cli/cmd_helper.cpp",
                "// @dottalk.file v1\n// layer: helper\n\nvoid helper() {}\n",
            )
            result = MOD.audit(root)
            self.assertIsNotNone(result)
            self.assertEqual(["src/cli/cmd_helper.cpp"], result["helpers"])
            self.assertEqual([], result["no_usage"])

    def test_command_layer_without_usage_remains_a_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, "include/dotref.hpp", '{"REAL", "TOPIC", "text", true}\n')
            write(
                root,
                "src/cli/cmd_real.cpp",
                "// @dottalk.file v1\n// layer: command\n\nvoid cmd_REAL() {}\n",
            )
            result = MOD.audit(root)
            self.assertIsNotNone(result)
            self.assertEqual(["src/cli/cmd_real.cpp"], result["no_usage"])
            self.assertEqual([], result["helpers"])

    def test_legacy_usage_helper_and_unregistered_command_stay_separate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, "include/dotref.hpp", '{"REAL", "TOPIC", "text", true}\n')
            write(
                root,
                "src/cli/cmd_legacy.cpp",
                "// @dottalk.file v1\n// layer: command\n\n"
                "// @dottalk.usage v1\n// status: implementation-helper\n\nvoid helper() {}\n",
            )
            write(
                root,
                "src/cli/cmd_missing.cpp",
                "// @dottalk.file v1\n// layer: command\n\n"
                "// @dottalk.usage v1\n// command: MISSING\n\nvoid cmd_MISSING() {}\n",
            )
            result = MOD.audit(root)
            self.assertIsNotNone(result)
            self.assertEqual(["src/cli/cmd_legacy.cpp"], result["helpers"])
            self.assertEqual(
                [("src/cli/cmd_missing.cpp", "MISSING")], result["unregistered"]
            )


if __name__ == "__main__":
    unittest.main()
