#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_EXPECTED = "LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_PROMOTION_READBACK_GREEN"

def read_first(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def append_csv(path: Path, row: dict[str, str], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        if not exists:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-locale-savepoint", action="store_true")
    args = ap.parse_args()

    if not args.accept_locale_savepoint:
        print("[LOC-023G] Refusing without --accept-locale-savepoint")
        return 2

    repo = Path(args.repo_root).resolve()
    summary_path = repo / "docs/locale/reports/locale_phase23g_status_summary_v1.csv"
    row = read_first(summary_path)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[LOC-023G] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}")
        return 2

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    savepoint_id = "LOC-023G"
    savepoint = {
        "timestamp_utc": now,
        "savepoint_id": savepoint_id,
        "lane": "LOCALE",
        "status": status,
        "phase": "Phase 23G active shared locale spine promotion/readback",
        "validation_issues": row.get("VALIDATION_ISSUES", ""),
        "active_system_locales_dbf_present": row.get("ACTIVE_SYSTEM_LOCALES_DBF_PRESENT", ""),
        "active_system_locale_fallback_dbf_present": row.get("ACTIVE_SYSTEM_LOCALE_FALLBACK_DBF_PRESENT", ""),
        "active_lmdb_env_dirs": row.get("ACTIVE_LMDB_ENV_DIRS", ""),
        "active_lmdb_mdb_files": row.get("ACTIVE_LMDB_MDB_FILES", ""),
        "active_lmdb_data_mdb_files": row.get("ACTIVE_LMDB_DATA_MDB_FILES", ""),
        "active_promotion_executed": row.get("ACTIVE_PROMOTION_EXECUTED", ""),
        "next_gate": row.get("NEXT_GATE", ""),
        "journal_anchor": savepoint_id,
        "source_reports": "docs/locale/reports/locale_phase23g_promotion_status_summary_v1.csv;docs/locale/reports/locale_phase23g_status_summary_v1.csv;docs/locale/reports/locale_phase23g_active_promotion_inventory_v1.csv;docs/locale/reports/locale_phase23g_gate_check_v1.csv;docs/locale/reports/locale_phase23g_readback_boundary_ledger_v1.csv;docs/locale/runlog/LOC-023G_ACTIVE_LOCALE_SPINE_READBACK_PROOF.md",
        "boundary_summary": "active shared locale spine promoted to neutral active locale roots; no source/HELP/CMDHELPCHK/manualgen/Data Dictionary/SelfDoc mutation; no Messaging runtime integration change",
    }
    digest_basis = json.dumps(savepoint, sort_keys=True, ensure_ascii=False)
    savepoint["entry_sha256"] = sha256_text(digest_basis)

    journal = repo / "docs/locale/LOCALE_SAVEPOINT_JOURNAL.md"
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8", newline="\n") as f:
        f.write(f"\n## {savepoint_id} — {now}\n\n")
        f.write(f"Status: `{status}`\n\n")
        f.write("Phase: Phase 23G active shared locale spine promotion/readback\n\n")
        f.write("Boundary: active locale spine only; no source/HELP/CMDHELPCHK/manualgen/Data Dictionary/SelfDoc mutation.\n\n")
        f.write(f"Entry SHA256: `{savepoint['entry_sha256']}`\n")

    latest = repo / "docs/locale/reports/locale_savepoint_latest_v1.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(savepoint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    index = repo / "docs/locale/reports/locale_savepoint_thread_index_v1.csv"
    append_csv(index, {
        "timestamp_utc": now,
        "savepoint_id": savepoint_id,
        "lane": "LOCALE",
        "status": status,
    }, ["timestamp_utc", "savepoint_id", "lane", "status"])

    print("[LOC-023G] Locale savepoint appended.")
    print(f"  journal: {journal}")
    print(f"  index: {index}")
    print(f"  latest: {latest}")
    print(f"  entry_sha256: {savepoint['entry_sha256']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
