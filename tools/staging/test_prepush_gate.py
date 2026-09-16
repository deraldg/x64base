"""Tests for the prepush gate's TIER0-only guard (AIF-078, 2026-08-29).

WHY THIS GUARD EXISTS. TIER0_STATE.md rides in every commit by design, so the
staged set is never empty and git's own "nothing to commit" refusal -- the
safety net that normally catches a re-run of an already-successful commit --
can never fire in this repository. Every accidental re-run SUCCEEDS, carrying
the previous commit's message and none of its content. It happened three times
in one session before anyone named it.

WHY IT IS TESTED HERE RATHER THAN BY HAND. The failure is an accident: you
cannot ask someone to reproduce it on demand, so an untested guard would rot
silently and nobody would find out until the fourth occurrence. The predicate
is kept pure in prepush_gate for exactly this reason -- the same shape as
repository_role_guard.validate_worktree, and for the same reason.
"""

import contextlib
import io
from types import SimpleNamespace
import unittest
from unittest import mock

import prepush_gate as gate

TIER0 = gate.TIER0_STATE_PATH
REAL_WORK = "src/cli/cmd_regression.cpp"


class Tier0OnlyPredicateTests(unittest.TestCase):
    def test_tier0_alone_is_caught(self):
        self.assertTrue(gate.is_tier0_only([TIER0], None, False))

    def test_windows_separators_still_match(self):
        self.assertTrue(
            gate.is_tier0_only([TIER0.replace("/", "\\")], None, False))

    def test_tier0_with_real_work_beside_it_is_a_normal_commit(self):
        # The overwhelmingly common case -- every real commit in this repo
        # carries TIER0 as a passenger. The guard must be invisible here.
        self.assertFalse(gate.is_tier0_only([TIER0, REAL_WORK], None, False))
        self.assertFalse(gate.is_tier0_only([REAL_WORK, TIER0], None, False))

    def test_a_different_lone_file_is_not_this_guard_s_business(self):
        self.assertFalse(gate.is_tier0_only([REAL_WORK], None, False))

    def test_empty_set_is_not_this_guard_s_business(self):
        # main() returns "clean" before reaching here; asserted so a future
        # reorder cannot turn an empty index into a BLOCKED message.
        self.assertFalse(gate.is_tier0_only([], None, False))

    def test_acknowledgement_lets_a_deliberate_refresh_through(self):
        self.assertFalse(gate.is_tier0_only([TIER0], None, True))

    def test_range_scope_is_exempt(self):
        # A --range check reads history that may already contain such commits.
        # Blocking a push on a mistake already made is a permanently red gate,
        # and a permanently red gate is a switched-off gate.
        self.assertFalse(gate.is_tier0_only([TIER0], "HEAD..@{u}", False))
        self.assertFalse(gate.is_tier0_only([TIER0], "HEAD~3..HEAD", False))


class Tier0OnlyMessageTests(unittest.TestCase):
    """The message is load-bearing, so it is asserted rather than assumed."""

    def setUp(self):
        self.text = " ".join(gate.tier0_only_message())

    def test_it_sends_the_reader_to_the_log_before_anything_else(self):
        self.assertIn("git log --oneline -3", self.text)

    def test_it_never_names_a_destructive_verb(self):
        # THE POINT OF THE WHOLE FILE. The papercut cost nothing; the reflex to
        # undo it cost a concurrent session 38 files of uncommitted work when
        # the reset reached for --hard in a shared worktree. Unstaged changes
        # never enter the object database, so none of it was recoverable. This
        # message must not put that idea in the reader's head.
        for verb in ("reset", "--hard", "revert", "rebase", "clean", "checkout"):
            self.assertNotIn(verb, self.text.lower())

    def test_it_says_the_work_is_probably_already_committed(self):
        self.assertIn("already", self.text)

    def test_it_names_the_way_out(self):
        self.assertIn("--allow-tier0-only", self.text)
        self.assertIn("X64BASE_ALLOW_TIER0_ONLY", self.text)


class PortalCheckExecutionTests(unittest.TestCase):
    """A child crash is not one of a check's documented outcomes."""

    @mock.patch.object(gate.os.path, "exists", return_value=True)
    @mock.patch.object(gate, "run_git", return_value="D:/code/ccode\n")
    @mock.patch.object(gate.subprocess, "run")
    def test_unexpected_child_exit_is_a_gate_execution_error(
        self, run, _run_git, _exists
    ):
        run.return_value = SimpleNamespace(returncode=1)

        with self.assertRaises(gate.PortalCheckExecutionError):
            gate._run_portal_check(
                "tools/staging/check_cited_paths.py", [], (0, 3))

    @mock.patch.object(gate.os.path, "exists", return_value=True)
    @mock.patch.object(gate, "run_git", return_value="D:/code/ccode\n")
    @mock.patch.object(gate.subprocess, "run")
    def test_documented_advisory_exit_is_preserved(
        self, run, _run_git, _exists
    ):
        run.return_value = SimpleNamespace(returncode=3)

        self.assertEqual(
            gate._run_portal_check(
                "tools/staging/check_cited_paths.py", [], (0, 3)),
            3,
        )

    @mock.patch.object(gate.os.path, "exists", return_value=True)
    @mock.patch.object(gate, "run_git", return_value="D:/code/ccode\n")
    @mock.patch.object(gate.subprocess, "run", side_effect=OSError("synthetic"))
    def test_launch_failure_is_not_rewritten_as_skipped(
        self, _run, _run_git, _exists
    ):
        with self.assertRaises(gate.PortalCheckExecutionError):
            gate._run_portal_check(
                "tools/staging/check_cited_paths.py", [], (0, 3))

    @mock.patch.object(gate, "main")
    def test_cli_blocks_and_never_prints_pass_after_child_crash(self, main):
        main.side_effect = gate.PortalCheckExecutionError(
            "tools/staging/check_cited_paths.py",
            "unexpected exit 1; expected one of (0, 3)",
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = gate.cli()

        combined = stdout.getvalue() + stderr.getvalue()
        self.assertEqual(rc, 2)
        self.assertIn("BLOCKED", combined)
        self.assertIn("FAIL (exit 2)", combined)
        self.assertNotIn("prepush-gate: PASS", combined)


if __name__ == "__main__":
    unittest.main()
