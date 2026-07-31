from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


SCRIPT = Path(__file__).resolve().parents[1] / "build_historical_source_museum.py"
SPEC = importlib.util.spec_from_file_location("build_historical_source_museum", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HistoricalSourceMuseumTests(unittest.TestCase):
    def test_archive_projection_is_complete_and_private_path_free(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "xbase.zip"
            with ZipFile(archive, "w") as bundle:
                for family, _, _, names in MODULE.FAMILIES:
                    for name in names:
                        bundle.writestr(f"xbase/{family}/{name}", f"/* {family}/{name} */\n")

            archive_sha, rows, payloads = MODULE.read_archive(archive)
            self.assertEqual(len(archive_sha), 64)
            self.assertEqual(len(rows), 21)
            self.assertEqual(len(payloads), 21)
            self.assertEqual(len({row["artifact_id"] for row in rows}), 21)
            self.assertTrue(all(row["public_path"].startswith("/") for row in rows))
            self.assertNotIn(str(root), MODULE.render_page(archive_sha, rows))

    def test_missing_required_member_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "incomplete.zip"
            with ZipFile(archive, "w") as bundle:
                bundle.writestr("xbase/xbase/XBASE.C", "missing the rest")
            with self.assertRaisesRegex(ValueError, "required archive member missing"):
                MODULE.read_archive(archive)

    def test_written_source_files_preserve_archive_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "xbase.zip"
            expected: dict[str, bytes] = {}
            with ZipFile(archive, "w") as bundle:
                for family, _, _, names in MODULE.FAMILIES:
                    for index, name in enumerate(names):
                        payload = (
                            f"/* {family}/{name} */\r\n"
                            f"byte-preservation-{family}-{index}\x1a"
                        ).encode("cp1252")
                        bundle.writestr(f"xbase/{family}/{name}", payload)
                        expected[f"{family}/{name.lower()}.txt"] = payload

            out_files = root / "public" / "historical-source"
            MODULE.write_outputs(
                archive,
                out_files,
                root / "historical-source-files.mdx",
                root / "historical-source-files.json",
                root / "historical-source-files.csv",
            )

            for relative, payload in expected.items():
                self.assertEqual((out_files / relative).read_bytes(), payload)
                target = out_files / relative
                viewer = target.with_name(
                    target.name.removesuffix(".txt") + ".html"
                )
                rendered = viewer.read_text(encoding="utf-8")
                self.assertIn("Read-only archive view", rendered)
                self.assertIn("byte-preservation", rendered)


if __name__ == "__main__":
    unittest.main()
