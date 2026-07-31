from __future__ import annotations

import hashlib
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "staging"))

from create_public_baseline_escrow import (  # noqa: E402
    archive_ledger,
    classify_relation,
    normalized_relative,
)


class PublicBaselineEscrowTests(unittest.TestCase):
    def test_normalized_relative_rejects_escape(self) -> None:
        with self.assertRaises(ValueError):
            normalized_relative("../outside.txt")

    def test_normalized_relative_accepts_spaces(self) -> None:
        self.assertEqual("docs/a file.txt", normalized_relative("docs\\a file.txt"))

    def test_classify_relation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "same.txt"
            path.write_bytes(b"same")
            digest = hashlib.sha256(b"same").hexdigest().upper()
            relation, actual, size = classify_relation(digest, path)
            self.assertEqual("EXACT_IN_DEVELOPMENT", relation)
            self.assertEqual(digest, actual)
            self.assertEqual(4, size)

    def test_archive_ledger_finds_public_only_and_divergent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            development = root / "development"
            development.mkdir()
            (development / "same.txt").write_bytes(b"same")
            (development / "different.txt").write_bytes(b"development")
            archive_path = root / "baseline.tar"
            with tarfile.open(archive_path, "w") as archive:
                for name, payload in (
                    ("same.txt", b"same"),
                    ("different.txt", b"baseline"),
                    ("public-only.txt", b"public"),
                ):
                    info = tarfile.TarInfo(name)
                    info.size = len(payload)
                    archive.addfile(info, io.BytesIO(payload))
            rows = archive_ledger(archive_path, development)
            relations = {row["path"]: row["development_relation"] for row in rows}
            self.assertEqual("EXACT_IN_DEVELOPMENT", relations["same.txt"])
            self.assertEqual("DIVERGENT_FROM_DEVELOPMENT", relations["different.txt"])
            self.assertEqual("PUBLIC_BASELINE_ONLY", relations["public-only.txt"])


if __name__ == "__main__":
    unittest.main()
