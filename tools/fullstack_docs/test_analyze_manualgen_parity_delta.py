from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("analyze_manualgen_parity_delta.py")
SPEC = importlib.util.spec_from_file_location("analyze_manualgen_parity_delta", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class GeneratedManualMetadataTests(unittest.TestCase):
    def test_harvest_provenance_headers_are_not_section_content(self) -> None:
        self.assertTrue(MODULE.is_generated_header_line("<!-- harvest_workspace: evidence/run -->"))
        self.assertTrue(MODULE.is_generated_header_line("<!-- harvest_selection_mode: explicit -->"))

    def test_section_heading_is_content(self) -> None:
        self.assertFalse(MODULE.is_generated_header_line("# Developer Manual"))


if __name__ == "__main__":
    unittest.main()
