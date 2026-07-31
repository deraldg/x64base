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


if __name__ == "__main__":
    unittest.main()
