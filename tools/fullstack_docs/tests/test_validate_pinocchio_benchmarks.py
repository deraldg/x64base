from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/validate_pinocchio_benchmarks.py"
DEVELOPMENT_BASELINE_INPUTS = (
    ROOT / "docs/maintenance/PINOCCHIO_HISTORICAL_ENGINE_BENCHMARKS_V1.csv",
    ROOT / "docs/maintenance/PINOCCHIO_MACHINE_PROFILE_CURRENT_V1.json",
)
SPEC = importlib.util.spec_from_file_location("validate_pinocchio_benchmarks", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class PinocchioBenchmarkValidatorTests(unittest.TestCase):
    @unittest.skipUnless(
        all(path.exists() for path in DEVELOPMENT_BASELINE_INPUTS),
        "development benchmark ledger and machine profile are intentionally absent from the public projection",
    )
    def test_repository_baseline_is_valid(self) -> None:
        rows, profile, findings = MOD.validate(ROOT)
        self.assertEqual(8, len(rows))
        self.assertEqual("Alienware m16 R2", profile["machine_type"])
        self.assertEqual([], findings)

    def test_exact_speedup_is_checked(self) -> None:
        row = {
            "baseline_id": "X",
            "before_seconds": "10",
            "after_seconds": "2",
            "after_seconds_min": "2",
            "after_seconds_max": "2",
            "speedup_x": "4",
            "speedup_min_x": "5",
            "speedup_max_x": "5",
            "machine_type": "lab-a",
            "machine_binding": "CURRENT_RUN_ONLY",
            "before_evidence_path": "missing",
            "before_evidence_sha256": "0",
            "after_evidence_path": "missing",
            "after_evidence_sha256": "0",
            "transcript_status": "RAW",
            "proof_state": "runtime_proven",
        }
        findings = MOD.validate_rows([row] * 8, ROOT)
        self.assertTrue(any("EXACT_SPEEDUP_MISMATCH" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
