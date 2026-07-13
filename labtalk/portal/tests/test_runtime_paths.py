from __future__ import annotations

import sys
import unittest
from pathlib import Path


PORTAL_ROOT = Path(__file__).resolve().parents[1]
if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))

from labtalk_portal import REPO_ROOT, dottalk_paths  # noqa: E402


class RuntimePathTests(unittest.TestCase):
    def test_relative_runtime_paths_resolve_from_repository_root(self) -> None:
        exe, workdir = dottalk_paths(
            {
                "paths": {
                    "dottalkpp_exe": "dottalkpp/bin/dottalkpp.exe",
                    "dottalkpp_workdir": ".",
                }
            }
        )

        self.assertEqual(exe, REPO_ROOT / "dottalkpp" / "bin" / "dottalkpp.exe")
        self.assertEqual(workdir, REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
