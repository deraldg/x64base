#!/usr/bin/env python3
"""AIF-101 M0: weekly acceleration metrics, regenerated from the repo's own record.

Emits one ASCII table: per ISO week, several independent denominators of activity.
Multiple metrics by design -- commit count alone partially measures the scoped-slice
process change itself (charter confound C2), so no single column is the finding.

Metrics (all derived from `git log` on the current branch; no hand counts):
  commits      : commits whose author-date falls in the week
  src+ / doc+  : lines added to source (src/ include/ tools/ bindings/) vs docs
                 (docs/ labtalk/ *.md at root) -- from --numstat
  newdoc       : files CREATED under docs/maintenance/ (diff-filter=A)
  closeout     : SESSION_CLOSEOUT_* files created
  proofs       : files created under labtalk/registries/{proofs.d,lessons.d}
  aifclaim     : claim files created under coordination/aif/
  regress      : .dts scripts created under dottalkpp/data/scripts/

Bounds / honesty:
  - Author dates, not committer dates (rebases would smear committer dates).
  - The table ends at the current (partial) ISO week and says so.
  - Binary files in numstat ("-") are skipped.
Usage: python3 tools/analysis/acceleration_metrics.py [--since 2026-05-01]
"""

import argparse
import datetime as dt
import subprocess
import sys
from collections import defaultdict

SRC_PREFIXES = ("src/", "include/", "tools/", "bindings/")
DOC_PREFIXES = ("docs/", "labtalk/")


def iso_week(date_str: str) -> str:
    d = dt.date.fromisoformat(date_str)
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def run_git(args):
    out = subprocess.run(
        ["git", "--no-optional-locks"] + args,
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--since", default="2026-05-01", help="start date (author-date)")
    args = ap.parse_args()

    # One pass: per-commit header (date) + numstat lines + name-status adds.
    log = run_git([
        "log", f"--since={args.since}", "--date=format:%Y-%m-%d",
        "--pretty=format:@@%ad", "--numstat",
    ])
    adds = run_git([
        "log", f"--since={args.since}", "--date=format:%Y-%m-%d",
        "--pretty=format:@@%ad", "--name-status", "--diff-filter=A",
    ])

    weeks = defaultdict(lambda: defaultdict(int))
    cur = None
    for line in log.splitlines():
        if line.startswith("@@"):
            cur = iso_week(line[2:])
            weeks[cur]["commits"] += 1
            continue
        if not line.strip() or cur is None:
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        a, _d, path = parts
        if a == "-":
            continue  # binary
        n = int(a)
        # Code vs data split (M0 finding 2: the W29/W31 "outliers" were verified
        # ~99% code-extension lines, so the split is reported, not assumed).
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        is_code = ext in ("cpp", "hpp", "h", "c", "py", "ps1", "cmake", "mjs", "js", "ts")
        if path.startswith(("src/", "include/", "bindings/")):
            weeks[cur]["eng_code" if is_code else "data_add"] += n
        elif path.startswith("tools/"):
            weeks[cur]["tool_code" if is_code else "data_add"] += n
        elif path.startswith(DOC_PREFIXES) or (path.endswith(".md") and "/" not in path):
            weeks[cur]["doc_add"] += n

    cur = None
    for line in adds.splitlines():
        if line.startswith("@@"):
            cur = iso_week(line[2:])
            continue
        if not line.startswith("A\t") or cur is None:
            continue
        path = line[2:]
        if path.startswith("docs/maintenance/"):
            weeks[cur]["newdoc"] += 1
        if "SESSION_CLOSEOUT_" in path:
            weeks[cur]["closeout"] += 1
        if path.startswith(("labtalk/registries/proofs.d/", "labtalk/registries/lessons.d/")):
            weeks[cur]["proofs"] += 1
        if path.startswith("coordination/aif/"):
            weeks[cur]["aifclaim"] += 1
        if path.startswith("dottalkpp/data/scripts/") and path.endswith(".dts"):
            weeks[cur]["regress"] += 1

    this_week = f"{dt.date.today().isocalendar()[0]}-W{dt.date.today().isocalendar()[1]:02d}"
    cols = ["commits", "eng_code", "tool_code", "data_add", "doc_add", "newdoc", "closeout", "proofs", "aifclaim", "regress"]
    print(f"{'week':<10}" + "".join(f"{c:>10}" for c in cols) + "  note")
    for wk in sorted(weeks):
        row = weeks[wk]
        note = "<- partial (current week)" if wk == this_week else ""
        print(f"{wk:<10}" + "".join(f"{row.get(c, 0):>10}" for c in cols) + f"  {note}")
    print("\nsource: git log --since={} on the current branch; author dates; binaries skipped.".format(args.since))
    print("No single column is the finding (charter C2): read them together.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
