"""Regression checks for explicit manualgen assembly-workspace selection."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


MANUALGEN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MANUALGEN_ROOT))

from manualgen_lib.inventory import collect_inventory  # noqa: E402
from manualgen_lib.harvest import REQUIRED_HARVEST_FILES, inventory_harvest  # noqa: E402
from manualgen_lib.paths import ManualgenPaths  # noqa: E402


class AssemblyWorkspaceSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.published = self.repo_root / "docs" / "manuals" / "developer" / "manualgen" / "published"
        self.primary = self.published / "developer_manual_publication_v1"
        self.supporting = self.published / "developer_manual_publication_v1_media_section_v1"
        for workspace in (self.primary, self.supporting):
            section_dir = workspace / "sections"
            section_dir.mkdir(parents=True)
            (section_dir / "sample.md").write_text("# Sample\n", encoding="utf-8")
        (self.published / "README.md").write_text(
            "# Roles\n\nPrimary reader: `developer_manual_publication_v1/developer_manual_publication_v1.md`\n\n"
            "## Supporting publication workspaces\n\n`developer_manual_publication_v1_media_section_v1/`\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_legacy_default_is_compatible_but_labeled(self) -> None:
        inv = collect_inventory(ManualgenPaths(self.repo_root))
        self.assertEqual(inv["selected_assembly_id"], self.supporting.name)
        self.assertEqual(inv["assembly_selection_mode"], "legacy_default")
        self.assertEqual(inv["selected_workspace_role"], "supporting_assembly_reference")
        self.assertEqual(inv["assembly_selection_valid"], 1)

    def test_explicit_workspace_id_selects_primary_reader_role(self) -> None:
        inv = collect_inventory(ManualgenPaths(self.repo_root, publication_workspace=self.primary.name))
        self.assertEqual(inv["selected_assembly_id"], self.primary.name)
        self.assertEqual(inv["assembly_selection_mode"], "explicit")
        self.assertEqual(inv["selected_workspace_role"], "primary_reader_workspace")
        self.assertEqual(inv["assembly_selection_valid"], 1)

    def test_explicit_repo_relative_workspace_is_supported(self) -> None:
        requested = self.supporting.relative_to(self.repo_root).as_posix()
        inv = collect_inventory(ManualgenPaths(self.repo_root, publication_workspace=requested))
        self.assertEqual(inv["selected_assembly_id"], self.supporting.name)
        self.assertEqual(inv["assembly_selection_mode"], "explicit")
        self.assertEqual(inv["assembly_selection_valid"], 1)

    def test_invalid_explicit_workspace_fails_closed(self) -> None:
        inv = collect_inventory(ManualgenPaths(self.repo_root, publication_workspace="missing_workspace"))
        self.assertEqual(inv["selected_assembly_id"], "")
        self.assertEqual(inv["assembly_selection_mode"], "explicit_invalid")
        self.assertEqual(inv["assembly_selection_valid"], 0)

    def test_explicit_harvest_workspace_is_inventoried_by_hash(self) -> None:
        harvest = self.repo_root / "candidate_harvest"
        harvest.mkdir()
        for name in REQUIRED_HARVEST_FILES:
            (harvest / name).write_text("id,value\n1,ok\n", encoding="utf-8")
        inv = inventory_harvest(ManualgenPaths(self.repo_root, harvest_workspace="candidate_harvest"))
        self.assertEqual(inv["selection_mode"], "explicit")
        self.assertEqual(inv["selection_valid"], 1)
        self.assertEqual(inv["present_file_count"], len(REQUIRED_HARVEST_FILES))
        self.assertTrue(all(row["sha256"] for row in inv["files"]))

    def test_invalid_explicit_harvest_workspace_fails_closed(self) -> None:
        inv = inventory_harvest(ManualgenPaths(self.repo_root, harvest_workspace="missing_harvest"))
        self.assertEqual(inv["selection_mode"], "explicit_invalid")
        self.assertEqual(inv["selection_valid"], 0)
        self.assertEqual(inv["present_file_count"], 0)


if __name__ == "__main__":
    unittest.main()
