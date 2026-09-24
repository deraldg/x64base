"""Tier 0 must never print "Staleness warnings: none" over inputs it failed to read.

Regression for proof.ai_portal.reentry_43day_20260923, P1. Git is stubbed, so
these tests run anywhere, including a sandbox that must not run git at all.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import generate_tier0_state as t0

TARGET_INDENTED = (
    "# Current Target\n\n"
    "    status      : active\n"
    "    updated_utc : 2026-07-31T18:50:00Z\n\n"
    "## NEXT TARGET -- a heading\n"
)


def make_tree(root: Path, target: str = TARGET_INDENTED,
              closeouts: tuple[str, ...] = ("SESSION_CLOSEOUT_A_2026-09-23.md",)) -> None:
    (root / "docs" / "agents").mkdir(parents=True)
    (root / "docs" / "maintenance").mkdir(parents=True)
    (root / "docs" / "agents" / "CURRENT_TARGET.md").write_text(target, encoding="utf-8")
    for name in closeouts:
        (root / "docs" / "maintenance" / name).write_text("x\n", encoding="utf-8")


def fake_git(answers: dict[str, str]):
    """Return a git stub keyed on the first two argv words; unknown -> '' (failure)."""
    def stub(root, *args):
        return answers.get(" ".join(args[:2]), "")
    return stub


HEALTHY = {
    "rev-parse --abbrev-ref": "development",
    "rev-parse --short": "abc1234",
    "log -1": "abc1234",
    "rev-list --count": "0",
    "ls-files --": "docs/maintenance/SESSION_CLOSEOUT_A_2026-09-23.md",
}


def warnings_of(body: str) -> str:
    return body.split("## Staleness warnings", 1)[1].split("##", 1)[0]


class Tier0Tests(unittest.TestCase):
    def render(self, answers, **tree):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_tree(root, **tree)
            with mock.patch.object(t0, "git", fake_git(answers)):
                return t0.render(root)

    def test_indented_updated_utc_is_read(self) -> None:
        body = self.render(HEALTHY)
        self.assertIn("updated       : 2026-07-31T18:50:00Z", body)

    def test_healthy_inputs_can_still_say_none(self) -> None:
        # The fix must not make "none" unreachable -- a gate that always warns
        # is a gate nobody reads.
        self.assertIn("- none", warnings_of(self.render(HEALTHY)))

    def test_git_unavailable_is_not_reported_as_healthy(self) -> None:
        w = warnings_of(self.render({}))
        self.assertNotIn("- none", w)
        self.assertIn("Could not measure", w)
        self.assertIn("INCOMPLETE", w)

    def test_unreadable_target_stamp_warns(self) -> None:
        w = warnings_of(self.render(HEALTHY, target="# Current Target\n\n## X\n"))
        self.assertIn("declared target stamp", w)

    def test_uncommitted_newest_closeout_warns(self) -> None:
        answers = dict(HEALTHY)
        answers["log -1"] = ""        # no commit touches the newest closeout
        answers["ls-files --"] = ""
        body = self.render(answers)
        self.assertIn("commits behind HEAD : not committed", body)
        self.assertIn("is on disk but in no commit", warnings_of(body))

    def test_older_widowed_closeout_warns(self) -> None:
        body = self.render(HEALTHY, closeouts=(
            "SESSION_CLOSEOUT_A_2026-09-23.md",
            "SESSION_CLOSEOUT_B_2026-09-20.md",
        ))
        w = warnings_of(body)
        self.assertIn("SESSION_CLOSEOUT_B_2026-09-20.md", w)
        self.assertNotIn("- none", w)


if __name__ == "__main__":
    unittest.main()
