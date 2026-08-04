"""Test the tracking extractor against the real registries (AIF-086 M1).

Runs seed_tracking.seed() into a temp dir and asserts the structural invariants
that matter for a non-drifting tracking layer: one row per authored record, unique
natural keys, and referential integrity from SYSRUNLANE back to SYSRUN. Skips
cleanly if pyyaml is unavailable.
"""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SEEDER = REPO / "tools" / "tracking" / "seed_tracking.py"


def _load_seeder():
    spec = importlib.util.spec_from_file_location("seed_tracking", SEEDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@unittest.skipUnless(SEEDER.is_file(), "seed_tracking.py not found")
@unittest.skipUnless(importlib.util.find_spec("yaml") is not None, "pyyaml not installed")
class SeedTrackingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="tracking-seed-test-")
        cls.out = Path(cls._tmp.name)
        mod = _load_seeder()
        cls.counts = mod.seed(REPO, cls.out)
        cls.lanes = _rows(cls.out / "SYSLANE.csv")
        cls.runs = _rows(cls.out / "SYSRUN.csv")
        cls.runlane = _rows(cls.out / "SYSRUNLANE.csv")
        cls.proofs = _rows(cls.out / "SYSPROOF.csv")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_all_four_tables_emitted_nonempty(self):
        for name in ("SYSLANE", "SYSRUN", "SYSRUNLANE", "SYSPROOF"):
            self.assertTrue((self.out / f"{name}.csv").is_file(), f"{name}.csv missing")
            self.assertGreater(self.counts[name], 0, f"{name} is empty")

    def test_lane_keys_unique_and_well_formed(self):
        keys = [r["LKEY"] for r in self.lanes]
        self.assertEqual(len(keys), len(set(keys)), "duplicate LKEY")
        self.assertTrue(all(k.startswith("AIF-") for k in keys), "a LKEY is not an AIF-*")

    def test_run_keys_unique_and_have_owner(self):
        keys = [r["RKEY"] for r in self.runs]
        self.assertEqual(len(keys), len(set(keys)), "duplicate RKEY")
        self.assertTrue(all(r["OWNERKEY"].startswith("member.") for r in self.runs), "a run has no member owner")

    def test_runlane_references_a_real_run(self):
        run_keys = {r["RKEY"] for r in self.runs}
        for rl in self.runlane:
            self.assertIn(rl["RUNKEY"], run_keys, f"SYSRUNLANE references unknown run {rl['RUNKEY']}")

    def test_proof_keys_unique(self):
        keys = [r["PKEY"] for r in self.proofs]
        self.assertEqual(len(keys), len(set(keys)), "duplicate PKEY")


if __name__ == "__main__":
    unittest.main()
