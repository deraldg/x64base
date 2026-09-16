#!/usr/bin/env python3
"""Derive the manual anchor map's MD tables from the CSV, which is the source.

WHY THIS EXISTS
    The anchor map lived in two hand-maintained artifacts:

        DOTTALKPP_MANUAL_ANCHOR_MAP_V1.md              (what build_manual_docx.py reads)
        docs/manuals/anchors/manual_generation_anchor_map_v1.csv

    Nothing generated either one from the other, so they drifted. Measured
    2026-09-15: one row's state was spelled `proven/candidate` in the MD and
    `proven_candidate` in the CSV, and `proven/candidate` was not in the map's
    own documented vocabulary at all. One row, three disagreements.

    The CSV is now the source. The MD keeps all of its prose; only the three
    anchor tables are generated, between explicit markers. build_manual_docx.py
    is unaffected: it scans for lines beginning with a backticked ANCHOR id
    wherever they appear, which is still exactly what this emits.

USAGE
    python tools/fullstack_docs/derive_anchor_map.py --engine D:\\code\\ccode
    python tools/fullstack_docs/derive_anchor_map.py --engine . --check

    --check prints the drift and exits 1 without writing. That is the gate mode;
    a plain run rewrites the MD in place.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import os
import sys
from pathlib import Path

CSV_REL = Path("docs/manuals/anchors/manual_generation_anchor_map_v1.csv")
MD_REL = Path("DOTTALKPP_MANUAL_ANCHOR_MAP_V1.md")

FIELDS = ["anchor_id", "section", "layer", "layer_label",
          "evidence_paths", "manual_targets",
          "target_manual", "target_level",
          "state", "next_closure_action"]

# WHY target_manual AND target_level EXIST (added 2026-09-16)
#
# `manual_targets` alone cannot answer "what does the manual still need". It
# conflated three different things with nothing to tell them apart, measured
# 2026-09-16 over 79 distinct targets:
#
#   chapter-scale topics with no chapter        (SQLsel, TupTalk, Primary Keys)
#   section-scale targets inside a chapter      (Trinity Headers, x64 Workflow)
#   targets in a DIFFERENT manual entirely      (History, Design Philosophy --
#                                                those are reader-manual topics,
#                                                and the reader manual exists)
#
# Nine of the 79 matched a dev-NN chapter title. The other seventy could only be
# sorted by a person reading each one, which is a census that goes stale the
# moment somebody adds a row.
#
# Both columns are SEMICOLON LISTS ALIGNED 1:1 WITH manual_targets. An anchor
# can legitimately span levels and even manuals -- ANCHOR-REGRESSION-SUITE
# targets a developer chapter AND a site page -- so one value per anchor would
# have been a lie for exactly the rows that matter most. The alignment is
# enforced below and a mismatch is fatal, because a silently misaligned list is
# worse than no column at all: it reads as precision.
TARGET_MANUALS = {"developer", "reader", "command_reference", "site", "none"}
TARGET_LEVELS = {"chapter", "section"}

# The map documents its own vocabulary. A state outside it is an error, not a
# style choice -- that is how `proven/candidate` survived for 79 days.
STATES = {"observed", "proven", "candidate", "proven_candidate", "drift", "deferred"}

SECTIONS = [
    ("core", "Core Anchors", None),
    ("spine", "Spine Anchors (added 2026-09-15)",
     "These bind material the manual ALREADY CARRIES. They were unanchored because the core table\n"
     "was written 2026-06-28 and the doctrine spine kept growing after it -- dev-21, dev-22 and dev-23\n"
     "were all written later. An unanchored chapter is not a missing chapter; it is a chapter whose\n"
     "claims have no recorded evidence path, which is what the anchor rule exists to prevent.\n"),
    ("website", "Website Coverage Anchors (added 2026-09-15)",
     "These are topics the PUBLISHED WEBSITE already covers and the manual does not mention at all.\n"
     "Every row names the site page that makes the claim. They enter at `deferred` by definition:\n"
     "the concept is important and published, and systematic harvesting has not closed it.\n"
     "A site page is evidence that the topic matters to a reader; it is NOT evidence for the claim itself.\n"),
]

HEADER = ("| Anchor ID | Layer | Evidence path | Manual target | State | Next closure action |\n"
          "|---|---|---|---|---|---|")


def begin(key: str) -> str:
    return f"<!-- BEGIN GENERATED anchors:{key} -- derive_anchor_map.py; edit the CSV, not this table -->"


def end(key: str) -> str:
    return f"<!-- END GENERATED anchors:{key} -->"


def load_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        if rdr.fieldnames != FIELDS:
            die(f"{CSV_REL} columns are {rdr.fieldnames}, expected {FIELDS}")
        rows = list(rdr)

    seen: set[str] = set()
    known = {k for k, _, _ in SECTIONS}
    for r in rows:
        aid = r["anchor_id"]
        if not aid.startswith("ANCHOR-"):
            die(f"anchor_id {aid!r} does not start with ANCHOR-")
        if aid in seen:
            die(f"duplicate anchor_id {aid}")
        seen.add(aid)
        if r["section"] not in known:
            die(f"{aid}: section {r['section']!r} not one of {sorted(known)}")
        if r["state"] not in STATES:
            die(f"{aid}: state {r['state']!r} is not in the documented vocabulary "
                f"{sorted(STATES)}. Fix the CSV or amend the vocabulary deliberately.")
        for col in ("evidence_paths", "manual_targets", "next_closure_action", "layer", "layer_label",
                    "target_manual", "target_level"):
            if not r[col].strip():
                die(f"{aid}: {col} is empty")
            if "|" in r[col]:
                die(f"{aid}: {col} contains a pipe, which would break the MD table")

        tg = split_targets(r["manual_targets"])
        tm = split_targets(r["target_manual"])
        tl = split_targets(r["target_level"])
        if not (len(tg) == len(tm) == len(tl)):
            die(f"{aid}: {len(tg)} manual_target(s) but {len(tm)} target_manual and "
                f"{len(tl)} target_level. These three columns are parallel lists and "
                f"must have the same number of semicolon-separated items.")
        for v in tm:
            if v not in TARGET_MANUALS:
                die(f"{aid}: target_manual {v!r} is not in {sorted(TARGET_MANUALS)}")
        for v in tl:
            if v not in TARGET_LEVELS:
                die(f"{aid}: target_level {v!r} is not in {sorted(TARGET_LEVELS)}")
    return rows


def split_targets(cell: str) -> list[str]:
    return [i.strip() for i in cell.split(";") if i.strip()]


def looks_like_path(item: str) -> bool:
    """Evidence items are a mix of real paths and prose ("lock help messages").
    Backticking prose renders it as code and reads as a filename that does not
    exist, so only path-shaped items get code formatting."""
    return any(c in item for c in "/\\*") or item.endswith((".hpp", ".cpp", ".md",
                                                             ".csv", ".json", ".yaml",
                                                             ".dbf", ".dtx", ".py",
                                                             ".ps1", ".txt", ".mdx"))


def render_row(r: dict) -> str:
    ev = "; ".join((f"`{i}`" if looks_like_path(i) else i)
                   for i in (p.strip() for p in r["evidence_paths"].split(";")) if i)
    # Each target carries its own classification rather than the table growing two
    # more columns. Six columns already crowd the page, and the classification is
    # only meaningful next to the target it classifies.
    tg = "; ".join(f"{t} [{m}/{l}]" for t, m, l in
                   zip(split_targets(r["manual_targets"]),
                       split_targets(r["target_manual"]),
                       split_targets(r["target_level"])))
    return (f"| `{r['anchor_id']}` | {r['layer_label']} | {ev} | "
            f"{tg} | {r['state']} | {r['next_closure_action']} |")


def render_block(key: str, rows: list[dict]) -> str:
    body = "\n".join(render_row(r) for r in rows if r["section"] == key)
    return f"{begin(key)}\n{HEADER}\n{body}\n{end(key)}"


def splice(md: str, key: str, block: str) -> str:
    b, e = begin(key), end(key)
    if md.count(b) != 1 or md.count(e) != 1:
        die(f"{MD_REL} must contain exactly one {b!r} and one {e!r} marker pair")
    head, rest = md.split(b, 1)
    _, tail = rest.split(e, 1)
    return head + block + tail


def die(msg: str) -> None:
    print(f"derive_anchor_map: {msg}", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", default=os.environ.get("X64BASE_ENGINE_TREE"),
                    help="engine tree root (or set X64BASE_ENGINE_TREE)")
    ap.add_argument("--check", action="store_true",
                    help="report drift and exit 1 without writing")
    a = ap.parse_args()
    if not a.engine:
        die("pass --engine <tree> or set X64BASE_ENGINE_TREE")

    root = Path(a.engine).resolve()
    csv_path, md_path = root / CSV_REL, root / MD_REL
    for p in (csv_path, md_path):
        if not p.is_file():
            die(f"missing {p}")

    rows = load_rows(csv_path)
    current = md_path.read_text(encoding="utf-8")

    rendered = current
    for key, _title, _lead in SECTIONS:
        rendered = splice(rendered, key, render_block(key, rows))

    counts = {k: sum(1 for r in rows if r["section"] == k) for k, _, _ in SECTIONS}
    summary = ", ".join(f"{k}={v}" for k, v in counts.items())

    # The coverage number the map exists to produce. Printed every run so it can
    # never again require a person to hand-sort 79 strings to find out.
    slots = [(m, l) for r in rows
             for m, l in zip(split_targets(r["target_manual"]),
                             split_targets(r["target_level"]))]
    tally = {}
    for k in slots:
        tally[k] = tally.get(k, 0) + 1
    cov = ", ".join(f"{m}/{l}={n}" for (m, l), n in sorted(tally.items()))
    print(f"anchor map: {len(slots)} target slot(s) -- {cov}")

    if rendered == current:
        print(f"anchor map: IN SYNC -- {len(rows)} anchors ({summary})")
        return 0

    if a.check:
        print(f"anchor map: DRIFT -- {MD_REL} does not match {CSV_REL}")
        diff = difflib.unified_diff(current.splitlines(True), rendered.splitlines(True),
                                    fromfile=f"{MD_REL} (on disk)",
                                    tofile=f"{MD_REL} (derived from CSV)")
        sys.stdout.writelines(diff)
        print("\nThe CSV is the source. Re-run without --check to regenerate.")
        return 1

    md_path.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"anchor map: REGENERATED {MD_REL} -- {len(rows)} anchors ({summary})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
