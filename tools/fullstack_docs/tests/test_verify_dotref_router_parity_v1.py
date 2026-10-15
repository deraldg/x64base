from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.fullstack_docs import verify_dotref_router_parity_v1 as verifier


class DotrefRouterParityVerifierTests(unittest.TestCase):
    def test_changed_candidate_is_rejected_before_use(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "dotref_candidate.csv"
            candidate.write_text(
                '"NAME","SYNTAX","SUMMARY","SUPPORTED"\n'
                '"HELP","HELP","changed","T"\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                verifier.VerificationError, "PROJECTION_HASH_MISMATCH"
            ):
                verifier.read_approved_projection(candidate, SimpleNamespace())

    def test_prompt_text_is_not_a_structured_member(self) -> None:
        items = [SimpleNamespace(name="HELP", syntax="HELP [<topic>]")]
        text = ". HELP\n  HELP [<topic>]\nHELP\n  HELP [<topic>]\n"
        self.assertEqual(verifier.structured_members(text, items), ["HELP"])

    def test_name_without_following_syntax_is_not_a_member(self) -> None:
        items = [SimpleNamespace(name="VAR", syntax="VAR USAGE")]
        self.assertEqual(verifier.structured_members("VAR\nwrong\n", items), [])


if __name__ == "__main__":
    unittest.main()
