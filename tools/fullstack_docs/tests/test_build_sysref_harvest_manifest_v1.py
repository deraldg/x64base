from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/build_sysref_harvest_manifest_v1.py"
SPEC = importlib.util.spec_from_file_location("build_sysref_harvest_manifest_v1", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class ManifestBuilderTests(unittest.TestCase):
    def fixture(self, root: Path) -> dict[str, Path]:
        root.mkdir(parents=True, exist_ok=True)
        paths = {}
        for role in ("SYSCMD", "SYSARGS", "SRCUSAGE", "REFVOICE"):
            path = root / f"{role.lower()}.csv"
            path.write_text(f"role\n{role}\n", encoding="utf-8")
            paths[role] = path
        collector = root / "collector.py"
        collector.write_text("# collector\n", encoding="utf-8")
        paths["COLLECTOR"] = collector
        return paths

    def args(self, root: Path, paths: dict[str, Path], out: Path) -> list[str]:
        values = [
            "--root", str(root),
            "--harvest-run-id", "DOCFLUSH-TEST-001",
            "--created-utc", "2026-10-13T20:00:00Z",
            "--created-by", "member.ai.codex",
            "--collector-id", "test-collector-v1",
            "--collector-path", str(paths["COLLECTOR"]),
        ]
        for role in ("SYSCMD", "SYSARGS", "SRCUSAGE", "REFVOICE"):
            values.extend(["--input", f"{role}={paths[role]}"])
        values.extend(["--out", str(out)])
        return values

    def test_builds_sorted_hash_bound_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self.fixture(root)
            out = root / "manifest.json"
            with mock.patch.object(subprocess, "check_output", return_value="abc1234\n"):
                self.assertEqual(0, MOD.main(self.args(root, paths, out)))
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(MOD.SCHEMA, payload["schema"])
            self.assertEqual("ABC1234", payload["repo_sha"])
            self.assertEqual(["REFVOICE", "SRCUSAGE", "SYSARGS", "SYSCMD"], [row["role"] for row in payload["inputs"]])
            self.assertEqual("CANONICAL", payload["inputs"][0]["producer_run_id"])
            self.assertTrue(all(len(row["sha256"]) == 64 for row in payload["inputs"]))

    def test_missing_required_role_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self.fixture(root)
            args = self.args(root, paths, root / "manifest.json")
            index = args.index("--input")
            del args[index:index + 2]
            self.assertEqual(2, MOD.main(args))

    def test_duplicate_role_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self.fixture(root)
            args = self.args(root, paths, root / "manifest.json")
            args.extend(["--input", f"SYSCMD={paths['SYSCMD']}"])
            self.assertEqual(2, MOD.main(args))

    def test_outside_input_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "repo"
            paths = self.fixture(root)
            outside = base / "outside.csv"
            outside.write_text("outside\n", encoding="utf-8")
            args = self.args(root, paths, root / "manifest.json")
            for index, value in enumerate(args):
                if value.startswith("SYSCMD="):
                    args[index] = f"SYSCMD={outside}"
            self.assertEqual(2, MOD.main(args))

    def test_existing_output_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self.fixture(root)
            out = root / "manifest.json"
            out.write_text("existing\n", encoding="utf-8")
            self.assertEqual(2, MOD.main(self.args(root, paths, out)))


if __name__ == "__main__":
    unittest.main()
