from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


PLANNER = load_module(
    "harvest_promotion_planner_for_apply_test",
    HERE / "build_help_meta_harvest_promotion_plan.py",
)
APPLY = load_module(
    "harvest_promotion_apply",
    HERE / "apply_help_meta_harvest_promotion.py",
)


class HarvestPromotionApplyTests(unittest.TestCase):
    def fixture(self, root: Path):
        candidate = root / "candidate"
        canonical = root / "canonical"
        package = root / "package"
        candidate.mkdir()
        canonical.mkdir()
        for index, name in enumerate(PLANNER.PACKAGE_FILES):
            before = f"before-{index}\n"
            after = before if index % 2 else f"after-{index}\n"
            (canonical / name).write_bytes(before.encode())
            (candidate / name).write_bytes(after.encode())
        with mock.patch.object(PLANNER, "audit_workspace") as audit:
            audit.side_effect = [{"status": "PASS"}, {"status": "FAIL"}]
            plan = PLANNER.build_plan(
                root,
                candidate,
                canonical,
                package,
                "DOCFLUSH-TEST-APPLY",
                "2026-08-26T00:00:00Z",
            )
        plan_path = package / "help_meta_harvest_promotion_plan.json"
        authorization = package / "AUTHORIZATION.md"
        authorization.write_text(
            "\n".join([
                "Decision: authorized for canonical harvest apply.",
                f"Plan run: `{plan['run_id']}`.",
                f"Plan manifest SHA-256: `{APPLY.sha256(plan_path)}`.",
                f"Mutation ledger SHA-256: `{plan['mutation_ledger_sha256']}`.",
                f"Mutation rows authorized: {plan['planned_mutation_rows']}.",
            ]),
            encoding="utf-8",
        )
        return candidate, canonical, package, plan, plan_path, authorization

    @mock.patch.object(APPLY, "audit_workspace")
    def test_authorized_apply_backs_up_and_replaces_exact_rows(self, audit) -> None:
        audit.side_effect = [{"status": "PASS"}, {"status": "PASS"}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate, canonical, package, plan, plan_path, authorization = self.fixture(root)
            record = APPLY.apply_plan(
                root,
                plan_path,
                authorization,
                root / "backup",
                package / "execution.json",
                plan["run_id"],
                "2026-08-26T01:00:00Z",
            )
            self.assertEqual("APPLIED", record["status"])
            self.assertEqual(plan["planned_mutation_rows"], record["canonical_files_mutated"])
            for row in record["rows"]:
                self.assertEqual(row["after_sha256"], APPLY.sha256(root / row["target"]))
                self.assertEqual(row["before_sha256"], APPLY.sha256(root / row["backup"]))

    @mock.patch.object(APPLY, "audit_workspace")
    def test_missing_authorization_fails_before_mutation(self, audit) -> None:
        audit.return_value = {"status": "PASS"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _candidate, canonical, package, plan, plan_path, authorization = self.fixture(root)
            authorization.write_text("not authorized\n", encoding="utf-8")
            before = {path.name: path.read_bytes() for path in canonical.iterdir()}
            record = APPLY.apply_plan(
                root,
                plan_path,
                authorization,
                root / "backup",
                package / "execution.json",
                plan["run_id"],
                "2026-08-26T01:00:00Z",
            )
            after = {path.name: path.read_bytes() for path in canonical.iterdir()}
            self.assertEqual("FAIL_PREFLIGHT", record["status"])
            self.assertEqual(before, after)

    @mock.patch.object(APPLY, "audit_workspace")
    def test_mid_apply_failure_restores_every_before_hash(self, audit) -> None:
        audit.return_value = {"status": "PASS"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _candidate, canonical, package, plan, plan_path, authorization = self.fixture(root)
            before = {path.name: path.read_bytes() for path in canonical.iterdir()}
            calls = {"apply": 0, "failed": False}

            def fail_once(path: Path, value: bytes, token: str) -> None:
                if "rollback" not in token:
                    calls["apply"] += 1
                    if calls["apply"] == 2 and not calls["failed"]:
                        calls["failed"] = True
                        raise RuntimeError("injected write failure")
                APPLY.atomic_write(path, value, token)

            record = APPLY.apply_plan(
                root,
                plan_path,
                authorization,
                root / "backup",
                package / "execution.json",
                plan["run_id"],
                "2026-08-26T01:00:00Z",
                writer=fail_once,
            )
            after = {path.name: path.read_bytes() for path in canonical.iterdir()}
            self.assertEqual("FAILED_ROLLED_BACK", record["status"])
            self.assertEqual(1, record["rollback_performed"])
            self.assertEqual(before, after)

    @mock.patch.object(APPLY, "audit_workspace")
    def test_manual_rollback_is_after_hash_guarded(self, audit) -> None:
        audit.side_effect = [{"status": "PASS"}, {"status": "PASS"}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _candidate, canonical, package, plan, plan_path, authorization = self.fixture(root)
            before = {path.name: path.read_bytes() for path in canonical.iterdir()}
            execution_record = package / "execution.json"
            applied = APPLY.apply_plan(
                root,
                plan_path,
                authorization,
                root / "backup",
                execution_record,
                plan["run_id"],
                "2026-08-26T01:00:00Z",
            )
            self.assertEqual("APPLIED", applied["status"])
            rolled_back = APPLY.rollback_execution(
                root,
                execution_record,
                plan["run_id"],
                "2026-08-26T02:00:00Z",
                package / "rollback.json",
            )
            after = {path.name: path.read_bytes() for path in canonical.iterdir()}
            self.assertEqual("ROLLED_BACK", rolled_back["status"])
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
