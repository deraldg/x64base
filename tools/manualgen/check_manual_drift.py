#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual drift gate -- MANUAL-ASSEMBLY lane, M4.

Fails the build when a *generated* region of the committed assembled manual no
longer matches what its generator produces from current source. This is the
manual-side twin of the AIF-025 catalog checks and the AIF-032 diagram check.

How it works:
  1. Re-assemble the manual fresh into a temp dir (from CURRENT source).
  2. Slice both the committed manual and the fresh manual into per-part MAN
     regions (by part id).
  3. Normalise volatile tokens (build timestamps) and compare each region.
  4. Classify each mismatch by the part's class/mode:
        generated / bind   -> FAIL  (stale generated content; blocks the build)
        derived  (candidate)
        maintained (authored)
        reported (append)  -> REVIEW (regenerate-or-review signal; non-blocking)
        static             -> SKIP

Exit code is nonzero only if a FAIL-severity region drifted, so the gate can sit
on the fullstack push. Acceptance stays gated elsewhere; this only detects
staleness. Target Python 3.12; runs on 3.10.
"""

import os
import re
import sys
import json
import shutil
import tempfile
import subprocess

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MANIFEST = os.path.join(HERE, "manual_assembly_manifest.yaml")
ASSEMBLER = os.path.join(HERE, "assemble_manual.py")
COMMITTED_MD = os.path.join(
    ROOT, "docs/manuals/developer/manualgen/generated/assembled/developer_manual_assembled_v1.md"
)
DRIFT_REPORT = os.path.join(
    ROOT, "docs/manuals/developer/manualgen/generated/assembled/drift_report_v1.json"
)

TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def rd(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def slice_region(text, pid):
    """Return the inner body of the MAN region for `pid` (anchors excluded)."""
    pat = (
        r"^<!-- MAN:(?:BEGIN|APPEND) id=%s [^\n]*-->\n(.*?)\n<!-- MAN:END id=%s -->"
        % (re.escape(pid), re.escape(pid))
    )
    m = re.search(pat, text, re.S | re.M)
    return m.group(1) if m else None


def norm(s):
    if s is None:
        return None
    return TS.sub("<TS>", s).strip()


def severity_for(part):
    if part["region_mode"] == "bind" or part["class"] == "generated":
        return "FAIL"
    if part["class"] == "static":
        return "SKIP"
    return "REVIEW"


def main():
    if not os.path.exists(COMMITTED_MD):
        print("ERROR: no committed manual — run assemble_manual.py first.", file=sys.stderr)
        return 2

    manifest = yaml.safe_load(rd(MANIFEST))
    parts = sorted(manifest["parts"], key=lambda p: p["order"])

    # 1. fresh build into a temp dir
    tmp = tempfile.mkdtemp(prefix="manual_drift_")
    try:
        r = subprocess.run(
            [sys.executable, ASSEMBLER, "--out-dir", tmp],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        if r.returncode != 0:
            print("ERROR: fresh assembly failed:\n" + r.stdout.decode(), file=sys.stderr)
            return 2
        fresh_md = rd(os.path.join(tmp, "developer_manual_assembled_v1.md"))
        committed_md = rd(COMMITTED_MD)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    results = []
    fails, reviews, missing = 0, 0, 0
    for p in parts:
        pid = p["id"]
        sev = severity_for(p)
        if sev == "SKIP":
            results.append({"id": pid, "status": "skip", "severity": "SKIP"})
            continue
        a = norm(slice_region(committed_md, pid))
        b = norm(slice_region(fresh_md, pid))
        if a is None or b is None:
            missing += 1
            results.append(
                {"id": pid, "status": "region-missing", "severity": "ERROR",
                 "committed_found": a is not None, "fresh_found": b is not None}
            )
            continue
        if a == b:
            results.append({"id": pid, "status": "match", "severity": sev})
        else:
            if sev == "FAIL":
                fails += 1
            else:
                reviews += 1
            results.append({"id": pid, "status": "DRIFT", "severity": sev})

    report = {
        "schema": "dottalk.manual.drift_report.v1",
        "manual": os.path.relpath(COMMITTED_MD, ROOT).replace("\\", "/"),
        "parts_checked": sum(1 for r in results if r["status"] != "skip"),
        "fail_drift": fails,
        "review_drift": reviews,
        "region_missing": missing,
        "gate": "PASS" if (fails == 0 and missing == 0) else "FAIL",
        "results": results,
    }
    with open(DRIFT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # console summary
    print("MANUAL DRIFT GATE")
    for r in results:
        if r["status"] in ("DRIFT", "region-missing"):
            print("  [%s] %-28s %s" % (r["severity"], r["id"], r["status"]))
    print(
        "gate=%s  fail=%d  review=%d  missing=%d  (checked %d)"
        % (report["gate"], fails, reviews, missing, report["parts_checked"])
    )
    if reviews and fails == 0 and missing == 0:
        print("  (review-level drift is non-blocking: regenerate-or-review)")
    return 0 if (fails == 0 and missing == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
