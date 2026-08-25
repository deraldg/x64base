#!/usr/bin/env python3
"""Extract the authored tracking registries into schema-aligned CSVs for IMPORT.

The EXTRACT + NORMALIZE half of the tracking-state dogfood seeder
(TRACKING_STATE_DOGFOOD_LANE_V1.md, AIF-086 M1). Reads the authored registries
that drift -- the AIF intake queue, ai_runs.yaml, proofs.yaml -- and writes one CSV
per portal tracking table (portal/tracking_schema.hpp): SYSLANE, SYSRUN,
SYSRUNLANE, SYSPROOF. (SYSTASK is deferred: its source registry is a nested
doc-flush structure, not a flat task list -- second-ring work per decision C.)

CSV columns are the exact DBF FIELD NAMES (case-insensitive header mapping is how
`IMPORT` binds columns to fields), and FKs are NATURAL KEYS (member.mkey, LKEY,
RKEY) per the schema's key-FK decision -- so the load is a clean CREATE X64 +
IMPORT with no key->id resolution. A synthetic monotonic ID is assigned per row;
epochs default to 0 when the authored source has no date; ROWVER starts at 1.

The LOAD half (CREATE the tables + IMPORT the CSVs on the engine) is
load_tracking_tables.dts -- a maintainer step (the steward's sandbox glibc cannot
run the engine; measured 2026-08-04).

Idempotent: the CSVs are rewritten each run (a full snapshot re-seed).

Usage:
  python tools/tracking/seed_tracking.py                 # -> dottalkpp/data/metadata/portal/seed/
  python tools/tracking/seed_tracking.py --out /tmp/seed
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "dottalkpp" / "data" / "metadata" / "portal" / "seed"
DOCPAT = re.compile(r"([\w./-]+\.(?:md|csv|json|yaml|html|cpp|hpp|py))")
MEMBERPAT = re.compile(r"(member\.[A-Za-z0-9_.]+)")
PROJPAT = re.compile(r"(project\.[A-Za-z0-9_.]+)")
# R126: an AIF number IS AN INTEGER. The zero padding is a DISPLAY convention.
# Match loosely (any width, any padding) and normalise to int; render with %03d,
# which is a MINIMUM width and widens by itself past 999. Measured 2026-08-25:
# `AIF-\d{3}` read "AIF-1000" as NO MATCH in five readers and, in
# tools/tracking/seed_tracking.py, as "AIF-100" -- a DIFFERENT, ALREADY-TAKEN
# number. Silent identity collision, not a decline.
# ... AND NOT A BRACE-EXPANSION SHORTHAND. Measured 2026-08-25 while widening:
# docs/maintenance/SESSION_CLOSEOUT_AIF112_PHASE1_AND_LOCK_MUTUAL_EXCLUSION_
# 2026-08-15.md:60 writes `coordination/aif/AIF-11{6,7}.claim` for the PAIR
# 116 and 117. "{" is a non-word character, so a bare \b happily matched
# "AIF-11" and resolved it to AIF-011 -- a real number, wrongly cited. The old
# \d{3} pattern missed it by accident; the widened one must decline it on
# purpose. Only the PROSE scanners need this. Row-anchored patterns do not: a
# row id sits at line start and is followed by "|".
AIFPAT = re.compile(r"\bAIF-0*(\d+)\b(?!\{)")

COLUMNS = {
    "SYSLANE": ["ID", "LKEY", "TITLE", "OWNERKEY", "STEWARDKEY", "PROJECT", "SDLCLANE",
                "STATUS", "CLAIMED", "ANCHOR", "OPENAT", "CLOSEAT", "ROWVER"],
    "SYSRUN": ["ID", "RKEY", "MEMBERKEY", "ROLE", "OWNERKEY", "COMMITKEY", "AUTHORKEY",
               "PLANKEY", "PROJECT", "STATUS", "STARTAT", "BRANCH", "HANDLE", "REPORT", "ROWVER"],
    "SYSRUNLANE": ["RUNKEY", "LANEKEY"],
    "SYSPROOF": ["ID", "PKEY", "LABEL", "STATE", "LANEKEY", "SOURCE", "OBSAT", "ROWVER"],
    "SYSTASK": ["ID", "TKEY", "TITLE", "ASSIGNKEY", "STATUS", "CHANNEL", "LANEKEY",
                "DUEAT", "DONEAT", "ROWVER"],
}

# ai_portal_tasks.yaml uses lifecycle-phrase statuses; fold them onto the SYSTASK
# ladder (0 open, 1 in_progress, 2 done, 3 returned, 4 parked). Unknown -> 0 open.
_TASK_STATUS = {
    "open": 0, "proposed": 0, "backlog": 0, "staged": 0, "review_needed": 0,
    "gate6_scope_pending": 0,
    "active": 1, "active_seed": 1, "active_prototype": 1, "in_progress": 1,
    "closed_runtime_observed": 2, "closed_development_slice": 2, "closed": 2, "done": 2,
    "returned_for_correction": 3, "returned": 3,
    "parked": 4,
}


def _task_status(s: str) -> int:
    return _TASK_STATUS.get((s or "").strip().lower(), 0)


def _epoch(datestr: str) -> int:
    try:
        return int(dt.datetime.strptime(str(datestr)[:10], "%Y-%m-%d")
                   .replace(tzinfo=dt.timezone.utc).timestamp())
    except (ValueError, TypeError):
        return 0


def _lane_status(text: str) -> int:
    """Coarse first-pass status code (schema STATUS ladder). Refinement pending."""
    t = (text or "").lower()
    if "retired" in t:
        return 5
    if "closed" in t or "abandoned" in t:
        return 4
    if "landed" in t or "signed" in t or "accepted" in t or "complete" in t:
        return 3
    if "partial" in t or "mixed" in t or "pending" in t or " m1" in t or "m0" in t:
        return 2
    if "proposed" in t or "design-intended" in t or "findings recorded" in t or "registered" in t:
        return 0
    return 1


def extract_lanes(root: Path) -> list[dict]:
    rows = []
    qtxt = (root / "docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md").read_text(encoding="utf-8", errors="replace")
    for line in qtxt.splitlines():
        if not re.match(r"^\|\s*AIF-\d+", line):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 6:
            continue
        lkey = c[0]
        title = re.sub(r",\s*(Cowork|Claude|Codex|Grok|ChatGPT)[^,]*$", "", c[1])
        notes = c[-1]
        m_doc = DOCPAT.search(c[4] if len(c) > 4 else "") or DOCPAT.search(notes)
        ms = re.search(r"steward[^\n]{0,20}?(member\.[A-Za-z0-9_.]+)", notes)
        steward = ms.group(1) if ms else next((m for m in MEMBERPAT.findall(notes) if m != "member.derald"), "")
        proj = PROJPAT.search(c[3] if len(c) > 3 else "") or PROJPAT.search(notes)
        rows.append({
            "LKEY": lkey, "TITLE": title, "OWNERKEY": "member.derald", "STEWARDKEY": steward,
            "PROJECT": proj.group(1) if proj else "project.x64base.runtime",
            "SDLCLANE": "", "STATUS": _lane_status(c[5] if len(c) > 5 else ""),
            "CLAIMED": 1 if (root / "coordination" / "aif" / f"{lkey}.claim").exists() else 0,
            "ANCHOR": m_doc.group(1) if m_doc else "", "OPENAT": 0, "CLOSEAT": 0, "ROWVER": 1,
        })
    return rows


def extract_runs(root: Path) -> tuple[list[dict], list[dict]]:
    d = yaml.safe_load((root / "labtalk/registries/ai_runs.yaml").read_text(encoding="utf-8", errors="replace"))
    runs, runlane = [], []
    for r in d.get("runs", []):
        rkey = r.get("run_id", "")
        git = r.get("git") or {}
        runs.append({
            "RKEY": rkey, "MEMBERKEY": r.get("member", ""), "ROLE": r.get("role", ""),
            "OWNERKEY": r.get("owner", ""), "COMMITKEY": r.get("committer", ""),
            "AUTHORKEY": r.get("authored_by", ""), "PLANKEY": r.get("planned_by", ""),
            "PROJECT": r.get("project", ""), "STATUS": 1 if r.get("status") == "closed" else 0,
            "STARTAT": _epoch(r.get("started", "")), "BRANCH": git.get("branch", ""),
            "HANDLE": r.get("handle_binding", ""), "REPORT": rkey, "ROWVER": 1,
        })
        for lane in (r.get("lanes") or []):
            runlane.append({"RUNKEY": rkey, "LANEKEY": lane})
    return runs, runlane


def _proof_lane(p: dict) -> str:
    """First AIF-NNN mentioned in the proof's text fields -> its lane, or '' if none.
    Proofs carry no explicit lane field, so derive it from id/label/notes/source/related."""
    blob = " ".join(str(p.get(k, "")) for k in ("id", "label", "notes", "source", "item_id"))
    blob += " " + " ".join(str(x) for x in (p.get("related") or []))
    m = AIFPAT.search(blob)
    return f"AIF-{int(m.group(1)):03d}" if m else ""


def extract_proofs(root: Path) -> list[dict]:
    d = yaml.safe_load((root / "labtalk/registries/proofs.yaml").read_text(encoding="utf-8", errors="replace"))
    return [{
        "PKEY": p.get("id", ""), "LABEL": p.get("label", ""), "STATE": p.get("state", ""),
        "LANEKEY": _proof_lane(p), "SOURCE": str(p.get("source", "")), "OBSAT": 0, "ROWVER": 1,
    } for p in d.get("proofs", [])]


def extract_tasks(root: Path) -> list[dict]:
    d = yaml.safe_load((root / "labtalk/registries/ai_portal_tasks.yaml")
                       .read_text(encoding="utf-8", errors="replace"))
    rows = []
    for t in d.get("tasks", []):
        owner = str(t.get("owner", "")).strip()
        assign = owner if owner.startswith("member.") else (f"member.{owner.lower()}" if owner else "")
        rows.append({
            # TKEY is C(48); a couple of ids run longer and IMPORT truncates. The id
            # stays the natural key; widen the field only if a collision appears.
            "TKEY": t.get("id", ""), "TITLE": t.get("title", ""), "ASSIGNKEY": assign,
            "STATUS": _task_status(t.get("status", "")), "CHANNEL": t.get("channel", ""),
            "LANEKEY": t.get("ticket", ""), "DUEAT": 0, "DONEAT": 0, "ROWVER": 1,
        })
    return rows


def _assign_ids(rows: list[dict]) -> list[dict]:
    for i, r in enumerate(rows, 1):
        r["ID"] = i
    return rows


def _write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        wtr = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        wtr.writeheader()
        for row in rows:
            wtr.writerow({k: row.get(k, "") for k in columns})


def seed(root: Path, out: Path) -> dict:
    lanes = _assign_ids(extract_lanes(root))
    runs, runlane = extract_runs(root)
    runs = _assign_ids(runs)
    proofs = _assign_ids(extract_proofs(root))
    tasks = _assign_ids(extract_tasks(root))
    _write_csv(out / "SYSLANE.csv", lanes, COLUMNS["SYSLANE"])
    _write_csv(out / "SYSRUN.csv", runs, COLUMNS["SYSRUN"])
    _write_csv(out / "SYSRUNLANE.csv", runlane, COLUMNS["SYSRUNLANE"])
    _write_csv(out / "SYSPROOF.csv", proofs, COLUMNS["SYSPROOF"])
    _write_csv(out / "SYSTASK.csv", tasks, COLUMNS["SYSTASK"])
    return {"SYSLANE": len(lanes), "SYSRUN": len(runs), "SYSRUNLANE": len(runlane),
            "SYSPROOF": len(proofs), "SYSTASK": len(tasks)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Extract tracking registries to schema-aligned CSVs.")
    ap.add_argument("--root", default=str(REPO))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)
    counts = seed(Path(args.root), Path(args.out))
    print("seed_tracking: wrote " + ", ".join(f"{k}={v}" for k, v in counts.items()) + f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
