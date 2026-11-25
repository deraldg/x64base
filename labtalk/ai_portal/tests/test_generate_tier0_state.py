"""Tier 0 must never print "Staleness warnings: none" over inputs it failed to read.

Regression for proof.ai_portal.reentry_43day_20260923, P1. Git is stubbed, so
these tests run anywhere, including a sandbox that must not run git at all.
"""
from __future__ import annotations

import contextlib
import io
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


class LaneHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.write("coordination/aif/AIF-171.claim", "aif: AIF-171\n")

    def write(self, rel: str, body: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    def records(self, *paths: str) -> None:
        self.write(
            "labtalk/registries/runs.d/TEST-RUN.yaml",
            "run_id: TEST-RUN\nlanes: [AIF-171]\ncloseouts:\n"
            + "".join(f"- {path}\n" for path in paths),
        )

    def report(self, name: str, hour: str) -> None:
        self.write(
            name, f"---\nai_report_audit:\n  recorded_at_utc: 2026-10-15T{hour}:00Z\n---\n# Closeout\n"
        )

    def resolve(self, *git_answers: tuple[tuple[str, ...], str], lane: str = "AIF-171"):
        answers = {("rev-parse", "HEAD"): "HEAD-oid", **dict(git_answers)}
        with mock.patch.object(t0, "git", side_effect=lambda root, *args: answers.get(args, "")):
            return t0.lane_handoff(self.root, lane)

    def test_same_day_uses_recorded_utc_and_reports_local_visibility(self) -> None:
        latest = "docs/alpha_2026-10-15.md"
        older = "docs/zeta_2026-10-15.md"
        companion = "docs/legacy.md"
        self.records(latest, older, companion)
        self.report(latest, "18:02")
        self.report(older, "09:21")
        self.write(companion, "# Companion without a recorded time\n")
        body, code = self.resolve()
        self.assertEqual(code, 0)
        self.assertIn(f"closeout: {latest}", body)
        self.assertNotIn(f"closeout: {older}", body)
        self.assertIn("artifact: local-only", body)
        self.assertIn("local-only binding", body)
        self.assertIn("unranked legacy companion", body)

    def test_legacy_name_comes_from_registry_and_uses_labeled_git_time(self) -> None:
        name = "docs/GOOD_NEIGHBOR_CLOSEOUT.md"
        self.records(name)
        self.write(name, "# Legacy closeout\n")
        body, code = self.resolve(
            (("rev-parse", "--verify", f"HEAD:{name}"), "artifact-oid"),
            (("hash-object", "--", name), "artifact-oid"),
            (("log", "-1", "--format=%cI", "--", name), "2026-10-15T11:02:00-07:00"),
            (("rev-parse", "--verify", "@{u}"), "upstream-oid"),
        )
        self.assertEqual(code, 0)
        self.assertIn("2026-10-15T18:02:00+00:00 (Git last-change UTC", body)
        self.assertIn("artifact: committed at HEAD", body)
        self.assertIn("artifact at configured upstream: absent", body)

    def test_absent_candidate_blocks_selection(self) -> None:
        self.records("docs/missing.md", "docs/older.md")
        self.report("docs/older.md", "09:21")
        body, code = self.resolve()
        self.assertEqual(code, 3)
        self.assertIn("absent from worktree: docs/missing.md", body)
        self.assertNotIn("closeout: docs/older.md", body)

    def test_equal_recorded_stamps_are_ambiguous(self) -> None:
        self.records("docs/a.md", "docs/b.md")
        self.report("docs/a.md", "18:02")
        self.report("docs/b.md", "18:02")
        body, code = self.resolve()
        self.assertEqual(code, 3)
        self.assertIn("equally recent UTC records", body)

    def test_an_unclaimed_lane_cannot_select_a_closeout(self) -> None:
        body, code = self.resolve(lane="AIF-999")
        self.assertEqual(code, 3)
        self.assertIn("No durable claim", body)


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

    def test_check_accepts_transport_and_generation_metadata_difference(self) -> None:
        fresh = "# Tier 0\n    generated_utc : 2026-10-12T20:00:00Z\nHEAD: abc\n"
        persisted = "# Tier 0\r\n    generated_utc : 2026-10-11T20:00:00Z\r\nHEAD: abc\r\n"
        self.assertEqual(
            t0.normalized_for_check(fresh),
            t0.normalized_for_check(persisted),
        )

    def test_check_rejects_a_stale_persisted_projection(self) -> None:
        fresh = "# Tier 0\n    generated_utc : 2026-10-12T20:00:00Z\nHEAD: new\n"
        stale = "# Tier 0\n    generated_utc : 2026-10-12T19:00:00Z\nHEAD: old\n"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / t0.OUTPUT_RELATIVE
            target.parent.mkdir(parents=True)
            target.write_text(stale, encoding="utf-8")
            stderr = io.StringIO()
            with (
                mock.patch.object(t0, "repo_root", return_value=root),
                mock.patch.object(t0, "render", return_value=fresh),
                contextlib.redirect_stderr(stderr),
            ):
                result = t0.main(["--check"])

        self.assertEqual(result, 3)
        self.assertIn("tier0: stale", stderr.getvalue())

    def test_check_rejects_a_missing_persisted_projection(self) -> None:
        fresh = "# Tier 0\n    generated_utc : 2026-10-12T20:00:00Z\nHEAD: abc\n"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            stderr = io.StringIO()
            with (
                mock.patch.object(t0, "repo_root", return_value=root),
                mock.patch.object(t0, "render", return_value=fresh),
                contextlib.redirect_stderr(stderr),
            ):
                result = t0.main(["--check"])

        self.assertEqual(result, 3)
        self.assertIn("tier0: stale -- missing", stderr.getvalue())

    def test_check_accepts_a_current_persisted_projection(self) -> None:
        fresh = "# Tier 0\n    generated_utc : 2026-10-12T20:00:00Z\nHEAD: abc\n"
        persisted = "# Tier 0\n    generated_utc : 2026-10-12T19:00:00Z\nHEAD: abc\n"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / t0.OUTPUT_RELATIVE
            target.parent.mkdir(parents=True)
            target.write_text(persisted, encoding="utf-8")
            stdout = io.StringIO()
            with (
                mock.patch.object(t0, "repo_root", return_value=root),
                mock.patch.object(t0, "render", return_value=fresh),
                contextlib.redirect_stdout(stdout),
            ):
                result = t0.main(["--check"])

        self.assertEqual(result, 0)
        self.assertIn("tier0: current", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
