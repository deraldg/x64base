#!/usr/bin/env python3
"""
prepush_gate.py — mechanical enforcement of the AI_PORTAL Pre-Push Gate.

Single source of truth for the exclusion list is AI_PORTAL.md (the
"Outside-AI Delivery Rule", line ~300):

    "Do not include binaries, build directories, generated runtime data,
     unrelated formatting, cleanup, or branch operations."

This guard inspects a change set (staged index by default, or a commit range)
and classifies each path into three lanes:

  HARD BLOCK  — things that must never be committed to source:
                build trees, CMake byproducts, compiled binaries, IDE project
                files. Presence => exit 2 (the gate fails).

  WARN/ACK    — versioned data & runtime fixtures (DBF/DBT/FPT/CNX/CDX/INX,
                LMDB, generated help/metadata catalogs) and suspiciously large
                change sets. These CAN be legitimate (a deliberate fixture
                promotion the task named), so they do not hard-fail; they
                require an explicit acknowledgement flag. Without it => exit 3.

  OK          — source, headers, docs, scripts, configs, manifests.

Exit codes:  0 clean · 2 hard-blocked · 3 warn-needs-ack · 4 usage/git error.

Usage:
  python tools/staging/prepush_gate.py                 # check staged index
  python tools/staging/prepush_gate.py --range HEAD..@{u}   # check a push range
  python tools/staging/prepush_gate.py --allow-data    # ack intentional fixtures
  python tools/staging/prepush_gate.py --allow-mass     # ack a large change set
  python tools/staging/prepush_gate.py --install-hook   # install as .git/hooks/pre-commit

The gate is advisory-by-design for the WARN lane: it never silently drops a
file, it reports and asks a human (or an agent) to name the mutation.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys

# --- Threshold for the "mass change" heuristic ---------------------------------
MASS_CHANGE_THRESHOLD = 60

# --- HARD BLOCK patterns (never belong in a source commit) ---------------------
# Directory-segment matches (any path containing the segment) and glob suffixes.
HARD_BLOCK_DIR_SEGMENTS = (
    "/CMakeFiles/",
    "/build-msvc/",
    "/_tvision_local/",
)
HARD_BLOCK_PATH_PREFIXES = (
    "build/",
    "out/",
    "dist/",
    "bin/",
    "obj/",
)
HARD_BLOCK_PATH_PREFIX_GLOBS = (
    "build-*/",
    "build_*/",
    "cmake-build-*/",
)
HARD_BLOCK_SUFFIXES = (
    ".exe", ".dll", ".lib", ".pdb", ".obj", ".ilk", ".exp", ".pch",
    ".sln", ".vcxproj", ".vcxproj.filters", ".vcxproj.user",
    ".recipe", ".tlog", ".lastbuildstate",
)
HARD_BLOCK_BASENAMES = (
    "CMakeCache.txt",
    "cmake_install.cmake",
    "CTestTestfile.cmake",
    "build.ninja",
)

# --- WARN lane: versioned data & generated runtime data ------------------------
DATA_SUFFIXES = (".dbf", ".dbt", ".fpt", ".cnx", ".cdx", ".inx", ".mdx")
DATA_DIR_SEGMENTS = (
    "/data/dbf/",
    "/data/indexes/",
    "/data/lmdb/",
    "/data/help/",
    "/data/metadata/",
    "/data/manuals/",
)


def run_git(args: list[str]) -> str:
    try:
        out = subprocess.run(
            ["git"] + args,
            check=True, capture_output=True, text=True,
        )
        return out.stdout
    except FileNotFoundError:
        print("prepush-gate: git not found on PATH", file=sys.stderr)
        sys.exit(4)
    except subprocess.CalledProcessError as e:
        print(f"prepush-gate: git {' '.join(args)} failed:\n{e.stderr}", file=sys.stderr)
        sys.exit(4)


def changed_paths(range_spec: str | None) -> list[str]:
    if range_spec:
        raw = run_git(["diff", "--name-only", "--diff-filter=ACMR", range_spec])
    else:
        raw = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [p.strip().strip('"') for p in raw.splitlines() if p.strip()]


def norm(path: str) -> str:
    return "/" + path.replace("\\", "/").lstrip("/")


def is_hard_block(path: str) -> bool:
    p = norm(path)
    base = p.rsplit("/", 1)[-1]
    rel = p.lstrip("/")
    if any(seg in p for seg in HARD_BLOCK_DIR_SEGMENTS):
        return True
    if any(rel.startswith(pre) for pre in HARD_BLOCK_PATH_PREFIXES):
        return True
    if any(fnmatch.fnmatch(rel, g + "*") for g in HARD_BLOCK_PATH_PREFIX_GLOBS):
        return True
    if base in HARD_BLOCK_BASENAMES:
        return True
    low = base.lower()
    if any(low.endswith(sfx) for sfx in HARD_BLOCK_SUFFIXES):
        return True
    return False


def is_data_fixture(path: str) -> bool:
    p = norm(path).lower()
    if any(p.endswith(sfx) for sfx in DATA_SUFFIXES):
        return True
    if any(seg in p for seg in DATA_DIR_SEGMENTS):
        return True
    return False


def install_hook() -> int:
    hook_dir = run_git(["rev-parse", "--git-path", "hooks"]).strip()
    os.makedirs(hook_dir, exist_ok=True)
    hook_path = os.path.join(hook_dir, "pre-commit")
    script = (
        "#!/bin/sh\n"
        "# Installed by tools/staging/prepush_gate.py --install-hook\n"
        "# Enforces the AI_PORTAL Pre-Push Gate on the staged index.\n"
        'python "$(git rev-parse --show-toplevel)/tools/staging/prepush_gate.py" || exit 1\n'
    )
    with open(hook_path, "w", newline="\n") as f:
        f.write(script)
    try:
        os.chmod(hook_path, 0o755)
    except OSError:
        pass
    print(f"prepush-gate: installed pre-commit hook at {hook_path}")
    print("  (bypass a single intentional commit with: git commit --no-verify)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="AI_PORTAL Pre-Push Gate enforcement.")
    ap.add_argument("--range", dest="range_spec", default=None,
                    help="commit range to check (e.g. HEAD..@{u}); default = staged index")
    ap.add_argument("--allow-data", action="store_true",
                    help="acknowledge intentional data/fixture changes (the task named the mutation)")
    ap.add_argument("--allow-mass", action="store_true",
                    help="acknowledge a large change set")
    ap.add_argument("--install-hook", action="store_true",
                    help="install this gate as a git pre-commit hook and exit")
    args = ap.parse_args()

    if args.install_hook:
        return install_hook()

    paths = changed_paths(args.range_spec)
    scope = args.range_spec or "staged index"
    if not paths:
        print(f"prepush-gate: no changes in {scope} — clean.")
        return 0

    hard = [p for p in paths if is_hard_block(p)]
    data = [p for p in paths if p not in hard and is_data_fixture(p)]
    ok = [p for p in paths if p not in hard and p not in data]

    print(f"prepush-gate: inspecting {len(paths)} path(s) in {scope}")
    print(f"  source/docs/config : {len(ok)}")
    print(f"  data/fixtures      : {len(data)}")
    print(f"  hard-block         : {len(hard)}")

    exit_code = 0

    if hard:
        print("\n  BLOCKED — these never belong in a source commit "
              "(build trees / binaries / IDE project files):", file=sys.stderr)
        for p in sorted(hard)[:40]:
            print(f"    ✗ {p}", file=sys.stderr)
        if len(hard) > 40:
            print(f"    … and {len(hard) - 40} more", file=sys.stderr)
        print("  Unstage them (git restore --staged <path>) or add to .gitignore.",
              file=sys.stderr)
        exit_code = 2

    if data and not args.allow_data:
        print("\n  WARN — data/runtime fixtures staged. These are report-only unless "
              "the task named the mutation.", file=sys.stderr)
        for p in sorted(data)[:40]:
            print(f"    ? {p}", file=sys.stderr)
        if len(data) > 40:
            print(f"    … and {len(data) - 40} more", file=sys.stderr)
        print("  If intentional, re-run with --allow-data (or restore them).",
              file=sys.stderr)
        if exit_code == 0:
            exit_code = 3

    if len(paths) > MASS_CHANGE_THRESHOLD and not args.allow_mass:
        print(f"\n  WARN — {len(paths)} paths staged (> {MASS_CHANGE_THRESHOLD}). "
              "Large sets often mean an accidental mass add or an un-sliced batch.",
              file=sys.stderr)
        print("  Confirm the scope, then re-run with --allow-mass if intentional.",
              file=sys.stderr)
        if exit_code == 0:
            exit_code = 3

    if exit_code == 0:
        print("\nprepush-gate: PASS — change set is source/docs/config only "
              "(or acknowledged).")
    else:
        print(f"\nprepush-gate: FAIL (exit {exit_code}).", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
