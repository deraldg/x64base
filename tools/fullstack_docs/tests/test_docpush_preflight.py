from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "docpush_preflight.py"
SPEC = importlib.util.spec_from_file_location("docpush_preflight", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class DocpushPreflightTests(unittest.TestCase):
    def test_contract_summary_is_structured(self) -> None:
        summary = MOD.contract_audit_summary(
            "header\nSUMMARY file_missing=0 usage_missing=1 "
            "unregistered=2 helpers=10\nfooter\n"
        )
        self.assertEqual(
            {
                "file_missing": 0,
                "usage_missing": 1,
                "unregistered": 2,
                "helpers": 10,
            },
            summary,
        )

    def test_missing_summary_is_not_mistaken_for_clean(self) -> None:
        self.assertIsNone(MOD.contract_audit_summary("audit failed before summary\n"))


if __name__ == "__main__":
    unittest.main()
