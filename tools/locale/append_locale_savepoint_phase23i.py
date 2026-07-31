#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_EXPECTED = "LOCALE_PHASE23I_MESSAGING_LOCALE_SPINE_SOURCE_INTEGRATION_PROBE_GREEN_SOURCE_HELD"

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
        print("[LOC-023I] Refusing without --accept-locale-savepoint")
        return 2

    repo = Path(args.repo_root).resolve()
    summary_path = repo / "docs/locale/reports/locale_phase23i_status_summary_v1.csv"
    row = read_first(summary_path)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[LOC-023I] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}")
        return 2

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    savepoint_id = "LOC-023I"
    savepoint = {
        "timestamp_utc": now,
        "savepoint_id": savepoint_id,
        "lane": "LOCALE",
        "status": status,
        "phase": "Phase 23I Messaging locale spine source integration probe",
        "validation_issues": row.get("VALIDATION_ISSUES", ""),
        "source_mutation_authorized": row.get("SOURCE_MUTATION_AUTHORIZED", ""),
        "runtime_behavior_change_authorized": row.get("RUNTIME_BEHAVIOR_CHANGE_AUTHORIZED", ""),
        "active_locale_spine_present": row.get("ACTIVE_LOCALE_SPINE_PRESENT", ""),
        "source_scan_rows": row.get("SOURCE_SCAN_ROWS", ""),
        "source_evidence_rows": row.get("SOURCE_EVIDENCE_ROWS", ""),
        "integration_seam_rows": row.get("INTEGRATION_SEAM_ROWS", ""),
        "api_contract_rows": row.get("API_CONTRACT_ROWS", ""),
        "next_gate": row.get("NEXT_GATE", ""),
        "journal_anchor": savepoint_id,
        "source_reports": "docs/locale/LOCALE_PHASE23I_MESSAGING_LOCALE_SPINE_SOURCE_INTEGRATION_PROBE.md;docs/locale/reports/locale_phase23i_status_summary_v1.csv;docs/locale/reports/locale_phase23i_source_scan_v1.csv;docs/locale/reports/locale_phase23i_source_evidence_v1.csv;docs/locale/reports/locale_phase23i_integration_seams_v1.csv;docs/locale/reports/locale_phase23i_runtime_api_contract_v1.csv;docs/locale/reports/locale_phase23i_boundary_ledger_v1.csv",
        "boundary_summary": "report-only Messaging source integration probe; no source mutation; no runtime behavior change; no active DBF/CDX/LMDB mutation; no HELP/CMDHELPCHK/manualgen/Data Dictionary/SelfDoc mutation",
    }
    digest_basis = json.dumps(savepoint, sort_keys=True, ensure_ascii=False)
    savepoint["entry_sha256"] = sha256_text(digest_basis)

    journal = repo / "docs/locale/LOCALE_SAVEPOINT_JOURNAL.md"
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8", newline="\n") as f:
        f.write(f"\n## {savepoint_id} — {now}\n\n")
        f.write(f"Status: `{status}`\n\n")
        f.write("Phase: Phase 23I Messaging locale spine source integration probe\n\n")
        f.write("Boundary: report-only probe; no source/runtime/protected mutation.\n\n")
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

    print("[LOC-023I] Locale savepoint appended.")
    print(f"  journal: {journal}")
    print(f"  index: {index}")
    print(f"  latest: {latest}")
    print(f"  entry_sha256: {savepoint['entry_sha256']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
