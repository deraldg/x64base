"""Tests for the index.lock guard's settle window (R138, 2026-09-01).

WHY THIS EXISTS. On 2026-09-01 the prepush gate hard-failed twice in three
minutes on a 668857-byte `.git/index.lock` that was gone seconds later both
times -- byte-identical across runs, with `.git/index` untouched. It was a live
git mid-operation, not wreckage. The guard stat'd the lock once, returned the
STALE exit code, and the gate summarized it as "a stale index.lock is present.
Remove it" -- while the guard's own output for that same lock said "not the
known-stale signature -- do not delete it blindly." The check proved NOT STALE
and the summary asserted STALE. Anyone following the summary deletes a live
git's lock.

WHY IT IS TESTED RATHER THAN REASONED ABOUT. The condition is a RACE. It cannot
be reproduced on demand against a real repository, which is exactly how the
single-stat version survived from 2026-07-31 to 2026-09-01 without anyone
noticing it could not tell a busy repo from a broken one. A fabricated root
makes all four states reproducible in under a second.

FOUR STATES, and the pairs that matter are 2-vs-4 and 3-vs-4:

  1. no lock                       -> 0, not wedged
  2. zero-byte lock                -> 2, STALE, decided on sight
  3. non-empty lock that clears    -> 0, a git finished while we watched
  4. non-empty lock that persists  -> 5, WAIT, and it is not code 2

The falsification that matters is 3 -> 0. If it ever returns 2 or 5 again, the
gate is back to failing on healthy repositories.
"""

import pathlib
import sys
import tempfile
import threading
import unittest

import check_sandbox_git_guard as guard


def _root_with(tmp: str, lock_bytes: bytes | None) -> pathlib.Path:
    """A fabricated repository root. No git is involved anywhere in this file:
    the guard only ever stats a path, so a directory named `.git` is a complete
    and honest stand-in, and the test cannot wedge the real repository."""
    root = pathlib.Path(tmp)
    (root / ".git").mkdir()
    (root / "AI_README.md").write_text("fixture\n", encoding="utf-8")
    if lock_bytes is not None:
        (root / ".git" / "index.lock").write_bytes(lock_bytes)
    return root


class LockSettleTests(unittest.TestCase):
    def setUp(self):
        # Keep the real sample COUNT so the loop shape is under test, and
        # shorten only the interval. A test that changed both would not be
        # exercising the code that ships.
        self._saved = guard.SETTLE_SECONDS
        guard.SETTLE_SECONDS = 0.02

    def tearDown(self):
        guard.SETTLE_SECONDS = self._saved

    def test_no_lock_is_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(guard.check_lock(_root_with(tmp, None)), 0)

    def test_zero_byte_lock_is_stale_and_hard(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(guard.check_lock(_root_with(tmp, b"")), 2)

    def test_zero_byte_lock_is_not_waited_on(self):
        # Decided on sight: the stale case must not pay the settle window, and
        # must not be rescued by a deletion racing in behind it.
        with tempfile.TemporaryDirectory() as tmp:
            root = _root_with(tmp, b"")
            guard.SETTLE_SECONDS = 5.0  # would be visible if it were slept on
            self.assertEqual(guard.check_lock(root), 2)

    def test_non_empty_lock_that_clears_is_not_a_failure(self):
        # THE ONE THAT WAS BROKEN. A live git wrote its refreshed index into the
        # lock and renamed it away while the guard was looking.
        with tempfile.TemporaryDirectory() as tmp:
            root = _root_with(tmp, b"DIRC" + b"\x00" * 4096)
            lock = root / ".git" / "index.lock"
            threading.Timer(0.03, lock.unlink).start()
            self.assertEqual(guard.check_lock(root), 0)

    def test_non_empty_lock_that_persists_is_advisory_not_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _root_with(tmp, b"DIRC" + b"\x00" * 4096)
            rc = guard.check_lock(root)
            self.assertEqual(rc, 5)
            self.assertNotEqual(rc, 2, "a busy repo must never report as STALE")


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    unittest.main()
