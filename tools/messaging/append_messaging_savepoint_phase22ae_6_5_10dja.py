#!/usr/bin/env python3
"""Append MSG-022AE.6.5.10DJA messaging savepoint with duplicate guard."""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Dict

PHASE = "MSG-022AE.6.5.10DJA"
STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10DJA_ACTUAL_RUNTIME_PROOF_COMMAND_STAGING_GREEN_CONCRETE_MANUAL_RUN_SCRIPT_STAGED_SOURCE_HELD"
SUMMARY_REL = "docs/messaging/apply/phase22ae_6_5_10dja_actual_runtime_proof_command_staging_v1/phase22ae_6_5_10dja_summary_v1.json"
NEXT_GATE = "HOLD_OR_RUN_PHASE22AE_6_5_10DJA_ACTUAL_RUNTIME_PROOF_AND_CAPTURE_TRANSCRIPT"


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def phase_present(repo: Path) -> bool:
    paths = [
        repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md",
        repo / "docs/messaging/reports/message_savepoint_thread_index_v1.csv",
        repo / "docs/messaging/reports/message_savepoint_latest_v1.json",
    ]
    return any(PHASE in read_text(p) for p in paths)


def load_summary(repo: Path) -> Dict[str, object]:
    p = repo / SUMMARY_REL
    if not p.exists():
        raise SystemExit(f"10DJA summary not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("status") != STATUS:
        raise SystemExit(f"10DJA summary is not green: {data.get('status')}")
    return data


def update_index(index: Path, entry: Dict[str, str]) -> None:
    index.parent.mkdir(parents=True, exist_ok=True)
    if index.exists() and index.stat().st_size > 0:
        with index.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fields = list(reader.fieldnames or [])
    else:
        rows = []
        fields = []
    preferred = ["phase", "savepoint", "status", "next_gate", "timestamp_utc", "entry_sha256", "summary_path"]
    for f in preferred:
        if f not in fields:
            fields.append(f)
    row = {k: "" for k in fields}
    for k, v in entry.items():
        if k in row:
            row[k] = v
    for alt in ["id", "savepoint_id", "message_savepoint", "phase_id"]:
        if alt in row:
            row[alt] = PHASE
    if "status" in row:
        row["status"] = STATUS
    if "timestamp" in row:
        row["timestamp"] = entry["timestamp_utc"]
    if "created_at_utc" in row:
        row["created_at_utc"] = entry["timestamp_utc"]
    if "sha256" in row:
        row["sha256"] = entry["entry_sha256"]
    rows.append(row)
    with index.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    args = ap.parse_args()
    if not args.accept_messaging_savepoint:
        raise SystemExit("Refusing to append without --accept-messaging-savepoint")
    repo = Path(args.repo_root).resolve()
    if phase_present(repo):
        print(f"[{PHASE}] Messaging savepoint already present; duplicate append skipped.")
        return 0
    summary = load_summary(repo)
    ts = now_utc()
    body = "\n".join([
        f"## {PHASE}",
        "",
        f"- timestamp_utc: {ts}",
        f"- status: {STATUS}",
        f"- summary: {SUMMARY_REL}",
        f"- next_gate: {NEXT_GATE}",
        "- boundary: actual runtime proof commands staged only; runtime not executed by package; source/HELP/CMDHELPCHK/DBF/CDX/LMDB/workspace mutation 0",
        "",
    ])
    entry_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as f:
        f.write(body)
    entry = {
        "phase": PHASE,
        "savepoint": PHASE,
        "status": STATUS,
        "next_gate": NEXT_GATE,
        "timestamp_utc": ts,
        "entry_sha256": entry_sha,
        "summary_path": SUMMARY_REL,
    }
    update_index(repo / "docs/messaging/reports/message_savepoint_thread_index_v1.csv", entry)
    latest = repo / "docs/messaging/reports/message_savepoint_latest_v1.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps({**entry, "summary": summary}, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[{PHASE}] Messaging savepoint appended.")
    print(f"  journal: {journal}")
    print(f"  index: {repo / 'docs/messaging/reports/message_savepoint_thread_index_v1.csv'}")
    print(f"  latest: {latest}")
    print(f"  entry_sha256: {entry_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
