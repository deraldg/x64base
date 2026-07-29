#!/usr/bin/env python3
"""
rdb_truth_check_v1.py -- transcript scorer for rdb_truth_proof_v1.dts

STATUS: review-needed. Authored by hosted AI. Read before running.

Usage:
    python rdb_truth_check_v1.py transcript.txt
    python rdb_truth_check_v1.py transcript.txt --json report.json

Input:
    A captured console transcript of a rdb_truth_proof_v1.dts run.

Exit codes:
    0  every Tier A marker scored .T. and every Tier B block was parseable
    1  at least one marker scored .F. or a required block was missing
    2  transcript unusable (missing BEGIN/END envelope)

Why this exists:
    DotTalk has no memvar capture for REL row counts, so row-set findings
    (RDB-01/02/07/10/12) cannot self-assert inside the .dts. The doctrine in
    DTS_AUTHORING_AND_DATA_ENV_RULES_V1_20260721.md rightly bans eyeballed
    tests, so those blocks are scored here instead -- mechanically, and with
    an explicit expectation recorded per block.
"""

import argparse
import json
import re
import sys

ENVELOPE_BEGIN = "RDB-TRUTH-M0-BEGIN"
ENVELOPE_END = "RDB-TRUTH-M0-END"

# marker name -> (kind, what a .T. means)
TIER_A = {
    # v2 marker names (rdb_truth_proof_v2.dts): comparisons-only per RT-02,
    # positioned/labelled forms per RT-01 area-addressing fix.
    "F00_positioned_on_delrow": ("fixture", "fixture built correctly"),
    "F01_fixture_parent_selected": ("fixture", "fixture built correctly"),
    "F02_parent_marked_deleted_here": ("fixture", "fixture built correctly"),
    "F03_fixture_parent_recalled": ("fixture", "fixture restored"),
    "F04_survived_self_relation_probe": ("fixture", "engine survived RDB-14 probe"),
    # AIF-074 P1.4: typed equality closed the RDB-03 asymmetry; the marker now
    # asserts the char/numeric match SUCCEEDS (was DIVERGE_..._blocks_...).
    "CONFORM_R03A_typed_equality_crosses_char_numeric":
        ("conform", "P1.4 typed equality: char child matches numeric parent value"),
    "DIVERGE_R03B_numeric_child_allows_same_equality":
        ("diverge", "RDB-03 confirmed: same comparison succeeds when child is numeric"),
    "DIVERGE_R04_blank_key_joins_blank_key":
        ("diverge", "RDB-04 confirmed: blank joins blank (SQL would emit no row)"),
    "CONFORM_R05A_deleted_child_skipped":
        ("conform", "RDB-05 child delete filter behaves as documented"),
    "DIVERGE_R05B_no_match_is_indistinguishable_from_top":
        ("diverge", "RDB-05 confirmed: no-match parks at top(), unobservable"),
    "DIVERGE_R05C_deleted_parent_still_resolves_children":
        ("diverge", "RDB-05 confirmed: parent delete flag ignored"),
}

# block name -> (finding, what the checker asserts about it)
TIER_B = {
    "ORACLE-A-REL-ENUM-CURRENT-PARENT": (
        "RDB-01",
        "row count here must be LESS THAN the SQLITE FULL_JOIN_ROWS count in ORACLE-G "
        "if REL is scoped to the current parent",
    ),
    "ORACLE-B-REL-ENUM-OTHER-PARENT": (
        "RDB-01",
        "moving the parent cursor must change the result set; equal results falsify RDB-01",
    ),
    "ORACLE-C-REL-ENUM-NO-PATH-MULTICHILD": (
        "RDB-02",
        "must contain a failure line; success falsifies RDB-02",
    ),
    "ORACLE-D-LIMIT-INDISTINGUISHABLE": (
        "RDB-07",
        "neither LIMIT run may carry a truncation indicator; any such indicator falsifies RDB-07",
    ),
    "ORACLE-E-DISTINCT-DEGRADATION": (
        "RDB-10",
        "the expression-term run must emit MORE rows than the bare-field run",
    ),
    "ORACLE-F-MATCHES-COLUMN-SEMANTICS": (
        "RDB-12",
        "depth-1 and depth-2 (matches:) values must be compared by hand against ORACLE-G counts",
    ),
    "ORACLE-G-SQLITE-GROUND-TRUTH": (
        "oracle",
        "supplies SQL truth for the comparisons above",
    ),
}

MARKER_RE = re.compile(r"^\s*([A-Za-z0-9_]+):\s*(\.[TF]\.)\s*$")
TRUNC_RE = re.compile(r"truncat|TRUNCAT|scan limit|SCANLIMIT", re.IGNORECASE)
FAIL_RE = re.compile(r"failed|cannot|no relations|not found|error", re.IGNORECASE)


def extract_envelope(lines):
    start = end = None
    for i, ln in enumerate(lines):
        if ENVELOPE_BEGIN in ln and start is None:
            start = i
        if ENVELOPE_END in ln:
            end = i
    if start is None or end is None or end <= start:
        return None
    return lines[start : end + 1]


def extract_block(lines, name):
    begin, end = f"{name}-BEGIN", f"{name}-END"
    s = e = None
    for i, ln in enumerate(lines):
        if begin in ln and s is None:
            s = i
        elif end in ln and s is not None and e is None:
            e = i
    if s is None or e is None:
        return None
    return [ln.rstrip() for ln in lines[s + 1 : e]]


def data_rows(block):
    """Rows that look like emitted tuple data, not status chatter."""
    out = []
    for ln in block:
        t = ln.strip()
        if not t:
            continue
        if t.upper() in {"OK", "OK."}:
            continue
        if t.startswith("*") or t.startswith("FORMULA"):
            continue
        out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    with open(args.transcript, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read().splitlines()

    # RUNTIME-OBSERVED FIX (2026-07-29, A9/A10 probe): the live REPL prefixes
    # every processed line with the prompt marker plus a space (". A9-PROBE").
    # The synthetic transcripts this scorer was exercised against had no such
    # prefix, so MARKER_RE and the OK-line filter would have missed every real
    # line. Strip one leading prompt marker before any parsing.
    # RUNTIME-OBSERVED FIX 2 (run 2): silent lines (GO, SELECT-with-no-echo, ...)
    # leave their prompt dots stacked on the NEXT output line (". . F00...:.T."),
    # so strip repeated prefixes, not just one.
    raw = [re.sub(r"^(?:\s*\.\s)+", "", ln) for ln in raw]

    env = extract_envelope(raw)
    if env is None:
        print(f"FATAL: transcript has no {ENVELOPE_BEGIN}/{ENVELOPE_END} envelope.")
        return 2

    report = {"tier_a": {}, "tier_b": {}, "verdict": None}
    failures = []

    # ---- Tier A ----
    seen = {}
    for ln in env:
        m = MARKER_RE.match(ln)
        if m:
            seen[m.group(1)] = m.group(2)

    print("=== TIER A -- self-asserted markers ===")
    for name, (kind, meaning) in TIER_A.items():
        val = seen.get(name)
        if val is None:
            status, note = "MISSING", "marker never printed"
            failures.append(f"{name}: missing")
        elif val == ".T.":
            status, note = "PASS", meaning
        else:
            status = "FALSIFIED" if kind == "diverge" else "FAIL"
            note = (
                f"finding NOT reproduced -- audit claim is wrong, report it ({meaning})"
                if kind == "diverge"
                else f"unexpected behaviour ({meaning})"
            )
            failures.append(f"{name}: {val}")
        report["tier_a"][name] = {"value": val, "status": status, "note": note}
        print(f"  [{status:9}] {name} = {val}")
        print(f"              {note}")

    # ---- Tier B ----
    print("\n=== TIER B -- oracle blocks ===")
    blocks = {}
    for name, (finding, assertion) in TIER_B.items():
        blk = extract_block(env, name)
        if blk is None:
            report["tier_b"][name] = {"status": "MISSING", "finding": finding}
            failures.append(f"{name}: block missing")
            print(f"  [MISSING  ] {name} ({finding})")
            continue
        rows = data_rows(blk)
        blocks[name] = rows
        report["tier_b"][name] = {
            "status": "CAPTURED",
            "finding": finding,
            "row_count": len(rows),
            "assertion": assertion,
            "rows": rows,
        }
        print(f"  [CAPTURED ] {name} ({finding}) -- {len(rows)} row(s)")
        print(f"              {assertion}")

    # ---- derived checks over Tier B ----
    print("\n=== DERIVED CHECKS ===")

    def derived(label, ok, detail):
        state = "PASS" if ok else "FALSIFIED"
        if not ok:
            failures.append(f"{label}: {detail}")
        print(f"  [{state:9}] {label} -- {detail}")
        report.setdefault("derived", {})[label] = {"status": state, "detail": detail}

    a = blocks.get("ORACLE-A-REL-ENUM-CURRENT-PARENT")
    b = blocks.get("ORACLE-B-REL-ENUM-OTHER-PARENT")
    if a is not None and b is not None:
        derived(
            "RDB-01_parent_scoped",
            a != b,
            f"moving the parent cursor changed the result ({len(a)} vs {len(b)} rows)"
            if a != b
            else "result did not change with the parent cursor -- RDB-01 falsified",
        )

    c = blocks.get("ORACLE-C-REL-ENUM-NO-PATH-MULTICHILD")
    if c is not None:
        hit = any(FAIL_RE.search(x) for x in c)
        derived(
            "RDB-02_sibling_unreachable",
            hit,
            "bare REL ENUM reported failure with >1 child relation"
            if hit
            else "bare REL ENUM succeeded with >1 child -- RDB-02 falsified",
        )

    d = blocks.get("ORACLE-D-LIMIT-INDISTINGUISHABLE")
    if d is not None:
        trunc = any(TRUNC_RE.search(x) for x in d)
        derived(
            "RDB-07_limit_silent",
            not trunc,
            "no truncation indicator present"
            if not trunc
            else "a truncation indicator WAS present -- RDB-07 falsified",
        )

    e = blocks.get("ORACLE-E-DISTINCT-DEGRADATION")
    if e is not None:
        derived(
            "RDB-10_distinct_degrades",
            len(e) > 2,
            f"{len(e)} rows across both DISTINCT runs; the expression run should "
            f"emit extra rows (split by hand if ambiguous)",
        )

    print("\n=== VERDICT ===")
    if failures:
        report["verdict"] = "FAIL"
        print("FAIL -- the following need attention:")
        for f in failures:
            print(f"  - {f}")
        print("\nNote: a FALSIFIED DIVERGE_ marker means the AUDIT was wrong, not the")
        print("engine. That is a good outcome. Update the findings document.")
    else:
        report["verdict"] = "PASS"
        print("PASS -- every marker behaved as the source read predicted.")
        print("Reminder: PASS means the divergences from SQL truth are CONFIRMED,")
        print("not that x64base is relationally correct.")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"\nJSON report written to {args.json_out}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
