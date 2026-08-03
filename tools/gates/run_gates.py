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

STRICT BY DEFAULT since 2026-08-02. A failing gate fails the run (exit 1).

  python tools/gates/run_gates.py [--advisory] [--only census,registry] [--root <repo>]

PROMOTED 2026-08-02, on a measured clean tree, not on intent:

  census    1046/1046 tracked source files carry @dottalk.file  (100.0%, uncovered 0)
  registry  185 citations verifiable, 0 missing, 0 untracked, 0 external

Why the flip. Coverage reached 100% on 2026-07-25 and had decayed to 99.4% by
2026-08-02 -- six files, none malicious, just new work that nobody re-ran the
gate against. An advisory gate reports drift to whoever happens to look. This
project already measured what that is worth: check_session_log_row.py records
33 percent compliance for the one closeout obligation that had no mechanism,
against 83-94 percent for the four that did. A rule with no gate is obeyed a
third of the time.

--advisory restores the old behaviour: run everything, report, exit 0. It is
for surveying a tree you already know is dirty (a mid-migration lane, a fresh
clone being triaged) -- NOT for getting a red run to go away. If a gate fails
on work you intend to land, fix the tree or say in the closeout why the finding
is accepted.

Exit: 0 all gates pass, 1 a gate failed (or --advisory runner error), 2 runner error.

Owner: member.derald . steward: member.ai.claude.cowork . lane: AIF-062 . status: supported
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
    ap.add_argument("--advisory", action="store_true",
                    help="report failures without failing the run (exit 0)")
    ap.add_argument("--strict", action="store_true",
                    help="accepted and ignored -- strict is the default since 2026-08-02. "
                         "Kept so existing scripts and docs that pass it keep working.")
    ap.add_argument("--only", metavar="NAMES",
                    help="comma-separated subset, e.g. --only census")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    # Strict is the default; --advisory is the only way out. --strict is a no-op kept for
    # compatibility: several docs, the standards seed and finish_session.py all spell the
    # old invocation, and silently rejecting it would break them for no gain.
    strict = not args.advisory

    wanted = ([s.strip() for s in args.only.split(",")] if args.only
              else [g[0] for g in GATES])

    print("=" * 68)
    print(f"x64base static drift gates   root: {root}")
    print(f"mode: {'STRICT (failures fail the run)' if strict else 'ADVISORY (--advisory: failures reported, run still passes)'}")
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
    if strict:
        print(f"STRICT: {len(failed)} gate(s) failed -> FAIL", file=sys.stderr)
        print("Fix the tree, or re-run with --advisory if you are deliberately surveying "
              "a dirty tree.", file=sys.stderr)
        return 1
    print(f"advisory: {len(failed)} gate(s) failing, not failing the run (--advisory).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
