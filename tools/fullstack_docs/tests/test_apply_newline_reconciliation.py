from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/apply_newline_reconciliation.py"
SPEC = importlib.util.spec_from_file_location("apply_newline_reconciliation", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class NewlineReconciliationTests(unittest.TestCase):
    def test_crlf_restoration_preserves_normalized_content(self) -> None:
        source = b"one\ntwo\n"
        restored = MODULE.to_crlf(source)
        self.assertEqual(b"one\r\ntwo\r\n", restored)
        self.assertEqual(MODULE.normalized_lf(source), MODULE.normalized_lf(restored))

    def test_conversion_is_idempotent(self) -> None:
        source = b"one\r\ntwo\r\n"
        self.assertEqual(source, MODULE.to_crlf(source))

    def test_appendix_lf_bytes_restore_to_recorded_crlf_hash(self) -> None:
        source = b"# Partial HELP\n\nText\n"
        restored = MODULE.to_crlf(source)
        self.assertEqual(MODULE.normalized_lf(source), MODULE.normalized_lf(restored))
        self.assertNotEqual(MODULE.sha256_bytes(source), MODULE.sha256_bytes(restored))


if __name__ == "__main__":
    unittest.main()
