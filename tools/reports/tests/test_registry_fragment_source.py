"""Tests for the live report path over authoritative registry fragments."""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
BUILDER = REPO / "tools" / "reports" / "build_reports.py"
REGISTRY_HELPER = REPO / "tools" / "registries" / "registry_fragments.py"
SPEC = importlib.util.spec_from_file_location("registry_fragments_test", REGISTRY_HELPER)
REGISTRY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(REGISTRY)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_fragment_registries(root: Path) -> tuple[Path, Path]:
    registry = root / "labtalk" / "registries"
    write(registry / "runs.d" / "_header.yaml", "runs_registry:\n  schema: test\n")
    write(
        registry / "runs.d" / "AIPR-TEST-001.yaml",
        "run_id: AIPR-TEST-001\n"
        "project: project.test\n"
        "lanes: [AIF-900]\n"
        "started: 2026-08-15\n"
        "status: complete\n",
    )
    write(
        registry / "runs.d" / "AIPR-TEST-002.yaml",
        "run_id: AIPR-TEST-002\n"
        "project: project.test\n"
        "lanes: [AIF-900]\n"
        "started: 2026-08-16\n"
        "status: active\n",
    )
    write(registry / "proofs.d" / "_header.yaml", "proof_states: []\n")
    write(
        registry / "proofs.d" / "proof.test.fragment.yaml",
        "id: proof.test.fragment\n"
        "label: Fragment source proof\n"
        "state: source_defined\n"
        "notes: composed without touching flat files\n",
    )
    runs_flat = registry / "ai_runs.yaml"
    proofs_flat = registry / "proofs.yaml"
    write(
        runs_flat,
        "runs:\n- run_id: STALE-FLAT-RUN\n"
        "current_by_lane:\n  AIF-900: STALE-FLAT-RUN\n",
    )
    write(proofs_flat, "proofs:\n- id: proof.stale.flat\n")
    return runs_flat, proofs_flat


class RegistryCompositionTests(unittest.TestCase):
    def test_compose_uses_fragments_computes_indexes_and_does_not_touch_flats(self):
        with tempfile.TemporaryDirectory(prefix="registry-compose-test-") as temporary:
            root = Path(temporary)
            runs_flat, proofs_flat = seed_fragment_registries(root)
            before = {
                path: (path.read_bytes(), path.stat().st_mtime_ns)
                for path in (runs_flat, proofs_flat)
            }

            runs = REGISTRY.compose_registry(root, "ai_runs.yaml")
            proofs = REGISTRY.compose_registry(root, "proofs.yaml")

            self.assertEqual([r["run_id"] for r in runs["runs"]],
                             ["AIPR-TEST-001", "AIPR-TEST-002"])
            self.assertEqual(runs["current_by_lane"]["AIF-900"], "AIPR-TEST-002")
            self.assertEqual(runs["current_by_project"]["project.test"], "AIPR-TEST-002")
            self.assertEqual([p["id"] for p in proofs["proofs"]],
                             ["proof.test.fragment"])
            for path, (body, modified) in before.items():
                self.assertEqual(path.read_bytes(), body)
                self.assertEqual(path.stat().st_mtime_ns, modified)

    def test_compose_rejects_missing_and_duplicate_ids(self):
        with tempfile.TemporaryDirectory(prefix="registry-id-test-") as temporary:
            root = Path(temporary)
            run_dir = root / "labtalk" / "registries" / "runs.d"
            write(run_dir / "_header.yaml", "runs_registry: {}\n")
            write(run_dir / "missing.yaml", "status: active\n")
            with self.assertRaisesRegex(ValueError, r"missing\.yaml.*run_id"):
                REGISTRY.compose_registry(root, "ai_runs.yaml")

            (run_dir / "missing.yaml").unlink()
            write(run_dir / "one.yaml", "run_id: AIPR-DUPLICATE\n")
            write(run_dir / "two.yaml", "run_id: AIPR-DUPLICATE\n")
            with self.assertRaisesRegex(ValueError, r"duplicate run_id 'AIPR-DUPLICATE'"):
                REGISTRY.compose_registry(root, "ai_runs.yaml")


@unittest.skipUnless(BUILDER.is_file(), "build_reports.py not found")
class FragmentReportIntegrationTests(unittest.TestCase):
    def test_fragment_build_ignores_and_does_not_mutate_flat_snapshots(self):
        with tempfile.TemporaryDirectory(prefix="fragment-report-test-") as temporary:
            root = Path(temporary) / "repo"
            out = Path(temporary) / "out"
            for area, names in {
                "bbs": ("SYSBOARD", "SYSTHREAD", "SYSPOST"),
                "identity": (
                    "SYSMEMBER", "SYSROLE", "SYSPERM", "SYSMEMROLE",
                    "SYSROLEPERM", "SYSUSER", "SYSGRANT",
                ),
            }.items():
                for name in names:
                    source = REPO / "dottalkpp" / "data" / "metadata" / area / f"{name}.dbf"
                    target = root / "dottalkpp" / "data" / "metadata" / area / f"{name}.dbf"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)

            helper = root / "tools" / "registries" / "registry_fragments.py"
            helper.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REGISTRY_HELPER, helper)
            write(root / "labtalk" / "registries" / "portal.yaml", "sections: []\n")
            write(root / "docs" / "ai-friendly" / "AI_INTERACTION_INTAKE_QUEUE_V1.md", "")
            runs_flat, proofs_flat = seed_fragment_registries(root)
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns)
                      for path in (runs_flat, proofs_flat)}

            result = subprocess.run(
                [sys.executable, str(BUILDER), "--root", str(root), "--out", str(out),
                 "--source", "fragments"],
                cwd=str(REPO), capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=120, check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr[-1000:])
            portal = (out / "AI_PORTAL_REPORT.html").read_text(encoding="utf-8")
            index = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("source: current local registry fragments", portal)
            self.assertIn("AIPR-TEST-002", portal)
            self.assertIn("proof.test.fragment", portal)
            self.assertNotIn("STALE-FLAT-RUN", portal)
            self.assertNotIn("proof.stale.flat", portal)
            self.assertIn(
                "python tools/reports/build_reports.py --source fragments",
                index,
            )
            self.assertIn("authoritative local registry fragments", index)
            for path, (body, modified) in before.items():
                self.assertEqual(path.read_bytes(), body)
                self.assertEqual(path.stat().st_mtime_ns, modified)


if __name__ == "__main__":
    unittest.main()
