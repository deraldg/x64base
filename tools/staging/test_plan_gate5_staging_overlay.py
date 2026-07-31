from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "staging"))

from plan_gate5_staging_overlay import (  # noqa: E402
    expand_entry,
    git_blob_oid,
    parse_delta_candidate,
)


class Gate5StagingOverlayPlanTests(unittest.TestCase):
    def test_delta_parser_reads_only_text_fence_entries(self) -> None:
        text = "# title\n\n```text\na/*.md\n# comment\nb/file.json\n```\n"
        self.assertEqual(["a/*.md", "b/file.json"], parse_delta_candidate(text))

    def test_expand_entry_supports_glob_and_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("a", encoding="utf-8")
            (root / "docs" / "b.txt").write_text("b", encoding="utf-8")
            self.assertEqual([root / "docs" / "a.md"], expand_entry(root, "docs/*.md"))
            self.assertEqual(2, len(expand_entry(root, "docs")))

    def test_git_blob_oid_matches_sha1_shape(self) -> None:
        value = b"hello\n"
        expected = hashlib.sha1(b"blob 6\0hello\n").hexdigest()  # noqa: S324
        self.assertEqual(expected, git_blob_oid(value, "sha1"))


if __name__ == "__main__":
    unittest.main()
