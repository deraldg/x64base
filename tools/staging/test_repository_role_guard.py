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

    def test_website_root_is_deliberately_not_a_role(self):
        r"""The site tree must stay unrecognised, in BOTH path spellings.

        D:\dev\x64base-site shares this repository -- github.com/deraldg/x64base
        carries four unrelated histories as orphan branches -- so it is a real
        tree an agent may be standing in, not a typo. The guard still refuses it,
        and that refusal is a decision rather than an oversight.

        THIS TEST EXISTS TO MAKE ADDING A WEBSITE ROLE A DELIBERATE ACT. Granting
        a role grants a push target; that is a change to the permitted set and
        belongs to the owner. If a future change makes this fail, do not delete
        the test -- get the contract amended first.
        See docs/contracts/REPOSITORY_ROLE_AND_PROMOTION_CONTRACT_V1.md.
        """
        for spelling in (r"D:\dev\x64base-site", "/mnt/d/dev/x64base-site"):
            self.assertIsNone(
                guard.detect_role(spelling),
                f"{spelling} gained a role; the permitted push set changed",
            )

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
        # root is REQUIRED for a branch-cut role: without it the per-commit
        # ancestry cannot be established and the guard fails closed.
        self.assertEqual(guard.validate_push_updates(role, own, root=str(self.wt_main)), [])
        self.assertTrue(guard.validate_push_updates(role, own))  # no root -> refused
        for target in ("refs/heads/main", "refs/heads/development"):
            with self.subTest(target=target):
                self.assertTrue(
                    guard.validate_push_updates(
                        role,
                        [("refs/heads/ci/fix", head, target, guard.ZERO_SHA)],
                        root=str(self.wt_main),
                    )
                )

    def test_explicit_refspec_cannot_smuggle_development(self):
        """Codex review, PR #13, 2026-08-16 -- reproduced before fixing.

        The role is earned by HEAD's ancestry, but `git push` accepts a
        refspec: `git push origin development:ci/fix` sends development's tip
        at the accepted destination. The destination matched and nothing looked
        at local_sha, so the exact history this role exists to exclude would
        have published, and a PR from that branch would have carried it to main.
        """
        role = guard.detect_branch_cut_role(str(self.wt_main), "ci/fix")
        dev = subprocess.run(
            ["git", "-C", str(self.wt_main), "rev-parse", "development"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        errors = guard.validate_push_updates(
            role,
            [("refs/heads/development", dev, "refs/heads/ci/fix", guard.ZERO_SHA)],
            root=str(self.wt_main),
        )
        self.assertTrue(errors, "a development SHA reached an accepted branch ref")
        self.assertIn("development history", " ".join(errors))

    def test_missing_development_ref_fails_closed(self):
        """Codex review, PR #13 -- unverifiable history must not read as safe.

        ref_is_ancestor returns False for "not an ancestor" AND for "ref absent",
        so deleting only refs/remotes/origin/development made a worktree sitting
        on development look like a clean cut from main. Same defect shape as
        proof.tooling.catalog_state_blindness, reintroduced hours after it was
        written up.
        """
        subprocess.run(
            ["git", "-C", str(self.dev), "update-ref", "-d",
             "refs/remotes/origin/development"],
            check=True, capture_output=True,
        )
        # The local development branch still exists, so it must still be found.
        self.assertIsNone(guard.detect_branch_cut_role(str(self.wt_dev), "ci/bad"))
        # carries_development reports None only when NOTHING can be compared.
        head = subprocess.run(
            ["git", "-C", str(self.wt_main), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        self.assertIs(guard.carries_development(str(self.wt_main), head), False)

    def test_no_development_ref_at_all_is_undeterminable_and_refused(self):
        """The None path -- and it needed a second attempt to actually reach.

        The test above deletes only the remote-tracking ref, so the LOCAL
        development branch still answers and `present` is never empty. Mutation
        testing proved it: changing `return None` to `return False` in
        carries_development broke NO test. The check was green for a reason
        unrelated to what it claimed.

        This one removes every development ref, which is the only state in
        which the answer is genuinely unknowable, and requires that a cut which
        is otherwise perfectly clean is still REFUSED. Safety here is not
        "development is absent so nothing can be smuggled" -- it is "the claim
        cannot be established, so it is not granted."
        """
        for ref in ("refs/remotes/origin/development", "refs/heads/development"):
            subprocess.run(
                ["git", "-C", str(self.dev), "update-ref", "-d", ref],
                capture_output=True,
            )
        head = subprocess.run(
            ["git", "-C", str(self.wt_main), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        self.assertIsNone(guard.carries_development(str(self.wt_main), head))
        # A textbook-clean cut from origin/main, refused because unverifiable.
        self.assertIsNone(guard.detect_branch_cut_role(str(self.wt_main), "ci/fix"))

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


class AnnotatedTagPushTests(unittest.TestCase):
    """The tag arm, against a REAL repository for the same reason the branch-cut
    tests use one: every condition is a fact about Git state -- object type, and
    whether a commit is reachable from a remote ref. A stubbed test would pass
    while the guard misread a real tree.

    Added 2026-08-30 with the arm itself. The arm exists because the contract
    asserted tags were pushable while this file refused them; a widening with no
    test would swap one undetected disagreement for another.
    """

    def _git(self, cwd, *args, check=True):
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=str(cwd), check=check, capture_output=True, text=True,
        )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        origin = base / "origin.git"
        self.dev = base / "dev"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True,
                       capture_output=True)
        subprocess.run(["git", "init", "-q", str(self.dev)], check=True,
                       capture_output=True)
        self._git(self.dev, "remote", "add", "origin", str(origin))
        (self.dev / "f.txt").write_text("a\n", encoding="utf-8")
        self._git(self.dev, "add", ".")
        self._git(self.dev, "commit", "-qm", "base")
        self._git(self.dev, "branch", "-M", "development")
        self._git(self.dev, "push", "-q", "origin", "development")
        self._git(self.dev, "fetch", "-q", "origin")
        self.published = self._git(self.dev, "rev-parse", "HEAD").stdout.strip()

        # A commit that exists locally and has NOT been pushed.
        (self.dev / "g.txt").write_text("g\n", encoding="utf-8")
        self._git(self.dev, "add", ".")
        self._git(self.dev, "commit", "-qm", "not yet pushed")
        self.unpublished = self._git(self.dev, "rev-parse", "HEAD").stdout.strip()

        self.role = guard.RepositoryRole(
            name="development",
            root=str(self.dev),
            required_branch="development",
            allowed_remote_branch="development",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def _tag(self, name, target, annotated=True):
        if annotated:
            self._git(self.dev, "tag", "-a", name, "-m", "snapshot", target)
        else:
            self._git(self.dev, "tag", name, target)
        return self._git(self.dev, "rev-parse", f"refs/tags/{name}").stdout.strip()

    def _push(self, name, sha, remote_sha=guard.ZERO_SHA):
        return guard.validate_push_updates(
            self.role,
            [(f"refs/tags/{name}", sha, f"refs/tags/{name}", remote_sha)],
            root=str(self.dev),
        )

    def test_annotated_tag_on_a_published_commit_is_allowed(self):
        sha = self._tag("v9.9.9", self.published)
        self.assertEqual(self._push("v9.9.9", sha), [])

    def test_lightweight_tag_is_refused(self):
        sha = self._tag("lw", self.published, annotated=False)
        errors = self._push("lw", sha)
        self.assertTrue(any("ANNOTATED" in e for e in errors), errors)

    def test_tag_naming_an_unpublished_commit_is_refused(self):
        """THE LOAD-BEARING ONE. A tag must not be the thing that publishes a
        commit -- the check is against origin/development, not the local branch,
        so tagging unpushed work cannot smuggle it out under a name."""
        sha = self._tag("v9.9.8", self.unpublished)
        errors = self._push("v9.9.8", sha)
        self.assertTrue(any("already published" in e for e in errors), errors)

    def test_tag_that_exists_on_the_remote_may_not_be_moved(self):
        sha = self._tag("v9.9.7", self.published)
        errors = self._push("v9.9.7", sha, remote_sha="b" * 40)
        self.assertTrue(any("may not be moved" in e for e in errors), errors)

    def test_tag_deletion_is_still_refused(self):
        errors = guard.validate_push_updates(
            self.role,
            [("(delete)", guard.ZERO_SHA, "refs/tags/v9.9.9", "a" * 40)],
            root=str(self.dev),
        )
        self.assertTrue(any("deletion is not permitted" in e for e in errors), errors)

    def test_a_branch_cut_role_may_not_push_tags(self):
        sha = self._tag("v9.9.6", self.published)
        cut = guard.RepositoryRole(
            name="branch-cut",
            root=str(self.dev),
            required_branch="ci/fix",
            allowed_remote_branch="ci/fix",
            branch_cut=True,
        )
        errors = guard.validate_push_updates(
            cut,
            [("refs/tags/v9.9.6", sha, "refs/tags/v9.9.6", guard.ZERO_SHA)],
            root=str(self.dev),
        )
        self.assertTrue(any("branch-cut role may not push tags" in e for e in errors), errors)

    def test_a_branch_ref_is_still_governed_by_the_branch_rules(self):
        """The new arm must not have become a way around the old ones."""
        errors = guard.validate_push_updates(
            self.role,
            [("refs/heads/development", "1" * 40, "refs/heads/other", "2" * 40)],
            root=str(self.dev),
        )
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
