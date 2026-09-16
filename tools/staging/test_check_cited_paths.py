"""Focused regressions for the local citation gate transport layer.

The content-level cross-repo cases remain in ``check_cited_paths.py --selftest``.
These tests protect the two host failures that selftest did not cover: Windows
command-line length and locale-dependent decoding of Git output.
"""

from types import SimpleNamespace
import unittest
from unittest import mock

import check_cited_paths as gate


class GitTransportTests(unittest.TestCase):
    @mock.patch.object(gate.subprocess, "run")
    def test_git_decodes_repository_bytes_as_utf8_with_replacement(self, run):
        run.return_value = SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

        self.assertEqual(gate.git(["status"]), "ok\n")

        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs["encoding"], "utf-8")
        self.assertEqual(kwargs["errors"], "replace")
        self.assertTrue(kwargs["text"])

    @mock.patch.object(gate.subprocess, "run")
    def test_git_failure_is_not_rewritten_as_empty_output(self, run):
        run.return_value = SimpleNamespace(
            returncode=128,
            stdout="",
            stderr="fatal: synthetic failure",
        )

        with self.assertRaises(gate.GitCommandError):
            gate.git(["ls-files"])


class BulkPathTests(unittest.TestCase):
    @mock.patch.object(gate, "git")
    def test_tracked_query_lists_index_once_without_path_arguments(self, git):
        paths = ["docs/p%04d.md" % n for n in range(700)]
        git.return_value = "\n".join(paths + ["src/unrelated.cpp"]) + "\n"

        self.assertEqual(gate.tracked_repo_paths(paths), set(paths))
        git.assert_called_once_with(["ls-files"])

    @mock.patch.object(gate, "git")
    def test_ignore_query_batches_bulk_paths_below_windows_limit(self, git):
        paths = ["docs/%s/p%04d.md" % ("x" * 90, n) for n in range(700)]
        git.return_value = "docs/p0001.md\n"

        self.assertEqual(
            gate.ignored_repo_paths(paths),
            {"docs/p0001.md"},
        )
        self.assertGreater(git.call_count, 1)
        seen = set()
        for call in git.call_args_list:
            args, kwargs = call
            command = args[0]
            self.assertEqual(command[:2], ["check-ignore", "--"])
            self.assertEqual(kwargs["ok"], (0, 1))
            self.assertLessEqual(
                sum(len(a) + 3 for a in command),
                gate.WINDOWS_ARG_BUDGET,
            )
            seen.update(command[2:])
        self.assertEqual(seen, set(paths))


if __name__ == "__main__":
    unittest.main()
