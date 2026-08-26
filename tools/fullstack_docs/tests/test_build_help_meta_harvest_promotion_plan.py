from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "build_help_meta_harvest_promotion_plan.py"
SPEC = importlib.util.spec_from_file_location("harvest_promotion_plan", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class HarvestPromotionPlanTests(unittest.TestCase):
    def make_workspaces(self, root: Path) -> tuple[Path, Path, Path]:
        candidate = root / "candidate"
        canonical = root / "canonical"
        output = root / "output"
        candidate.mkdir()
        canonical.mkdir()
        for index, name in enumerate(MOD.PACKAGE_FILES):
            before = f"before-{index}\n"
            after = before if index % 2 else f"after-{index}\n"
            (canonical / name).write_text(before, encoding="utf-8")
            (candidate / name).write_text(after, encoding="utf-8")
        return candidate, canonical, output

    @mock.patch.object(MOD, "audit_workspace")
    def test_plan_selects_only_changed_files_and_cannot_apply(self, audit) -> None:
        audit.side_effect = [{"status": "PASS"}, {"status": "FAIL"}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate, canonical, output = self.make_workspaces(root)
            plan = MOD.build_plan(
                root,
                candidate,
                canonical,
                output,
                "DOCFLUSH-TEST-001",
                "2026-08-26T00:00:00Z",
            )
            expected_changes = (len(MOD.PACKAGE_FILES) + 1) // 2
            self.assertEqual("PASS_PLAN_ONLY", plan["status"])
            self.assertEqual(expected_changes, plan["planned_mutation_rows"])
            self.assertEqual(0, plan["apply_available"])
            self.assertEqual(0, plan["mutation_authorized"])
            self.assertEqual(0, plan["canonical_files_mutated"])
            self.assertTrue((output / "help_meta_harvest_mutation_ledger.json").is_file())
            plan_path = output / "help_meta_harvest_promotion_plan.json"
            review = (output / "HELP_META_HARVEST_PROMOTION_REVIEW.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(MOD.sha256(plan_path), review)
            self.assertIn(plan["mutation_ledger_sha256"], review)

    @mock.patch.object(MOD, "audit_workspace")
    def test_stale_candidate_fails_closed(self, audit) -> None:
        audit.side_effect = [{"status": "FAIL"}, {"status": "FAIL"}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate, canonical, output = self.make_workspaces(root)
            plan = MOD.build_plan(
                root,
                candidate,
                canonical,
                output,
                "DOCFLUSH-TEST-002",
                "2026-08-26T00:00:00Z",
            )
            self.assertEqual("FAIL_PLAN_ONLY", plan["status"])
            self.assertIn("CANDIDATE_NOT_CURRENT", plan["findings"])

    @mock.patch.object(MOD, "audit_workspace")
    def test_same_inputs_and_observation_time_are_idempotent(self, audit) -> None:
        audit.return_value = {"status": "PASS"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate, canonical, output = self.make_workspaces(root)
            args = (
                root,
                candidate,
                canonical,
                output,
                "DOCFLUSH-TEST-003",
                "2026-08-26T00:00:00Z",
            )
            MOD.build_plan(*args)
            before = {path.name: path.read_bytes() for path in output.iterdir()}
            MOD.build_plan(*args)
            after = {path.name: path.read_bytes() for path in output.iterdir()}
            self.assertEqual(before, after)

    def test_path_outside_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            outside = Path(directory) / "outside"
            outside.mkdir()
            with self.assertRaisesRegex(ValueError, "escapes repository root"):
                MOD.repo_relative(root, outside)


if __name__ == "__main__":
    unittest.main()
