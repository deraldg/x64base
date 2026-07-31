from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools/selfdoc/validate_maint_documentation_parity.py"
SPEC = importlib.util.spec_from_file_location("maint_documentation_parity", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class MaintDocumentationParityTests(unittest.TestCase):
    def test_current_maint_surfaces_pass(self) -> None:
        self.assertEqual([], VALIDATOR.validate(REPO_ROOT))


if __name__ == "__main__":
    unittest.main()
