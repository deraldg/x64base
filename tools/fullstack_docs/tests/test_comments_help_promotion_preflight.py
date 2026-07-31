from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.fullstack_docs.build_comments_help_promotion_preflight import (
    HELP_FILES,
    build_preflight,
)


class PromotionPreflightTests(unittest.TestCase):
    def test_builds_hash_bound_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            run = root / "DOCFLUSH-20260722-001"
            out = run / "promotion_preflight"

            for path in (
                repo / "dottalkpp/data/comments/SRCFILE.dbf",
                repo / "dottalkpp/data/indexes/comments/SRCFILE.cdx",
                repo / "dottalkpp/data/lmdb/comments/SRCFILE.cdx.d/data.mdb",
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(path.name.encode("ascii"))

            help_live = repo / "dottalkpp/data/help"
            help_candidate = run / "help_refresh_candidate/isolated_help_v2"
            for name in HELP_FILES:
                (help_live / name).parent.mkdir(parents=True, exist_ok=True)
                (help_candidate / name).parent.mkdir(parents=True, exist_ok=True)
                (help_live / name).write_bytes(("live-" + name).encode("ascii"))
                (help_candidate / name).write_bytes(("candidate-" + name).encode("ascii"))

            comments_package = run / "comments_reharvest/fullstack_20260722_contracts_v2"
            comments_candidate = comments_package / "candidate_source_comment_metadata_import_v2"
            comments_candidate.mkdir(parents=True)
            candidate = comments_candidate / "SRCFILE_IMPORT.csv"
            candidate.write_text("FILEID\n1\n", encoding="utf-8")
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest().upper()
            (comments_package / "source_comment_reharvest_manifest_v1.json").write_text(
                json.dumps({
                    "candidate_files": {
                        candidate.name: {
                            "bytes": candidate.stat().st_size,
                            "rows": 1,
                            "sha256": digest,
                        }
                    }
                }),
                encoding="utf-8",
            )

            payload = build_preflight(repo, run, out)
            self.assertEqual(payload["help"]["files"], 9)
            self.assertEqual(payload["comments"]["candidate_files"], 1)
            self.assertEqual(payload["comments"]["live_files"], 3)
            self.assertFalse(payload["live_mutation_authorized"])
            self.assertTrue((out / "help_live_candidate_sha256_manifest_v1.csv").is_file())


if __name__ == "__main__":
    unittest.main()
