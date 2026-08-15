import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import repository_role_guard as guard


class RepositoryRoleGuardTests(unittest.TestCase):
    def test_known_roots_have_distinct_roles(self):
        self.assertIs(guard.detect_role(guard.DEVELOPMENT_ROOT), guard.DEVELOPMENT_ROLE)
        self.assertIs(guard.detect_role(guard.STAGING_ROOT), guard.STAGING_ROLE)

    def test_development_worktree_requires_development_branch(self):
        self.assertEqual(
            guard.validate_worktree(guard.DEVELOPMENT_ROLE, "development"),
            [],
        )
        self.assertTrue(guard.validate_worktree(guard.DEVELOPMENT_ROLE, "main"))

    def test_staging_worktree_requires_main_branch(self):
        self.assertEqual(
            guard.validate_worktree(guard.STAGING_ROLE, "main"),
            [],
        )
        self.assertTrue(
            guard.validate_worktree(guard.STAGING_ROLE, "development")
        )

    def test_explicit_promotion_branch_is_narrow(self):
        self.assertEqual(
            guard.validate_worktree(
                guard.STAGING_ROLE,
                "promotion/source-slice",
                allow_staging_branch=True,
            ),
            [],
        )
        self.assertTrue(
            guard.validate_worktree(
                guard.STAGING_ROLE,
                "feature/unrelated",
                allow_staging_branch=True,
            )
        )

    def test_development_may_push_development_only(self):
        allowed = [
            (
                "refs/heads/development",
                "1" * 40,
                "refs/heads/development",
                "2" * 40,
            )
        ]
        forbidden = [
            (
                "refs/heads/development",
                "1" * 40,
                "refs/heads/main",
                "2" * 40,
            )
        ]
        self.assertEqual(
            guard.validate_push_updates(guard.DEVELOPMENT_ROLE, allowed),
            [],
        )
        self.assertTrue(
            guard.validate_push_updates(guard.DEVELOPMENT_ROLE, forbidden)
        )

    def test_staging_may_push_main_only(self):
        allowed = [
            ("refs/heads/main", "1" * 40, "refs/heads/main", "2" * 40)
        ]
        forbidden = [
            (
                "refs/heads/development",
                "1" * 40,
                "refs/heads/development",
                "2" * 40,
            )
        ]
        self.assertEqual(
            guard.validate_push_updates(
                guard.STAGING_ROLE,
                allowed,
                development_ancestor_override=False,
            ),
            [],
        )
        self.assertTrue(
            guard.validate_push_updates(guard.STAGING_ROLE, forbidden)
        )

    def test_staging_rejects_main_tip_containing_development(self):
        updates = [
            ("refs/heads/main", "1" * 40, "refs/heads/main", "2" * 40)
        ]
        self.assertTrue(
            guard.validate_push_updates(
                guard.STAGING_ROLE,
                updates,
                development_ancestor_override=True,
            )
        )

    def test_deletions_and_tags_are_rejected(self):
        deletion = [
            (
                "(delete)",
                guard.ZERO_SHA,
                "refs/heads/development",
                "2" * 40,
            )
        ]
        tag = [
            ("refs/tags/v1", "1" * 40, "refs/tags/v1", guard.ZERO_SHA)
        ]
        self.assertTrue(
            guard.validate_push_updates(guard.DEVELOPMENT_ROLE, deletion)
        )
        self.assertTrue(
            guard.validate_push_updates(guard.DEVELOPMENT_ROLE, tag)
        )

    def test_hook_install_preserves_existing_pre_push(self):
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run(
                ["git", "init", "-q", temp],
                check=True,
                capture_output=True,
            )
            hook_dir = Path(temp) / ".git" / "hooks"
            pre_push = hook_dir / "pre-push"
            original = "#!/bin/sh\nprintf 'existing hook\\n'\n"
            pre_push.write_text(original, encoding="utf-8", newline="\n")
            os.chmod(pre_push, 0o755)

            guard.install_hooks(temp)

            preserved = hook_dir / "pre-push.x64base-preserved"
            self.assertEqual(preserved.read_text(encoding="utf-8"), original)
            wrapper = pre_push.read_text(encoding="utf-8")
            self.assertIn("repository_role_guard.py", wrapper)
            self.assertIn("pre-push.x64base-preserved", wrapper)
            self.assertIn('cat > "$UPDATES"', wrapper)


class BranchCutFromMainTests(unittest.TestCase):
    """The PR-branch role added 2026-08-14.

    These build a real repository with real worktrees rather than asserting on
    pure functions, because every condition the role checks is a fact about Git
    state -- linked-ness, and which refs are ancestors of HEAD. A stubbed test
    here would pass while the guard misread a real tree, which is the failure
    mode this whole file exists to prevent.
    """

    def _git(self, cwd, *args):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=str(cwd),
            check=True,
            capture_output=True,
        )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        origin = base / "origin.git"
        self.dev = base / "dev"
        self.wt_main = base / "wt-main"
        self.wt_dev = base / "wt-dev"

        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True,
                       capture_output=True)
        subprocess.run(["git", "init", "-q", str(self.dev)], check=True,
                       capture_output=True)
        self._git(self.dev, "remote", "add", "origin", str(origin))
        (self.dev / "f.txt").write_text("a\n", encoding="utf-8")
        self._git(self.dev, "add", ".")
        self._git(self.dev, "commit", "-qm", "base")
        self._git(self.dev, "branch", "-M", "main")
        self._git(self.dev, "push", "-q", "origin", "main")
        self._git(self.dev, "checkout", "-qb", "development")
        (self.dev / "d.txt").write_text("d\n", encoding="utf-8")
        self._git(self.dev, "add", ".")
        self._git(self.dev, "commit", "-qm", "development work")
        self._git(self.dev, "push", "-q", "origin", "development")
        self._git(self.dev, "fetch", "-q", "origin")
        self._git(self.dev, "worktree", "add", "-b", "ci/fix",
                  str(self.wt_main), "origin/main")
        self._git(self.dev, "worktree", "add", "-b", "ci/bad",
                  str(self.wt_dev), "development")

        # Point the development role at this throwaway tree for the duration.
        self._saved = guard.DEVELOPMENT_ROLE
        guard.DEVELOPMENT_ROLE = guard.RepositoryRole(
            name="development",
            root=str(self.dev),
            required_branch="development",
            allowed_remote_branch="development",
        )

    def tearDown(self):
        guard.DEVELOPMENT_ROLE = self._saved
        self._tmp.cleanup()

    def test_branch_cut_from_main_is_allowed(self):
        role = guard.detect_branch_cut_role(str(self.wt_main), "ci/fix")
        self.assertIsNotNone(role)
        self.assertEqual(role.allowed_remote_branch, "ci/fix")
        self.assertEqual(guard.validate_worktree(role, "ci/fix"), [])

    def test_branch_carrying_development_history_is_refused(self):
        """The load-bearing one: no smuggling development toward main."""
        self.assertIsNone(guard.detect_branch_cut_role(str(self.wt_dev), "ci/bad"))

    def test_worktree_cannot_be_used_to_reach_main_or_development(self):
        for branch in ("main", "development"):
            with self.subTest(branch=branch):
                self.assertIsNone(
                    guard.detect_branch_cut_role(str(self.wt_main), branch)
                )

    def test_main_worktree_is_not_a_branch_cut(self):
        self.assertIsNone(guard.detect_branch_cut_role(str(self.dev), "ci/fix"))

    def test_undeclared_repository_is_still_refused(self):
        stray = Path(self._tmp.name) / "stray"
        subprocess.run(["git", "init", "-q", str(stray)], check=True,
                       capture_output=True)
        self.assertIsNone(guard.detect_role(str(stray)))
        self.assertIsNone(guard.detect_branch_cut_role(str(stray), "ci/fix"))

    def test_independent_clone_of_the_same_origin_is_refused(self):
        """A separate CLONE is not a linked worktree, even cut from origin/main.

        Added after mutation testing: deleting the linked-worktree requirement
        broke no test, because the only "undeclared" case exercised was a bare
        `git init` with no origin/main -- refused by the ancestor check instead,
        for reasons that had nothing to do with linked-ness. A clone satisfies
        every OTHER condition, so it is the case that actually pins this one.
        """
        clone = Path(self._tmp.name) / "clone"
        subprocess.run(
            ["git", "clone", "-q", str(Path(self._tmp.name) / "origin.git"),
             str(clone)],
            check=True, capture_output=True,
        )
        self._git(clone, "checkout", "-qb", "ci/fix", "origin/main")
        self.assertIsNone(guard.detect_role(str(clone)))
        self.assertIsNone(guard.detect_branch_cut_role(str(clone), "ci/fix"))

    def test_branch_cut_role_may_push_only_its_own_branch(self):
        role = guard.detect_branch_cut_role(str(self.wt_main), "ci/fix")
        head = subprocess.run(
            ["git", "-C", str(self.wt_main), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        own = [("refs/heads/ci/fix", head, "refs/heads/ci/fix", guard.ZERO_SHA)]
        self.assertEqual(guard.validate_push_updates(role, own), [])
        for target in ("refs/heads/main", "refs/heads/development"):
            with self.subTest(target=target):
                self.assertTrue(
                    guard.validate_push_updates(
                        role,
                        [("refs/heads/ci/fix", head, target, guard.ZERO_SHA)],
                    )
                )

    def test_deletions_and_tags_still_refused_for_branch_cuts(self):
        role = guard.detect_branch_cut_role(str(self.wt_main), "ci/fix")
        head = "a" * 40
        self.assertTrue(
            guard.validate_push_updates(
                role, [("(delete)", guard.ZERO_SHA, "refs/heads/ci/fix", head)]
            )
        )
        self.assertTrue(
            guard.validate_push_updates(
                role, [("refs/tags/v1", head, "refs/tags/v1", guard.ZERO_SHA)]
            )
        )


if __name__ == "__main__":
    unittest.main()
