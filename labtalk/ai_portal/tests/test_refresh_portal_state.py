from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import refresh_portal_state


class RefreshPortalStateTests(unittest.TestCase):
    def test_default_scope_excludes_physical_storage_walk(self) -> None:
        labels = [step.label for step in refresh_portal_state.selected_steps(False)]
        self.assertNotIn("memory inventory", labels)
        self.assertNotIn("memory classification", labels)
        self.assertIn("seed budget", labels)
        self.assertIn("mandatory tracked onboarding", labels)
        self.assertIn("identifier status", labels)
        self.assertIn("Portal truth audit", labels)
        self.assertIn("recall graph tracked targets", labels)

    def test_f0_policy_gates_follow_tier0_generation(self) -> None:
        labels = [step.label for step in refresh_portal_state.STEPS]
        self.assertEqual(
            labels[:3],
            ["tier-0 state", "seed budget", "mandatory tracked onboarding"],
        )

    def test_f0_policy_gates_reuse_their_authoritative_tools(self) -> None:
        by_label = {step.label: step for step in refresh_portal_state.STEPS}
        self.assertEqual(
            by_label["seed budget"].relative_script,
            "tools/staging/check_seed_budget.py",
        )
        self.assertEqual(
            by_label["mandatory tracked onboarding"].relative_script,
            "labtalk/ai_portal/check_mandatory_tracked.py",
        )

    def test_storage_scope_preserves_inventory_before_classification(self) -> None:
        labels = [step.label for step in refresh_portal_state.selected_steps(True)]
        self.assertLess(labels.index("history summary"), labels.index("memory inventory"))
        self.assertLess(labels.index("memory inventory"), labels.index("memory classification"))
        self.assertLess(labels.index("memory classification"), labels.index("memory pilot manifest"))

    def test_deterministic_generators_use_check_mode(self) -> None:
        by_label = {step.label: step for step in refresh_portal_state.STEPS}
        self.assertEqual(by_label["tier-0 state"].check_args, ("--check",))
        self.assertEqual(by_label["identifier status"].check_args, ("--check",))
        self.assertEqual(by_label["feed status"].check_args, ("--check",))
        self.assertEqual(by_label["history summary"].check_args, ("--check",))

    def test_failure_output_is_bounded(self) -> None:
        rendered = refresh_portal_state.clipped("a" * 5000, limit=100)
        self.assertLess(len(rendered), 140)
        self.assertIn("output clipped", rendered)

    def test_check_summary_counts_successes_not_attempts(self) -> None:
        steps = (
            refresh_portal_state.RefreshStep("green", "green.py"),
            refresh_portal_state.RefreshStep("red", "red.py"),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(refresh_portal_state, "selected_steps", return_value=steps),
            mock.patch.object(refresh_portal_state, "run_step", side_effect=(True, False)),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            result = refresh_portal_state.main(["--check"])

        self.assertEqual(result, 1)
        self.assertIn("portal-state: check (control plane)", stdout.getvalue())
        self.assertIn("1/2 step(s) passed; failed: red", stderr.getvalue())

    def test_success_summary_reports_all_steps_passed(self) -> None:
        steps = (refresh_portal_state.RefreshStep("green", "green.py"),)
        stdout = io.StringIO()
        with (
            mock.patch.object(refresh_portal_state, "selected_steps", return_value=steps),
            mock.patch.object(refresh_portal_state, "run_step", return_value=True),
            contextlib.redirect_stdout(stdout),
        ):
            result = refresh_portal_state.main([])

        self.assertEqual(result, 0)
        self.assertIn("portal-state: PASS -- 1/1 step(s) passed", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
