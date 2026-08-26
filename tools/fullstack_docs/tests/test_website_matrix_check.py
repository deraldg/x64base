from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools" / "fullstack_docs" / "website_matrix_check.py"
SPEC = importlib.util.spec_from_file_location("website_matrix_check", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WebsiteMatrixCheckTests(unittest.TestCase):
    def test_matrix_runs_every_declared_hard_relationship(self) -> None:
        seen: list[list[str]] = []

        def passing(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
            seen.append(command)
            return subprocess.CompletedProcess(command, 0, "PASS\n", "")

        failed = MODULE.run_matrix_check(Path("C:/ccode"), Path("D:/site"), passing)
        self.assertEqual([], failed)
        joined = [" ".join(command) for command in seen]
        self.assertEqual(5, len(joined))
        self.assertTrue(any("docpush_preflight.py" in command for command in joined))
        self.assertTrue(any("validate_website_content_manifest.py" in command for command in joined))
        self.assertTrue(any("fn-check" in command for command in joined))
        self.assertTrue(any("err-check" in command for command in joined))
        self.assertTrue(any("loc-check" in command for command in joined))

    def test_failed_fullstack_entry_fails_the_matrix(self) -> None:
        def with_stale_help(
            command: list[str], **_kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            if any("docpush_preflight.py" in token for token in command):
                return subprocess.CompletedProcess(command, 2, "E2 FAIL\n", "")
            return subprocess.CompletedProcess(command, 0, "PASS\n", "")

        failed = MODULE.run_matrix_check(
            Path("C:/ccode"), Path("D:/site"), with_stale_help
        )
        self.assertEqual(["fullstack_publication_entry"], failed)


if __name__ == "__main__":
    unittest.main()
