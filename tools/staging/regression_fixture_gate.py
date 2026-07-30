#!/usr/bin/env python3
"""regression_fixture_gate.py -- every registered regression must have its script.

`REGRESSION LIST` advertises a curated set of runnable proofs. Each entry in
cmd_regression.cpp names a .dts under dottalkpp/data/scripts/. Nothing verified
that the named file exists, or that it is tracked by git.

Found by this gate on the day it was written (AIF-074, 2026-07-29): REGRESSION
RELJOIN is registered and points at main\\rel_join_enum_regression.dts, a 12-test
suite that is UNTRACKED. A fresh clone can list that regression and cannot run
it. The catalog entry is a promise the repository cannot keep.

That is the same defect family this lane spent the day closing -- a name pointing
at something that is not there -- one layer below the contracts. The shortcut
gate checks command names resolve; this checks fixture paths resolve.

Two independent checks:
  MISSING  (hard fail) -- the script is not on disk at all.
  UNTRACKED (hard fail by default) -- the script exists locally but git does not
            know it, so it does not survive a clone. Use --allow-untracked to
            downgrade this to a warning while a promotion decision is pending.

Usage:
  python tools/staging/regression_fixture_gate.py [repo_root] [--allow-untracked]

Exit codes:
  0  every registered regression resolves to a tracked script
  1  at least one is missing or untracked
  2  inputs could not be parsed (hard failure -- a gate that cannot see its
     subject must not report success)
"""

import os
import re
import subprocess
import sys


SCRIPTS_REL = os.path.join("dottalkpp", "data", "scripts")


def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def collect_registrations(root: str):
    """Return [(NAME, script_path_as_written)] from the curated catalog."""
    path = os.path.join(root, "src", "cli", "cmd_regression.cpp")
    if not os.path.isfile(path):
        return None, "cmd_regression.cpp not found at " + path
    text = read(path)
    start = text.find("kRegressionSpecs")
    if start < 0:
        return None, "could not locate kRegressionSpecs in cmd_regression.cpp"
    body = text[start:]

    # Entries look like: { "NAME", "path\\to\\script.dts", "summary", bool },
    pairs = re.findall(r'\{\s*"([A-Z0-9_]+)"\s*,\s*"([^"]+\.[Dd][Tt][Ss])"', body)
    if not pairs:
        return None, "catalog located but no (name, script) pairs parsed"
    return pairs, None


def tracked_files(root: str):
    """Set of git-tracked paths under the scripts dir, normalized to forward slashes."""
    try:
        out = subprocess.run(
            ["git", "ls-files", SCRIPTS_REL.replace("\\", "/")],
            cwd=root, capture_output=True, text=True, timeout=60,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return {line.strip().replace("\\", "/") for line in out.stdout.splitlines() if line.strip()}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    allow_untracked = "--allow-untracked" in sys.argv
    root = os.path.abspath(args[0] if args else os.getcwd())

    regs, err = collect_registrations(root)
    if err:
        print("REGRESSION FIXTURE GATE: CANNOT VERIFY -- " + err)
        return 2

    tracked = tracked_files(root)
    if tracked is None:
        print("REGRESSION FIXTURE GATE: CANNOT VERIFY -- git ls-files failed")
        return 2

    missing, untracked = [], []
    for name, script in regs:
        rel = re.sub(r"/+", "/", script.replace("\\", "/"))
        full = os.path.join(root, SCRIPTS_REL, *rel.split("/"))
        if not os.path.isfile(full):
            missing.append((name, script))
            continue
        git_rel = (SCRIPTS_REL.replace("\\", "/") + "/" + rel)
        if git_rel not in tracked:
            untracked.append((name, script))

    print("REGRESSION FIXTURE GATE")
    print("  registered regressions : {0}".format(len(regs)))
    print("  scripts missing        : {0}".format(len(missing)))
    print("  scripts untracked      : {0}{1}".format(
        len(untracked), "  (warning only: --allow-untracked)" if allow_untracked else ""))

    if missing:
        print("")
        print("FAIL: registered but the script is NOT ON DISK:")
        for name, script in missing:
            print("  REGRESSION {0:<22} -> {1}".format(name, script))

    if untracked:
        print("")
        label = "WARN" if allow_untracked else "FAIL"
        print("{0}: registered and present locally, but NOT TRACKED by git.".format(label))
        print("      A fresh clone can list these and cannot run them.")
        for name, script in untracked:
            print("  REGRESSION {0:<22} -> {1}".format(name, script))
        print("")
        print("      Promote the file deliberately, or remove the catalog entry.")

    if missing or (untracked and not allow_untracked):
        return 1

    print("")
    print("PASS: every registered regression resolves to a tracked script.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
