#!/usr/bin/env python3
"""
Static drift gates for x64base -- one runner, all source-tree checks.

These are STATIC checks: they read the tree and the registries. No build, no exe, no
data. Safe to run any time, including while dottalk_bbsd is up. (Test-All.ps1 is the
separate golden-file CLI harness and does need a built exe.)

Gates:
  census    tools/fullstack_docs/source_census.py --strict
            every tracked .cpp/.hpp carries an @dottalk.file block.
            AIF-050; passable since 2026-07-25 at 1034/1034.

  registry  tools/gates/validate_registries.py --strict
            every artifact proofs.yaml / ai_runs.yaml / lessons.yaml CITES exists and
            is tracked by git. AIF-062; a citation nobody can follow is not evidence.

Advisory by default: runs everything, reports, exits 0. --strict makes any failing gate
fail the run (exit 1) -- promote once the tree is clean and you want regressions caught.

  python tools/gates/run_gates.py [--strict] [--only census,registry] [--root <repo>]

Exit: 0 all gates pass (or advisory), 1 a gate failed under --strict, 2 runner error.

Owner: member.derald . steward: member.ai.claude.cowork . lane: AIF-062 . status: candidate
"""
import argparse
import subprocess
import sys
from pathlib import Path

GATES = [
    ("census",
     "@dottalk.file coverage (AIF-050)",
     ["tools/fullstack_docs/source_census.py", "--strict"]),
    ("registry",
     "registry citations resolve and are tracked (AIF-062)",
     ["tools/gates/validate_registries.py", "--strict", "--quiet"]),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--strict", action="store_true",
                    help="a failing gate fails the run (exit 1)")
    ap.add_argument("--only", metavar="NAMES",
                    help="comma-separated subset, e.g. --only census")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    wanted = ([s.strip() for s in args.only.split(",")] if args.only
              else [g[0] for g in GATES])

    print("=" * 68)
    print(f"x64base static drift gates   root: {root}")
    print(f"mode: {'STRICT (failures fail the run)' if args.strict else 'advisory'}")
    print("=" * 68)

    results = []
    for name, desc, cmd in GATES:
        if name not in wanted:
            continue
        script = root / cmd[0]
        print(f"\n--- gate: {name} -- {desc}")
        if not script.is_file():
            print(f"    SKIP: {cmd[0]} not found")
            results.append((name, "SKIP", 0))
            continue
        proc = subprocess.run([sys.executable, str(script), "--root", str(root)] + cmd[1:],
                              capture_output=True, text=True, errors="replace")
        out = (proc.stdout or "") + (proc.stderr or "")
        for line in out.rstrip().splitlines():
            print(f"    {line}")
        state = "PASS" if proc.returncode == 0 else "FAIL"
        print(f"    -> {state} (exit {proc.returncode})")
        results.append((name, state, proc.returncode))

    print("\n" + "=" * 68)
    print("SUMMARY")
    for name, state, rc in results:
        print(f"  {state:5}  {name}")
    failed = [r for r in results if r[1] == "FAIL"]
    print("=" * 68)

    if not failed:
        print("All gates pass.")
        return 0
    if args.strict:
        print(f"STRICT: {len(failed)} gate(s) failed -> FAIL", file=sys.stderr)
        return 1
    print(f"advisory: {len(failed)} gate(s) failing (not a failure yet). "
          f"Re-run with --strict once the tree is clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
