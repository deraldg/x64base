#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SAVEPOINT_ID = "LOC-023P-MSGMGR-SCHEMA-STATUS"
STATUS_EXPECTED = "LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS_BUILD_SMOKE_GREEN"

def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def read_first(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}

def append_csv(path: Path, row: dict[str, str], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        if not exists:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-locale-savepoint", action="store_true")
    ap.add_argument("--allow-duplicate-correction", action="store_true")
    args = ap.parse_args()

    if not args.accept_locale_savepoint:
        print(f"[{SAVEPOINT_ID}] Refusing without --accept-locale-savepoint")
        return 2

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs/locale/reports"
    summary = read_first(reports / "locale_phase23p_msgmgr_schema_status_validation_summary_v1.csv")
    status = summary.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[{SAVEPOINT_ID}] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}")
        return 2

    index = reports / "locale_savepoint_thread_index_v1.csv"
    existing = [r for r in read_csv(index) if r.get("savepoint_id") == SAVEPOINT_ID]
    same_status = [r for r in existing if r.get("status") == status]
    other_status = [r for r in existing if r.get("status") != status]

    if same_status and not args.allow_duplicate_correction:
        print(f"[{SAVEPOINT_ID}] ALREADY_SAVEPOINTED")
        print(f"  existing rows: {len(existing)}")
        print(f"  same-status rows: {len(same_status)}")
        print("  no journal append performed")
        return 0

    if other_status and not args.allow_duplicate_correction:
        print(f"[{SAVEPOINT_ID}] Refusing: savepoint id exists with different status.")
        return 2

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    savepoint = {
        "timestamp_utc": now,
        "savepoint_id": SAVEPOINT_ID,
        "lane": "LOCALE",
        "status": status,
        "phase": "Phase 23P MSGMGR schema status reporting",
        "validation_issues": summary.get("VALIDATION_ISSUES", ""),
        "build_proof": summary.get("BUILD_PROOF", ""),
        "msgmgr_status_proof": summary.get("MSGMGR_STATUS_PROOF", ""),
        "schema_root_proof": summary.get("SCHEMA_ROOT_PROOF", ""),
        "locale_schema_path_proof": summary.get("LOCALE_SCHEMA_PATH_PROOF", ""),
        "messaging_schema_held_proof": summary.get("MESSAGING_SCHEMA_HELD_PROOF", ""),
        "next_gate": summary.get("NEXT_GATE", ""),
        "journal_anchor": SAVEPOINT_ID,
        "source_reports": "docs/locale/LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS.md;docs/locale/reports/locale_phase23p_msgmgr_schema_status_apply_summary_v1.csv;docs/locale/reports/locale_phase23p_msgmgr_schema_status_validation_summary_v1.csv;docs/locale/reports/locale_phase23p_msgmgr_schema_status_mutation_inventory_v1.csv;docs/locale/reports/locale_phase23p_msgmgr_schema_status_boundary_ledger_v1.csv;docs/locale/reports/locale_phase23p_msgmgr_schema_status_validation_boundary_v1.csv;docs/locale/runlog/LOC-023P_MSGMGR_SCHEMA_STATUS_BUILD_AND_SMOKE_PROOF.md",
        "boundary_summary": "MSGMGR STATUS reports schema root and active locale schema path; Messaging schema held; no active schema/DBF/CDX/LMDB/HELP/CMDHELPCHK/manualgen/Data Dictionary/SelfDoc mutation",
    }
    savepoint["entry_sha256"] = sha256_text(json.dumps(savepoint, sort_keys=True, ensure_ascii=False))

    journal = repo / "docs/locale/LOCALE_SAVEPOINT_JOURNAL.md"
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8", newline="\n") as f:
        f.write(f"\n## {SAVEPOINT_ID} — {now}\n\n")
        f.write(f"Status: `{status}`\n\n")
        f.write("Phase: Phase 23P MSGMGR schema status reporting\n\n")
        f.write("Boundary: status reporting only; no active schema/catalog/protected mutation.\n\n")
        f.write(f"Entry SHA256: `{savepoint['entry_sha256']}`\n")

    latest = reports / "locale_savepoint_latest_v1.json"
    latest.write_text(json.dumps(savepoint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    append_csv(index, {
        "timestamp_utc": now,
        "savepoint_id": SAVEPOINT_ID,
        "lane": "LOCALE",
        "status": status,
    }, ["timestamp_utc", "savepoint_id", "lane", "status"])

    print(f"[{SAVEPOINT_ID}] Locale savepoint appended.")
    print(f"  journal: {journal}")
    print(f"  index: {index}")
    print(f"  latest: {latest}")
    print(f"  entry_sha256: {savepoint['entry_sha256']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
