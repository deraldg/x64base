from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools" / "fullstack_docs" / "guarded_help_refresh.py"
SPEC = importlib.util.spec_from_file_location("guarded_help_refresh", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GuardedHelpRefreshTests(unittest.TestCase):
    def make_repo(self, root: Path) -> tuple[Path, Path, Path]:
        help_root = root / "dottalkpp" / "data" / "help"
        help_root.mkdir(parents=True)
        (help_root / "HELP_TOPIC.dbf").write_bytes(b"before-topic")
        (help_root / "nested").mkdir()
        (help_root / "nested" / "proof.txt").write_bytes(b"before-proof")
        exe = root / "build" / "src" / "Release" / "dottalkpp.exe"
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b"exe")
        script = root / "commands.dts"
        script.write_text("QUIT\n", encoding="ascii")
        return help_root, exe, script

    def prepare(self, root: Path) -> tuple[Path, Path]:
        _, _, script = self.make_repo(root)
        plan = MODULE.build_plan(root, "RUN-1", "2026-08-26T00:00:00Z", script)
        plan_path = root / "plan.json"
        MODULE.write_json(plan_path, plan)
        auth = {
            "schema": MODULE.AUTH_SCHEMA,
            "run_id": "RUN-1",
            "authorized": True,
            "plan_sha256": MODULE.sha256_file(plan_path),
            "protected_file_count": plan["protected_file_count"],
            "control_sha256": MODULE.sha256_file(MODULE_PATH),
        }
        auth_path = root / "auth.json"
        MODULE.write_json(auth_path, auth)
        return plan_path, auth_path

    def test_missing_authorization_refuses_before_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, auth_path = self.prepare(root)
            auth = json.loads(auth_path.read_text())
            auth["authorized"] = False
            MODULE.write_json(auth_path, auth)
            backup = root / "backup"
            with self.assertRaises(ValueError):
                MODULE.apply_plan(
                    root, plan_path, auth_path, backup, root / "out.txt", root / "exec.json",
                    MODULE.CONFIRM_APPLY, "2026-08-26T00:01:00Z",
                )
            self.assertFalse(backup.exists())

    def test_failure_restores_complete_before_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, auth_path = self.prepare(root)
            help_root = root / "dottalkpp" / "data" / "help"

            def runner(_repo: Path, _script: Path) -> subprocess.CompletedProcess[str]:
                (help_root / "HELP_TOPIC.dbf").write_bytes(b"changed")
                (help_root / "new.dbf").write_bytes(b"new")
                return subprocess.CompletedProcess([], 1, "failed")

            with self.assertRaises(RuntimeError):
                MODULE.apply_plan(
                    root, plan_path, auth_path, root / "backup", root / "out.txt", root / "exec.json",
                    MODULE.CONFIRM_APPLY, "2026-08-26T00:01:00Z", runner=runner,
                    semantic_validator=lambda _repo: (True, "ok"), process_probe=lambda: [],
                )
            self.assertEqual(b"before-topic", (help_root / "HELP_TOPIC.dbf").read_bytes())
            self.assertFalse((help_root / "new.dbf").exists())
            self.assertEqual("FAILED_ROLLED_BACK", json.loads((root / "exec.json").read_text())["status"])

    def test_open_runtime_refuses_before_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, auth_path = self.prepare(root)
            backup = root / "backup"
            with self.assertRaises(ValueError):
                MODULE.apply_plan(
                    root, plan_path, auth_path, backup, root / "out.txt", root / "exec.json",
                    MODULE.CONFIRM_APPLY, "2026-08-26T00:01:00Z", process_probe=lambda: ["pid 1"],
                )
            self.assertFalse(backup.exists())

    def test_success_and_after_hash_guarded_manual_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, auth_path = self.prepare(root)
            help_root = root / "dottalkpp" / "data" / "help"
            transcript = "\n".join(
                [
                    "CMDHELP LEGACY wrote: 1 command rows, 1 arg rows",
                    "Usage contracts mined directly: 1 row(s) from 1 file(s)",
                    "OK no structural issues found",
                    "DOCFLUSH-E2-REFRESH-END",
                ]
            )

            def runner(_repo: Path, _script: Path) -> subprocess.CompletedProcess[str]:
                (help_root / "HELP_TOPIC.dbf").write_bytes(b"after-topic")
                return subprocess.CompletedProcess([], 0, transcript)

            execution_path = root / "exec.json"
            result = MODULE.apply_plan(
                root, plan_path, auth_path, root / "backup", root / "out.txt", execution_path,
                MODULE.CONFIRM_APPLY, "2026-08-26T00:01:00Z", runner=runner,
                semantic_validator=lambda _repo: (True, "clean"), process_probe=lambda: [],
            )
            self.assertEqual("APPLIED", result["status"])
            (help_root / "HELP_TOPIC.dbf").write_bytes(b"later-drift")
            with self.assertRaises(ValueError):
                MODULE.rollback_execution(
                    root, execution_path, root / "rollback.json", MODULE.CONFIRM_ROLLBACK,
                    "2026-08-26T00:02:00Z",
                )

    def test_relative_output_paths_resolve_from_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, auth_path = self.prepare(root)
            help_root = root / "dottalkpp" / "data" / "help"
            transcript = "\n".join(
                [
                    "CMDHELP LEGACY wrote: 1 command rows, 1 arg rows",
                    "Usage contracts mined directly: 1 row(s) from 1 file(s)",
                    "OK no structural issues found",
                    "DOCFLUSH-E2-REFRESH-END",
                ]
            )

            def runner(_repo: Path, _script: Path) -> subprocess.CompletedProcess[str]:
                (help_root / "HELP_TOPIC.dbf").write_bytes(b"after-topic")
                return subprocess.CompletedProcess([], 0, transcript)

            result = MODULE.apply_plan(
                root, Path("plan.json"), Path("auth.json"), Path("backup"),
                Path("out.txt"), Path("exec.json"), MODULE.CONFIRM_APPLY,
                "2026-08-26T00:01:00Z", runner=runner,
                semantic_validator=lambda _repo: (True, "clean"), process_probe=lambda: [],
            )
            self.assertEqual("APPLIED", result["status"])
            self.assertTrue((root / "out.txt").is_file())
            self.assertTrue((root / "exec.json").is_file())


if __name__ == "__main__":
    unittest.main()
