#!/usr/bin/env python3
"""Completeness reconciliation for the AI report index (OI-024 decision 1).

THE GAP THIS CLOSES IS ABSENCE, NOT MALFORMATION.

`labtalk/ai_portal/audit_trail.py` checks that a record which IS PRESENT is
well formed. Nothing checked that a KNOWN SUBMISSION HAS A RECORD. The
published data-flow diagram draws that check ("has all records?", absent ->
flag) as a DASHED box, meaning proposed, and it stayed proposed long enough to
cost real work: AIF-078 independently re-derived Grok's DTSHEMA v4 because the
intake that already contained it was never indexed, and neither session could
see the other. MONITOR_HARVEST_CURATE_EXTERNAL_AI_V1.md item 4 specifies this
reconciliation; OI-024 decision 1 is the instruction to build it.

WHAT IT RECONCILES

  A. INTAKE DIRECTORIES -> index. Every directory under
     docs/maintenance/external_ai_intake/ must be named by some entry's `path`.
     This one is RULED: the index's own header says received packages "MUST be
     added here". A miss here is a miss.

  B. RUNS -> index. Every run in runs.d/ against the index's report_ids.
     This one is NOT RULED and is therefore ADVISORY ONLY, never strict. The
     index calls itself the lookup layer for "AI-authored reports and received
     external-AI change packages", and whether every internal run owes an entry
     is a maintainer question. Reporting it is useful; failing on it would be
     this gate inventing policy, which is how a gate gets switched off.

  C. MERGE FRESHNESS. runs.d/ is the canonical store -- one file per record so
     two sessions never touch the same file -- and ai_runs.yaml is GENERATED
     from it. Measured 2026-09-19: 23 fragments, 8 records in the merged file,
     fourteen real runs missing including the previous day's. So this gate
     reads runs.d/ and CHECKS the merged file rather than trusting it. A
     completeness gate that reads a stale ledger reproduces, one layer down,
     the exact defect it was written to catch.

WHY IT PRINTS POPULATIONS EVEN WHEN IT FINDS NOTHING

OI-023's shape: a proof generator with no `else` cannot say "nothing to prove"
distinctly from "everything proved". Zero findings over zero inputs is not the
same claim as zero findings over fourteen, and a reader cannot tell them apart
from a silent PASS. Every run prints both numbers.

EXIT CODES
  0  report-only (default), whatever was found
  0  --strict with no A or C findings
  2  --strict with A or C findings
  3  the inputs could not be read (never confused with "clean")
"""

import argparse
import os
import sys

try:
    import yaml
except ImportError:
    print("check-report-index: PyYAML is not importable under "
          f"{sys.executable}.", file=sys.stderr)
    print("  This gate reads YAML registries. Run it under an interpreter that "
          "has PyYAML (the repo venv .venv312 does).", file=sys.stderr)
    sys.exit(3)

INTAKE_DIR = "docs/maintenance/external_ai_intake"
INDEX_FILE = "labtalk/registries/ai_report_index.yaml"
RUNS_DIR = "labtalk/registries/runs.d"
RUNS_MERGED = "labtalk/registries/ai_runs.yaml"


def repo_root(start):
    # The gate is invoked from anywhere; anchor on this file, not on cwd.
    here = os.path.dirname(os.path.abspath(start))
    return os.path.dirname(os.path.dirname(here))


def load_index(root):
    path = os.path.join(root, INDEX_FILE)
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    reports = data.get("reports") or []
    ids = set()
    paths = set()
    for entry in reports:
        if not isinstance(entry, dict):
            continue
        rid = entry.get("report_id")
        if rid:
            ids.add(str(rid).strip())
        p = entry.get("path")
        if p:
            # Normalize both separators: an index written on Windows and a walk
            # done on Linux must compare equal, or every row reads as a miss.
            paths.add(str(p).strip().replace("\\", "/"))
    return ids, paths, len(reports)


def intake_dirs(root):
    base = os.path.join(root, INTAKE_DIR)
    if not os.path.isdir(base):
        return []
    return sorted(
        name for name in os.listdir(base)
        if os.path.isdir(os.path.join(base, name))
    )


def run_fragments(root):
    base = os.path.join(root, RUNS_DIR)
    if not os.path.isdir(base):
        return {}
    out = {}
    for name in sorted(os.listdir(base)):
        if not name.endswith(".yaml") or name.startswith("_"):
            continue
        with open(os.path.join(base, name), "r", encoding="utf-8") as handle:
            frag = yaml.safe_load(handle) or {}
        if isinstance(frag, dict) and frag.get("run_id"):
            out[str(frag["run_id"]).strip()] = frag
    return out


def merged_run_ids(root):
    path = os.path.join(root, RUNS_MERGED)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    runs = data.get("runs") or []
    return {str(r.get("run_id")).strip() for r in runs
            if isinstance(r, dict) and r.get("run_id")}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strict", action="store_true",
                    help="exit 2 when a ruled population (A or C) has a gap")
    ap.add_argument("--root", default=None, help="repository root override")
    args = ap.parse_args(argv)

    root = args.root or repo_root(__file__)

    try:
        index_ids, index_paths, index_rows = load_index(root)
        dirs = intake_dirs(root)
        frags = run_fragments(root)
        merged = merged_run_ids(root)
    except Exception as exc:                      # noqa: BLE001 -- reported, not hidden
        print(f"check-report-index: could not read the registries: {exc}",
              file=sys.stderr)
        return 3

    print("check-report-index: reconciling known submissions against the index")
    print(f"  index rows          : {index_rows}")
    print(f"  intake directories  : {len(dirs)}")
    print(f"  run fragments       : {len(frags)}")

    # ---- A. intake directories that no index entry names --------------------
    # Matched by PREFIX, not equality: an entry's `path` points at a file
    # INSIDE the directory (its MANIFEST.md or an assessment), so the test is
    # whether any indexed path lives under the directory.
    unindexed_dirs = []
    for name in dirs:
        prefix = f"{INTAKE_DIR}/{name}/"
        if not any(p.startswith(prefix) for p in index_paths):
            unindexed_dirs.append(name)

    # ---- B. runs with no index entry (ADVISORY, unruled) --------------------
    unindexed_runs = sorted(rid for rid in frags if rid not in index_ids)

    # ---- C. merge freshness -------------------------------------------------
    stale_merge = []
    if merged is None:
        stale_merge = ["<merged ledger absent>"]
    else:
        stale_merge = sorted(rid for rid in frags if rid not in merged)

    print()
    if unindexed_dirs:
        print(f"A. UNINDEXED INTAKE DIRECTORIES -- {len(unindexed_dirs)} of "
              f"{len(dirs)}. The index header rules that received packages MUST "
              f"be added; these are misses.")
        for name in unindexed_dirs:
            print(f"     {INTAKE_DIR}/{name}/")
    else:
        print(f"A. every one of the {len(dirs)} intake directories is named by "
              f"an index entry.")

    print()
    if stale_merge:
        print(f"C. THE MERGED RUN LEDGER IS STALE -- {len(stale_merge)} "
              f"fragment(s) in {RUNS_DIR}/ are absent from {RUNS_MERGED}.")
        print("   Anything reading the merged file sees an incomplete picture "
              "and cannot know it. Regenerate:")
        print("     python tools/registries/registry_fragments.py merge --write")
        for rid in stale_merge:
            print(f"     {rid}")
    else:
        print(f"C. the merged ledger carries all {len(frags)} fragments.")

    print()
    if unindexed_runs:
        print(f"B. ADVISORY, UNRULED -- {len(unindexed_runs)} of {len(frags)} "
              f"runs have no index entry. Whether an internal run owes one is a "
              f"maintainer decision (OI-024); this gate reports and never fails "
              f"on it.")
        for rid in unindexed_runs:
            member = frags[rid].get("member", "?")
            print(f"     {rid}  ({member})")
    else:
        print(f"B. all {len(frags)} runs appear in the index.")

    ruled_findings = len(unindexed_dirs) + len(stale_merge)
    print()
    print(f"check-report-index: ruled findings {ruled_findings}, "
          f"advisory findings {len(unindexed_runs)}.")

    if args.strict and ruled_findings:
        print("check-report-index: FAIL (--strict)")
        return 2
    if ruled_findings:
        print("check-report-index: ADVISORY -- report-only; pass --strict to "
              "make these block.")
    else:
        print("check-report-index: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
