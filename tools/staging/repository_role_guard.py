#!/usr/bin/env python3
"""
Enforce the x64base development/staging repository-role contract.

Known roles:
  D:\code\ccode  -> development authoring worktree; may push development only.
  C:\x64base     -> sterilized staging worktree; may push main only.

The pre-push mode reads Git's update records from stdin:
  <local-ref> <local-sha> <remote-ref> <remote-sha>

Exit codes:
  0 role and ref updates are valid
  2 repository role, branch, or push target is forbidden
  4 environment, Git, or usage error
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEVELOPMENT_ROOT = r"D:\code\ccode"
STAGING_ROOT = r"C:\x64base"
ZERO_SHA = "0" * 40


@dataclass(frozen=True)
class RepositoryRole:
    name: str
    root: str
    required_branch: str
    allowed_remote_branch: str


DEVELOPMENT_ROLE = RepositoryRole(
    name="development",
    root=DEVELOPMENT_ROOT,
    required_branch="development",
    allowed_remote_branch="development",
)
STAGING_ROLE = RepositoryRole(
    name="staging",
    root=STAGING_ROOT,
    required_branch="main",
    allowed_remote_branch="main",
)


def normalized_path(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def windows_form(path: str) -> str:
    """Translate a WSL drive mount to its Windows spelling.

    "/mnt/d/code/ccode" -> "D:\\code\\ccode". Anything that is not a
    /mnt/<single-drive-letter> path is returned unchanged.

    This RECOGNISES an existing root under a second spelling; it does NOT add
    a new one. The permitted set is still exactly DEVELOPMENT_ROOT and
    STAGING_ROOT -- "/mnt/d/code/other" translates to "D:\\code\\other" and is
    still refused, and a native Linux path like "/home/x/ccode" does not
    translate at all.
    """
    match = re.fullmatch(r"/mnt/([A-Za-z])(/.*)?", path)
    if not match:
        return path
    drive = match.group(1).upper()
    remainder = (match.group(2) or "").replace("/", "\\")
    return f"{drive}:{remainder}"


def windows_key(path: str) -> str:
    """Comparison key for a WINDOWS-form path, usable from any OS.

    Deliberately does NOT call os.path.abspath. That is what made the guard
    unusable outside Windows: on POSIX, abspath("D:\\code\\ccode") resolves the
    literal against the current directory and yields nonsense, so even
    DEVELOPMENT_ROOT failed to compare equal to itself. Pure string
    normalisation is correct here because both operands are already absolute
    Windows paths by construction.
    """
    return path.replace("/", "\\").rstrip("\\").casefold()


def detect_role(root: str) -> RepositoryRole | None:
    """Identify the repository role of `root`, on Windows or under WSL.

    Two comparisons, in order:
      1. Native normalisation -- the original Windows behaviour, unchanged.
      2. Windows-form comparison after translating a WSL /mnt/<drive> path,
         so /mnt/d/code/ccode is recognised as D:\\code\\ccode.

    Before this, a commit from WSL hard-failed with "repository root is not a
    declared x64base development or staging root" -- not because the worktree
    was wrong, but because it was spelled in POSIX. AI_README/CLAUDE.md
    attributed that block to the sandbox; it is a path-FORM issue and WSL hit
    it too.
    """
    resolved = normalized_path(root)
    root_windows = windows_key(windows_form(root))

    for role in (DEVELOPMENT_ROLE, STAGING_ROLE):
        if resolved == normalized_path(role.root):
            return role
        if root_windows == windows_key(role.root):
            return role
    return None


def git_output(root: str, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", root, *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "unknown Git error"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}") from exc
    return result.stdout.strip()


def resolve_root(explicit_root: str | None) -> str:
    if explicit_root:
        return str(Path(explicit_root))
    return git_output(os.getcwd(), "rev-parse", "--show-toplevel")


def resolve_branch(root: str, explicit_branch: str | None) -> str:
    if explicit_branch is not None:
        return explicit_branch
    return git_output(root, "branch", "--show-current")


def validate_worktree(
    role: RepositoryRole | None,
    branch: str,
    *,
    allow_staging_branch: bool = False,
) -> list[str]:
    if role is None:
        return [
            "repository root is not a declared x64base development or staging root"
        ]
    if role is STAGING_ROLE and allow_staging_branch:
        if branch == "main" or branch.startswith("promotion/"):
            return []
    if branch != role.required_branch:
        return [
            f"{role.name} worktree requires branch {role.required_branch!r}; "
            f"observed {branch!r}"
        ]
    return []


def parse_push_updates(lines: Iterable[str]) -> list[tuple[str, str, str, str]]:
    updates: list[tuple[str, str, str, str]] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"invalid pre-push update record: {line!r}")
        updates.append((parts[0], parts[1], parts[2], parts[3]))
    return updates


def development_is_ancestor(root: str, local_sha: str) -> bool:
    refs = ("refs/remotes/origin/development", "refs/heads/development")
    for ref in refs:
        exists = subprocess.run(
            ["git", "-C", root, "show-ref", "--verify", "--quiet", ref]
        )
        if exists.returncode != 0:
            continue
        result = subprocess.run(
            ["git", "-C", root, "merge-base", "--is-ancestor", ref, local_sha]
        )
        return result.returncode == 0
    return False


def validate_push_updates(
    role: RepositoryRole,
    updates: list[tuple[str, str, str, str]],
    *,
    root: str | None = None,
    development_ancestor_override: bool | None = None,
) -> list[str]:
    errors: list[str] = []
    expected_ref = f"refs/heads/{role.allowed_remote_branch}"
    for local_ref, local_sha, remote_ref, _remote_sha in updates:
        if local_sha == ZERO_SHA or local_ref == "(delete)":
            errors.append(f"branch or tag deletion is not permitted: {remote_ref}")
            continue
        if not remote_ref.startswith("refs/heads/"):
            errors.append(f"only the declared branch may be pushed: {remote_ref}")
            continue
        if remote_ref != expected_ref:
            errors.append(
                f"{role.name} worktree may push only {expected_ref}; "
                f"attempted {local_ref} -> {remote_ref}"
            )
            continue
        if role is STAGING_ROLE and remote_ref == "refs/heads/main":
            is_ancestor = development_ancestor_override
            if is_ancestor is None and root:
                is_ancestor = development_is_ancestor(root, local_sha)
            if is_ancestor:
                errors.append(
                    "development is an ancestor of the proposed main tip; "
                    "merging development into main is forbidden"
                )
    return errors


def _write_managed_hook(
    path: str,
    body: str,
    *,
    accepted_legacy_markers: tuple[str, ...] = (),
) -> None:
    marker = "# Managed by tools/staging/repository_role_guard.py"
    if os.path.exists(path):
        existing = Path(path).read_text(encoding="utf-8", errors="replace")
        accepted = marker in existing or any(
            legacy in existing for legacy in accepted_legacy_markers
        )
        if not accepted:
            raise RuntimeError(
                f"refusing to overwrite unmanaged hook: {path}"
            )
    Path(path).write_text(body, encoding="utf-8", newline="\n")
    try:
        os.chmod(path, 0o755)
    except OSError:
        pass


def install_hooks(root: str) -> None:
    hook_dir = git_output(root, "rev-parse", "--git-path", "hooks")
    if not os.path.isabs(hook_dir):
        hook_dir = os.path.join(root, hook_dir)
    os.makedirs(hook_dir, exist_ok=True)
    pre_commit_path = os.path.join(hook_dir, "pre-commit")
    pre_push_path = os.path.join(hook_dir, "pre-push")
    preserved_pre_push = pre_push_path + ".x64base-preserved"
    marker = "# Managed by tools/staging/repository_role_guard.py\n"
    # Interpreter resolution, not a bare "python".
    #
    # The hook body is /bin/sh and runs from whatever shell invoked git. A bare
    # "python" resolves on Windows but NOT on Debian-family WSL, which ships
    # only "python3" -- so every WSL commit died at
    # ".git/hooks/pre-commit: 4: python: not found" before the guard could even
    # run. Hardcoding "python3" instead would break Windows, where python3 is
    # an unreliable Store alias. Prefer python3, fall back to python, and fail
    # with a legible message rather than a shell "not found".
    common = (
        'ROOT="$(git rev-parse --show-toplevel)"\n'
        'PY="$(command -v python3 || command -v python)"\n'
        'if [ -z "$PY" ]; then\n'
        '  echo "x64base hooks: no python3 or python on PATH" >&2\n'
        '  exit 1\n'
        'fi\n'
    )
    pre_commit = (
        "#!/bin/sh\n"
        + marker
        + common
        + '"$PY" "$ROOT/tools/staging/repository_role_guard.py" || exit 1\n'
        + '"$PY" "$ROOT/tools/staging/prepush_gate.py" || exit 1\n'
    )
    pre_push = (
        "#!/bin/sh\n"
        + marker
        + common
        + 'HOOK_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"\n'
        + 'UPDATES="${TMPDIR:-/tmp}/x64base-pre-push-$$"\n'
        + 'trap \'rm -f "$UPDATES"\' EXIT HUP INT TERM\n'
        + 'cat > "$UPDATES" || exit 1\n'
        + '"$PY" "$ROOT/tools/staging/repository_role_guard.py" '
        + '--pre-push < "$UPDATES" || exit 1\n'
        + 'if [ -x "$HOOK_DIR/pre-push.x64base-preserved" ]; then\n'
        + '  "$HOOK_DIR/pre-push.x64base-preserved" "$@" '
        + '< "$UPDATES" || exit $?\n'
        + "fi\n"
    )

    if os.path.exists(pre_commit_path):
        existing_pre_commit = Path(pre_commit_path).read_text(
            encoding="utf-8", errors="replace"
        )
        accepted_pre_commit = (
            marker.strip() in existing_pre_commit
            or "# Installed by tools/staging/prepush_gate.py --install-hook"
            in existing_pre_commit
        )
        if not accepted_pre_commit:
            raise RuntimeError(
                f"refusing to overwrite unmanaged hook: {pre_commit_path}"
            )

    if os.path.exists(pre_push_path):
        existing = Path(pre_push_path).read_text(
            encoding="utf-8", errors="replace"
        )
        if marker not in existing:
            if os.path.exists(preserved_pre_push):
                raise RuntimeError(
                    "refusing to replace pre-push: preserved hook already exists: "
                    f"{preserved_pre_push}"
                )
            os.replace(pre_push_path, preserved_pre_push)
            try:
                os.chmod(preserved_pre_push, 0o755)
            except OSError:
                pass

    _write_managed_hook(
        pre_commit_path,
        pre_commit,
        accepted_legacy_markers=(
            "# Installed by tools/staging/prepush_gate.py --install-hook",
        ),
    )
    _write_managed_hook(pre_push_path, pre_push)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enforce x64base repository path, branch, and push roles."
    )
    parser.add_argument("--root", help="override repository root for validation")
    parser.add_argument("--branch", help="override current branch for validation")
    parser.add_argument(
        "--pre-push",
        action="store_true",
        help="read and validate Git pre-push update records from stdin",
    )
    parser.add_argument(
        "--install-hooks",
        action="store_true",
        help="install managed pre-commit and pre-push hooks",
    )
    parser.add_argument(
        "--allow-staging-branch",
        action="store_true",
        help="allow an explicitly authorized promotion/* branch in staging",
    )
    args = parser.parse_args(argv)

    try:
        root = resolve_root(args.root)
        branch = resolve_branch(root, args.branch)
    except RuntimeError as exc:
        print(f"repository-role-guard: {exc}", file=sys.stderr)
        return 4

    role = detect_role(root)
    allow_staging_branch = (
        args.allow_staging_branch
        or os.environ.get("X64BASE_ALLOW_STAGING_BRANCH") == "1"
    )
    errors = validate_worktree(
        role,
        branch,
        allow_staging_branch=allow_staging_branch,
    )
    if errors:
        for error in errors:
            print(f"repository-role-guard: BLOCKED: {error}", file=sys.stderr)
        return 2
    assert role is not None

    if args.install_hooks:
        try:
            install_hooks(root)
        except RuntimeError as exc:
            print(f"repository-role-guard: {exc}", file=sys.stderr)
            return 4
        print(f"repository-role-guard: installed managed hooks in {root}")
        return 0

    if args.pre_push:
        try:
            updates = parse_push_updates(sys.stdin)
        except ValueError as exc:
            print(f"repository-role-guard: {exc}", file=sys.stderr)
            return 4
        errors = validate_push_updates(role, updates, root=root)
        if errors:
            for error in errors:
                print(f"repository-role-guard: BLOCKED: {error}", file=sys.stderr)
            return 2

    print(
        "repository-role-guard: PASS: "
        f"{root} is the {role.name} worktree on {branch}; "
        f"allowed remote branch is {role.allowed_remote_branch}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
