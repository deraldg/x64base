from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


MODULE = Path(__file__).resolve().parents[1] / "apply_dotref_m3e_promotion_v1.py"
SPEC = importlib.util.spec_from_file_location("apply_dotref_m3e_promotion_v1", MODULE)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


def item(name: str, syntax: str, summary: str, supported: bool) -> SimpleNamespace:
    return SimpleNamespace(name=name, syntax=syntax, summary=summary, supported=supported)


class DotrefM3ePromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.current = [item(f"C{i:03d}", f"C{i:03d}", f"Summary {i}", True) for i in range(268)]
        self.candidate = [item(row.name, row.syntax, row.summary, row.supported) for row in self.current]
        self.diff_rows = []
        for index in range(22):
            self.candidate[index].supported = False
            self.diff_rows.append({
                "NAME": self.current[index].name,
                "FIELD": "SUPPORTED",
                "CURRENT": "T",
                "CANDIDATE": "F",
                "DISPOSITION": "APPROVED_M3D_CANDIDATE",
            })

    def test_approved_support_only_projection_passes(self) -> None:
        actual = M.validate_projection(self.current, self.candidate, self.diff_rows)
        self.assertEqual(22, len(actual))

    def test_planted_stale_syntax_fixture_fails(self) -> None:
        self.candidate[100].syntax = "STALE SYNTAX"
        with self.assertRaisesRegex(M.PromotionError, "FIELD_DIFF_DOES_NOT_MATCH_APPROVAL"):
            M.validate_projection(self.current, self.candidate, self.diff_rows)

    def test_member_reordering_fails(self) -> None:
        self.candidate[0], self.candidate[1] = self.candidate[1], self.candidate[0]
        with self.assertRaisesRegex(M.PromotionError, "MEMBER_ORDER_OR_IDENTITY_DRIFT"):
            M.validate_projection(self.current, self.candidate, self.diff_rows)

    def test_changed_source_revision_fails(self) -> None:
        with self.assertRaisesRegex(M.PromotionError, "REPOSITORY_REVISION_MISMATCH"):
            M.validate_repo_binding("0" * 40, M.EXPECTED_BRANCH)

    def test_changed_input_hash_fails(self) -> None:
        with self.assertRaisesRegex(M.PromotionError, "CANDIDATE_HASH_MISMATCH"):
            M.validate_hash("candidate", "0" * 64, M.EXPECTED_CANDIDATE_SHA256)


if __name__ == "__main__":
    unittest.main()
