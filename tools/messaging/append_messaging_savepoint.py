#!/usr/bin/env python3
"""
Messaging savepoint append tool v2.

Backward compatible with the original Messaging savepoint tool, but adds:
  --lane
  --source-reports
  repeated --source-report
  --boundary-summary
  --allowed-candidate-mutations
  --forbidden-active-mutations

This preserves the append-only journal pattern. It does not mutate DBF/CDX/LMDB,
HELP DATA, CMDHELPCHK, source mining, runtime catalogs, or active promotions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def read_existing_index(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_index(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def normalize_reports(source_report: list[str], source_reports: str) -> str:
    parts: list[str] = []
    for s in source_report or []:
        if s:
            parts.append(s)
    if source_reports:
        for s in source_reports.split(";"):
            s = s.strip()
            if s:
                parts.append(s)
    # Preserve order, remove duplicates
    seen = set()
    out = []
    for p in parts:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return ";".join(out)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--savepoint-id", required=True)
    ap.add_argument("--lane", default="MESSAGING")
    ap.add_argument("--status", required=True)
    ap.add_argument("--phase", default="")
    ap.add_argument("--summary", default="")
    ap.add_argument("--next-gate", default="")
    ap.add_argument("--source-report", action="append", default=[])
    ap.add_argument("--source-reports", default="")
    ap.add_argument("--messages", default="")
    ap.add_argument("--text-rows", default="")
    ap.add_argument("--locales", default="")
    ap.add_argument("--validation-issues", default="")
    ap.add_argument("--boundary-summary", default="")
    ap.add_argument("--allowed-candidate-mutations", default="")
    ap.add_argument("--forbidden-active-mutations", default="")
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    args = ap.parse_args()

    if not args.accept_messaging_savepoint:
        raise SystemExit("Refusing to append Messaging savepoint without --accept-messaging-savepoint")

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports_dir = docs / "reports"
    docs.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    journal = docs / "MESSAGING_SAVEPOINT_JOURNAL.md"
    index = reports_dir / "message_savepoint_thread_index_v1.csv"
    latest = reports_dir / "message_savepoint_latest_v1.json"

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    source_reports = normalize_reports(args.source_report, args.source_reports)

    boundary_summary = args.boundary_summary
    if not boundary_summary:
        allowed = args.allowed_candidate_mutations or "none"
        forbidden = args.forbidden_active_mutations or "no active DBF/catalog mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no source-mining mutation; no active catalog promotion"
        boundary_summary = f"allowed candidate mutations: {allowed}; forbidden active/protected mutations: {forbidden}"

    entry_lines = [
        f"## {args.savepoint_id} — {args.status}",
        "",
        f"- Timestamp UTC: {timestamp}",
        f"- Lane: {args.lane}",
        f"- Phase: {args.phase}",
        f"- Messages: {args.messages}",
        f"- Text rows: {args.text_rows}",
        f"- Locales: {args.locales}",
        f"- Validation issues: {args.validation_issues}",
        f"- Summary: {args.summary}",
        f"- Boundary summary: {boundary_summary}",
    ]
    if args.allowed_candidate_mutations:
        entry_lines.append(f"- Allowed candidate mutations: {args.allowed_candidate_mutations}")
    if args.forbidden_active_mutations:
        entry_lines.append(f"- Forbidden active/protected mutations: {args.forbidden_active_mutations}")
    if source_reports:
        entry_lines.append(f"- Source reports: {source_reports}")
    if args.next_gate:
        entry_lines.append(f"- Next gate: {args.next_gate}")
    entry_lines.append("")
    entry = "\n".join(entry_lines)
    entry_hash = sha256_text(entry)

    with journal.open("a", encoding="utf-8", newline="") as f:
        f.write(entry)

    row = {
        "timestamp_utc": timestamp,
        "savepoint_id": args.savepoint_id,
        "lane": args.lane,
        "status": args.status,
        "phase": args.phase,
        "messages": args.messages,
        "text_rows": args.text_rows,
        "locales": args.locales,
        "validation_issues": args.validation_issues,
        "next_gate": args.next_gate,
        "journal_anchor": args.savepoint_id,
        "source_reports": source_reports,
        "boundary_summary": boundary_summary,
        "allowed_candidate_mutations": args.allowed_candidate_mutations,
        "forbidden_active_mutations": args.forbidden_active_mutations,
        "entry_sha256": entry_hash,
    }

    fields = [
        "timestamp_utc", "savepoint_id", "lane", "status", "phase",
        "messages", "text_rows", "locales", "validation_issues", "next_gate",
        "journal_anchor", "source_reports", "boundary_summary",
        "allowed_candidate_mutations", "forbidden_active_mutations", "entry_sha256",
    ]
    existing = read_existing_index(index)
    # Preserve older rows, adding blank values for new columns.
    normalized = []
    for r in existing:
        normalized.append({k: r.get(k, "") for k in fields})
    normalized.append(row)
    write_index(index, normalized, fields)

    latest.write_text(json.dumps(row, indent=2), encoding="utf-8")

    print(f"[{args.savepoint_id}] Messaging savepoint appended.")
    print(f"  journal: {journal}")
    print(f"  index: {index}")
    print(f"  latest: {latest}")
    print(f"  entry_sha256: {entry_hash}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
