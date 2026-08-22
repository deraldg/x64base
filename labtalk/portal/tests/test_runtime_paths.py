from __future__ import annotations

import sys
import unittest
from pathlib import Path


PORTAL_ROOT = Path(__file__).resolve().parents[1]
if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))

from labtalk_portal import LABTALK_ROOT, REPO_ROOT, dottalk_paths, load_portal_items  # noqa: E402


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

    def test_cascade_erp_workspace_is_registered_with_existing_paths(self) -> None:
        sections, items = load_portal_items()
        section_ids = {str(section.get("id")) for section in sections}
        cascade_items = {
            item.item_id: item
            for item in items
            if item.section_id == "portal.cascade_erp"
        }

        self.assertIn("portal.cascade_erp", section_ids)
        self.assertEqual(
            set(cascade_items),
            {
                "cascade.erp.lane",
                "cascade.erp.package_readme",
                "cascade.erp.manifest",
                "cascade.erp.sqlite",
                "cascade.erp.items_crosswalk",
                "cascade.erp.dual_schema_contract",
                "cascade.erp.schema_parity_report",
                "cascade.erp.mirror_runtime_status",
                "cascade.erp.rebuild_x64base_mirror",
                "cascade.erp.runtime",
            },
        )
        self.assertEqual(cascade_items["cascade.erp.sqlite"].kind, "sqlite_database")
        self.assertEqual(cascade_items["cascade.erp.runtime"].kind, "powershell_launcher")

        for item in cascade_items.values():
            path = item.data.get("path")
            self.assertIsInstance(path, str)
            self.assertTrue((LABTALK_ROOT / path).exists(), path)


if __name__ == "__main__":
    unittest.main()
