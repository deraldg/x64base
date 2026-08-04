#!/usr/bin/env python3
"""Extract the authored tracking registries into schema-aligned, key-based CSVs.

This is the EXTRACT + NORMALIZE half of the tracking-state dogfood seeder
(TRACKING_STATE_DOGFOOD_LANE_V1.md, AIF-086 M1). It reads the authored registries
that drift -- the AIF intake queue, ai_runs.yaml, proofs.yaml -- and writes one CSV
per portal tracking table (portal/tracking_schema.hpp): SYSLANE, SYSRUN,
SYSRUNLANE, SYSPROOF.

The CSVs are KEY-BASED intermediates: member references are natural keys
(member.derald), not numeric SYSMEMBER ids, because ids do not exist until the
engine loads the identity catalog. The LOAD half (create the DBF tables and resolve
key -> SYSMEMBER.ID while inserting) is a maintainer/engine step -- the same
handoff shape as SYSRULING seeding. This half is pure Python and fully testable.

Idempotent: the CSVs are rewritten each run; upsert-by-key is the loader's job.

Design rule (from the schema): TABLE = STATE. The long prose (intake Notes, a
proof's evidence essay) is deliberately NOT extracted; it stays in the markdown/
YAML. STATUS mapping is coarse/first-pass and is a documented Phase-0 refinement.

Usage:
  python tools/tracking/seed_tracking.py                 # -> data/metadata/portal/seed/
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
DOCPAT = re.compile(r"([\w./-]+\.(?:md|csv|json|yaml|html|cpp|hpp|py))")
MEMBERPAT = re.compile(r"(member\.[A-Za-z0-9_.]+)")
PROJPAT = re.compile(r"(project\.[A-Za-z0-9_.]+)")


def _epoch(datestr: str) -> int:
    """YYYY-MM-DD -> unix epoch seconds; 0 if unparseable."""
    try:
        return int(dt.datetime.strptime(str(datestr)[:10], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    except (ValueError, TypeError):
        return 0


def _lane_status(text: str) -> int:
    """Coarse first-pass status code (see schema STATUS ladder). Refinement pending."""
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
    return 1  # active by default


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
        anchor_src = c[4] if len(c) > 4 else ""
        notes = c[-1]
        m_doc = DOCPAT.search(anchor_src) or DOCPAT.search(notes)
        members = MEMBERPAT.findall(notes)
        owner = "member.derald"
        steward = ""
        # "steward member.X" wins for STEWARDKEY; first non-owner member is the fallback
        ms = re.search(r"steward[^\n]{0,20}?(member\.[A-Za-z0-9_.]+)", notes)
        if ms:
            steward = ms.group(1)
        elif members:
            steward = next((m for m in members if m != owner), "")
        proj = PROJPAT.search(c[3] if len(c) > 3 else "") or PROJPAT.search(notes)
        claim = (root / "coordination" / "aif" / f"{lkey}.claim").exists()
        rows.append({
            "LKEY": lkey, "TITLE": title, "OWNERKEY": owner, "STEWARDKEY": steward,
            "PROJECT": proj.group(1) if proj else "project.x64base.runtime",
            "SDLCLANE": "", "STATUS": _lane_status(c[5] if len(c) > 5 else ""),
            "CLAIMED": 1 if claim else 0, "ANCHOR": m_doc.group(1) if m_doc else "",
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
            "HANDLE": r.get("handle_binding", ""), "REPORT": rkey,
        })
        for lane in (r.get("lanes") or []):
            runlane.append({"RUNKEY": rkey, "LANEKEY": lane})
    return runs, runlane


def extract_proofs(root: Path) -> list[dict]:
    d = yaml.safe_load((root / "labtalk/registries/proofs.yaml").read_text(encoding="utf-8", errors="replace"))
    rows = []
    for p in d.get("proofs", []):
        rows.append({
            "PKEY": p.get("id", ""), "LABEL": p.get("label", ""), "STATE": p.get("state", ""),
            "LANEKEY": "", "SOURCE": str(p.get("source", "")),
        })
    return rows


def _write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        wtr = csv.DictWriter(fh, fieldnames=columns)
        wtr.writeheader()
        for row in rows:
            wtr.writerow(row)


def seed(root: Path, out: Path) -> dict:
    lanes = extract_lanes(root)
    runs, runlane = extract_runs(root)
    proofs = extract_proofs(root)
    _write_csv(out / "SYSLANE.csv", lanes,
               ["LKEY", "TITLE", "OWNERKEY", "STEWARDKEY", "PROJECT", "SDLCLANE", "STATUS", "CLAIMED", "ANCHOR"])
    _write_csv(out / "SYSRUN.csv", runs,
               ["RKEY", "MEMBERKEY", "ROLE", "OWNERKEY", "COMMITKEY", "AUTHORKEY", "PLANKEY",
                "PROJECT", "STATUS", "STARTAT", "BRANCH", "HANDLE", "REPORT"])
    _write_csv(out / "SYSRUNLANE.csv", runlane, ["RUNKEY", "LANEKEY"])
    _write_csv(out / "SYSPROOF.csv", proofs, ["PKEY", "LABEL", "STATE", "LANEKEY", "SOURCE"])
    return {"SYSLANE": len(lanes), "SYSRUN": len(runs), "SYSRUNLANE": len(runlane), "SYSPROOF": len(proofs)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Extract tracking registries to schema-aligned CSVs.")
    ap.add_argument("--root", default=str(REPO))
    ap.add_argument("--out", default=str(REPO / "data" / "metadata" / "portal" / "seed"))
    args = ap.parse_args(argv)
    counts = seed(Path(args.root), Path(args.out))
    print("seed_tracking: wrote " + ", ".join(f"{k}={v}" for k, v in counts.items()) + f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
