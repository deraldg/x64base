"""Tests for the mandatory-tracked checker's path normalization.

WHY THIS FILE EXISTS. This checker was written on 2026-07-31 after
`repository_role_guard.py` shipped untracked while `prepush_gate.py`, which
invokes it, was tracked -- a clone got a gate whose first dependency did not
exist. On 2026-08-29 the SAME defect was found again, inside the checker: it
normalized `.\\path.ps1` by stripping before replacing separators, producing a
leading slash that matched no file, and the is_file() filter then dropped it in
silence. 27 references in the entry documents, 10 survived. Five scripts the
portal instructs you to run were untracked while this gate reported PASS.

A guard whose own input normalization discards the cases it exists for cannot
fail. It reports PASS over a smaller set every time, and never says the set
shrank. So the normalization is pinned here rather than trusted -- particularly
the backslash spelling, because AI_README.md uses it (`.\\run-erp.ps1`, line
560) and nothing else in the tree would notice if it stopped being understood.
"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import check_mandatory_tracked as checker


def portal_saying(body, files=()):
    """Build a throwaway repo root whose AI_README.md contains `body`."""
    root = Path(tempfile.mkdtemp())
    (root / "AI_README.md").write_text(body, encoding="utf-8")
    (root / "AI_PORTAL.md").write_text("", encoding="utf-8")
    for rel in files:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")
    return root


class ScriptNormalizationTests(unittest.TestCase):
    def test_windows_spelling_is_understood(self):
        # THE REGRESSION. Before the fix this produced "/run-erp.ps1" and was
        # dropped without a word.
        root = portal_saying("Run `.\\run-erp.ps1` to start.", ["run-erp.ps1"])
        _, scripts = checker.declared(root)
        self.assertIn("run-erp.ps1", scripts)

    def test_posix_spelling_still_works(self):
        root = portal_saying("Run `./run-erp.ps1` to start.", ["run-erp.ps1"])
        _, scripts = checker.declared(root)
        self.assertIn("run-erp.ps1", scripts)

    def test_bare_spelling_still_works(self):
        root = portal_saying("Run `run-erp.ps1` to start.", ["run-erp.ps1"])
        _, scripts = checker.declared(root)
        self.assertIn("run-erp.ps1", scripts)

    def test_the_three_spellings_collapse_to_one_entry(self):
        # Otherwise the reported count inflates with the document's typography.
        root = portal_saying(
            "`.\\run-erp.ps1` and `./run-erp.ps1` and `run-erp.ps1`",
            ["run-erp.ps1"],
        )
        _, scripts = checker.declared(root)
        self.assertEqual({s for s in scripts if s.endswith("run-erp.ps1")},
                         {"run-erp.ps1"})

    def test_nested_windows_path_is_understood(self):
        root = portal_saying(
            "Run `tools\\staging\\prepush_gate.py` first.",
            ["tools/staging/prepush_gate.py"],
        )
        _, scripts = checker.declared(root)
        self.assertIn("tools/staging/prepush_gate.py", scripts)

    def test_nothing_normalizes_to_an_absolute_path(self):
        # The precise failure mode: a leading separator matches nothing, and
        # the is_file() filter removes the evidence.
        root = portal_saying(
            "`.\\a.ps1` `.\\b\\c.py` `./d.sh` `e/f.py`",
            ["a.ps1", "b/c.py", "d.sh", "e/f.py"],
        )
        _, scripts = checker.declared(root)
        self.assertEqual(len(scripts), 4)
        for s in scripts:
            self.assertFalse(s.startswith("/"), f"{s} normalized to absolute")
            self.assertNotIn("\\", s, f"{s} kept a backslash")

    def test_missing_explicit_paths_survive_extraction(self):
        root = portal_saying("Run `.\\ghost.ps1` after reading `docs\\missing.md`.")
        docs, scripts = checker.declared(root)
        self.assertIn("ghost.ps1", scripts)
        self.assertIn("docs/missing.md", docs)

    def test_missing_bare_prose_names_are_not_explicit_paths(self):
        root = portal_saying("The old `ghost.ps1` read `missing.md`.")
        docs, scripts = checker.declared(root)
        self.assertNotIn("ghost.ps1", scripts)
        self.assertNotIn("missing.md", docs)

    def test_gate_distinguishes_an_absent_tracked_doc_from_a_local_script(self):
        root = portal_saying("[Read first](gone.md#start) and run `./local.py`.", ["local.py"])
        have = set(checker.ENTRY_DOCS) | set(checker.ALWAYS_READ) | {"gone.md"}
        for rel in checker.ALWAYS_READ:
            (root / rel).touch()
        stdout = io.StringIO()
        with (
            mock.patch.object(checker, "repo_root", return_value=root),
            mock.patch.object(checker, "tracked", return_value=have),
            contextlib.redirect_stdout(stdout),
        ):
            self.assertEqual(checker.main(), 2)
        self.assertIn("MISSING PATH      gone.md", stdout.getvalue())
        self.assertIn("UNTRACKED SCRIPT  local.py", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
